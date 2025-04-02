"""
Strategy Manager module for Crypto Trading Bot
Implements various trading strategies for different market regimes
"""
import uuid
import time
import json
import logging
import numpy as np
from typing import Dict, List, Optional, Any, Union, Tuple, Type
from datetime import datetime, timedelta
from abc import ABC, abstractmethod

class Strategy(ABC):
    """Abstract base class for all trading strategies"""
    
    def __init__(self, name: str, parameters: Dict[str, Any]):
        """
        Initialize the strategy
        
        Args:
            name: Strategy name
            parameters: Strategy parameters
        """
        self.name = name
        self.parameters = parameters
        self.risk_settings = {
            "max_position_size": 10,  # % of portfolio
            "stop_loss": 5,           # % from entry
            "take_profit": 10,        # % from entry
            "max_concurrent_trades": 5,
            "emergency_stop_threshold": 15  # % portfolio drawdown
        }
    
    def set_risk_management(self, settings: Dict[str, Any]):
        """
        Set risk management settings
        
        Args:
            settings: Risk management settings
        """
        self.risk_settings.update(settings)
    
    @abstractmethod
    def get_signal(self, price: float, technicals: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Get trading signal
        
        Args:
            price: Current price
            technicals: Technical indicators
            
        Returns:
            Trading signal or None if no signal
        """
        pass
    
    def calculate_position_size(self, price: float, capital: float) -> float:
        """
        Calculate position size based on risk settings
        
        Args:
            price: Current price
            capital: Available capital
            
        Returns:
            Position size (quantity)
        """
        position_value = capital * (self.risk_settings["max_position_size"] / 100)
        return position_value / price


class TrendFollowingStrategy(Strategy):
    """
    Trend Following Strategy
    Uses EMA crossovers to identify and follow trends
    """
    
    def __init__(self, name: str, parameters: Dict[str, Any]):
        """Initialize with default parameters if not provided"""
        default_params = {
            "short_ema": 9,
            "long_ema": 21
        }
        # Update defaults with provided parameters
        default_params.update(parameters)
        super().__init__(name, default_params)
    
    def get_signal(self, price: float, technicals: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Get trading signal based on trend following strategy
        
        Args:
            price: Current price
            technicals: Technical indicators
            
        Returns:
            Trading signal or None if no signal
        """
        # Check if we have the necessary data
        if not technicals or "ema" not in technicals:
            return None
        
        # Get EMA values
        short_ema = technicals["ema"]["short"]
        long_ema = technicals["ema"]["medium"]
        
        # Check for buy signal: short EMA crosses above long EMA
        if short_ema > long_ema and price > short_ema:
            # Buy signal
            return {
                "action": "buy",
                "symbol": technicals["symbol"],
                "price": price,
                "quantity": 1,  # This would be calculated based on risk management
                "reason": "EMA crossover (bullish)",
                "timestamp": datetime.now().isoformat()
            }
        
        # Check for sell signal: short EMA crosses below long EMA
        if short_ema < long_ema and price < short_ema:
            # Sell signal
            return {
                "action": "sell",
                "symbol": technicals["symbol"],
                "price": price,
                "quantity": 1,  # This would be based on current position
                "reason": "EMA crossover (bearish)",
                "timestamp": datetime.now().isoformat()
            }
        
        # No signal
        return None


class MeanReversionStrategy(Strategy):
    """
    Mean Reversion Strategy
    Uses grid trading to buy low and sell high in sideways markets
    """
    
    def __init__(self, name: str, parameters: Dict[str, Any]):
        """Initialize with default parameters if not provided"""
        default_params = {
            "width": 2.0,  # Grid width in percentage
            "levels": 10   # Number of grid levels
        }
        # Update defaults with provided parameters
        default_params.update(parameters)
        super().__init__(name, default_params)
        
        self.grid_levels = {}  # To track grid levels for different symbols
    
    def get_signal(self, price: float, technicals: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Get trading signal based on mean reversion strategy
        
        Args:
            price: Current price
            technicals: Technical indicators
            
        Returns:
            Trading signal or None if no signal
        """
        # Check if we have the necessary data
        if not technicals or "bollinger" not in technicals:
            return None
        
        symbol = technicals["symbol"]
        bollinger = technicals["bollinger"]
        
        # Calculate grid levels if not already set
        if symbol not in self.grid_levels:
            self.calculate_grid_levels(symbol, bollinger["middle"], bollinger["upper"], bollinger["lower"])
        
        # Get grid levels for this symbol
        grid_levels = self.grid_levels.get(symbol, [])
        
        if not grid_levels:
            return None
        
        # Check if price crosses a grid level
        for level in grid_levels:
            if abs(price - level["price"]) / level["price"] < 0.001:  # Within 0.1% of the level
                return {
                    "action": level["action"],
                    "symbol": technicals["symbol"],
                    "price": price,
                    "quantity": 1,  # This would be calculated based on risk management
                    "reason": f"Grid level {level['level']} ({level['action']})",
                    "timestamp": datetime.now().isoformat()
                }
        
        # Check for oversold/overbought conditions for additional signals
        if technicals.get("rsi", 50) < 30 and price < bollinger["lower"]:
            # Oversold condition, buy signal
            return {
                "action": "buy",
                "symbol": technicals["symbol"],
                "price": price,
                "quantity": 1,  # This would be calculated based on risk management
                "reason": "Oversold condition (RSI + Bollinger)",
                "timestamp": datetime.now().isoformat()
            }
        
        if technicals.get("rsi", 50) > 70 and price > bollinger["upper"]:
            # Overbought condition, sell signal
            return {
                "action": "sell",
                "symbol": technicals["symbol"],
                "price": price,
                "quantity": 1,  # This would be based on current position
                "reason": "Overbought condition (RSI + Bollinger)",
                "timestamp": datetime.now().isoformat()
            }
        
        # No signal
        return None
    
    def calculate_grid_levels(self, symbol: str, middle: float, upper: float, lower: float):
        """
        Calculate grid levels
        
        Args:
            symbol: Cryptocurrency symbol
            middle: Middle Bollinger Band (SMA)
            upper: Upper Bollinger Band
            lower: Lower Bollinger Band
        """
        levels = []
        
        # Calculate grid width based on Bollinger Bands and parameter
        price_range = upper - lower
        grid_width = price_range / self.parameters["levels"]
        
        # Create buy levels below middle
        for i in range(1, int(self.parameters["levels"] / 2) + 1):
            price = middle - (i * grid_width)
            levels.append({
                "level": -i,
                "price": price,
                "action": "buy"
            })
        
        # Create sell levels above middle
        for i in range(1, int(self.parameters["levels"] / 2) + 1):
            price = middle + (i * grid_width)
            levels.append({
                "level": i,
                "price": price,
                "action": "sell"
            })
        
        # Store grid levels
        self.grid_levels[symbol] = levels


class MarketMakingStrategy(Strategy):
    """
    Market Making Strategy
    Places limit orders on both sides of the market to capture the spread
    """
    
    def __init__(self, name: str, parameters: Dict[str, Any]):
        """Initialize with default parameters if not provided"""
        default_params = {
            "spread": 0.5,    # Spread in percentage
            "order_size": 5   # Order size in percentage of capital
        }
        # Update defaults with provided parameters
        default_params.update(parameters)
        super().__init__(name, default_params)
    
    def get_signal(self, price: float, technicals: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Get trading signal based on market making strategy
        
        Args:
            price: Current price
            technicals: Technical indicators
            
        Returns:
            Trading signal or None if no signal
        """
        # Market making strategy would typically place limit orders on both sides
        # For simplicity, we'll simulate this with market orders based on price movements
        
        # Check if we have the necessary data
        if not technicals:
            return None
        
        # Calculate bid and ask prices
        spread_amount = price * (self.parameters["spread"] / 100)
        bid_price = price - spread_amount
        ask_price = price + spread_amount
        
        # In a real market making strategy, we would place limit orders at these prices
        # For this simulation, we'll generate signals when price approaches these levels
        
        # Check if price is near our bid price
        if abs(price - bid_price) / price < 0.001:
            # Buy signal
            return {
                "action": "buy",
                "symbol": technicals["symbol"],
                "price": price,
                "quantity": 1,  # This would be calculated based on risk management
                "reason": "Market making bid",
                "timestamp": datetime.now().isoformat()
            }
        
        # Check if price is near our ask price
        if abs(price - ask_price) / price < 0.001:
            # Sell signal
            return {
                "action": "sell",
                "symbol": technicals["symbol"],
                "price": price,
                "quantity": 1,  # This would be based on current position
                "reason": "Market making ask",
                "timestamp": datetime.now().isoformat()
            }
        
        # No signal
        return None


class ArbitrageStrategy(Strategy):
    """
    Arbitrage Strategy
    Exploits price differences between different exchanges
    """
    
    def __init__(self, name: str, parameters: Dict[str, Any]):
        """Initialize with default parameters if not provided"""
        default_params = {
            "min_spread": 0.5  # Minimum spread to consider arbitrage (percentage)
        }
        # Update defaults with provided parameters
        default_params.update(parameters)
        super().__init__(name, default_params)
    
    def get_signal(self, price: float, technicals: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Get trading signal based on arbitrage strategy
        
        Args:
            price: Current price
            technicals: Technical indicators
            
        Returns:
            Trading signal or None if no signal
        """
        # Arbitrage strategy requires prices from multiple exchanges
        # For simplicity, we'll simulate this with a random price difference
        
        # Check if we have the necessary data
        if not technicals:
            return None
        
        # Simulate price from another exchange
        import random
        other_exchange_price = price * (1 + (random.random() * 0.02 - 0.01))  # ±1% difference
        
        # Calculate percentage difference
        spread_percentage = abs(other_exchange_price - price) / price * 100
        
        # Check if spread is large enough for arbitrage
        if spread_percentage >= self.parameters["min_spread"]:
            if other_exchange_price > price:
                # Buy on this exchange, sell on the other
                return {
                    "action": "buy",
                    "symbol": technicals["symbol"],
                    "price": price,
                    "quantity": 1,  # This would be calculated based on risk management
                    "reason": f"Arbitrage opportunity ({spread_percentage:.2f}% spread)",
                    "timestamp": datetime.now().isoformat()
                }
            else:
                # Sell on this exchange, buy on the other
                return {
                    "action": "sell",
                    "symbol": technicals["symbol"],
                    "price": price,
                    "quantity": 1,  # This would be based on current position
                    "reason": f"Arbitrage opportunity ({spread_percentage:.2f}% spread)",
                    "timestamp": datetime.now().isoformat()
                }
        
        # No signal
        return None


class StrategyManager:
    """Manager for trading strategies and signal generation"""
    
    def __init__(self, api_service, market_analyzer):
        """
        Initialize the strategy manager
        
        Args:
            api_service: API service instance
            market_analyzer: Market analyzer instance
        """
        # Available strategies
        self.strategies = {
            "trend": TrendFollowingStrategy,
            "mean_reversion": MeanReversionStrategy,
            "market_making": MarketMakingStrategy,
            "arbitrage": ArbitrageStrategy
        }
        
        # API service and market analyzer
        self.api_service = api_service
        self.market_analyzer = market_analyzer
        
        # Active strategies for different symbols
        self.active_strategies = {}
        
        # Strategy performance metrics
        self.performance = {}
        
        # Risk management settings
        self.risk_settings = {
            "max_position_size": 10,  # % of portfolio
            "stop_loss": 5,           # % from entry
            "take_profit": 10,        # % from entry
            "max_concurrent_trades": 5,
            "emergency_stop_threshold": 15  # % portfolio drawdown
        }
        
        # Trade history
        self.trades = []
        
        self.logger = logging.getLogger(__name__)
    
    def activate_strategy(self, name: str, type_str: str, parameters: Dict[str, Any], symbols: List[str]) -> bool:
        """
        Create and activate a strategy
        
        Args:
            name: Strategy name
            type_str: Strategy type (trend, mean_reversion, market_making, arbitrage)
            parameters: Strategy parameters
            symbols: Trading pairs for the strategy
            
        Returns:
            Success status
        """
        if type_str not in self.strategies:
            self.logger.error(f"Strategy type {type_str} not found")
            return False
        
        try:
            # Create strategy instance
            strategy = self.strategies[type_str](name, parameters)
            
            # Apply risk management
            strategy.set_risk_management(self.risk_settings)
            
            # Activate for each symbol
            for symbol in symbols:
                key = f"{type_str}_{symbol}"
                self.active_strategies[key] = strategy
                
                # Initialize performance tracking
                self.performance[key] = {
                    "trades": 0,
                    "wins": 0,
                    "losses": 0,
                    "profit_loss": 0,
                    "return": 0
                }
            
            self.logger.info(f"Strategy {name} activated for {', '.join(symbols)}")
            return True
        
        except Exception as e:
            self.logger.error(f"Failed to activate strategy {name}: {str(e)}")
            return False
    
    def deactivate_strategy(self, type_str: str, symbols: List[str]) -> bool:
        """
        Deactivate a strategy for specific symbols
        
        Args:
            type_str: Strategy type
            symbols: Trading pairs to deactivate
            
        Returns:
            Success status
        """
        try:
            for symbol in symbols:
                key = f"{type_str}_{symbol}"
                if key in self.active_strategies:
                    del self.active_strategies[key]
            
            return True
        
        except Exception as e:
            self.logger.error(f"Failed to deactivate strategy for {', '.join(symbols)}: {str(e)}")
            return False
    
    async def get_optimal_strategy(self, symbol: str) -> Dict[str, Any]:
        """
        Get optimal strategy based on market regime
        
        Args:
            symbol: Cryptocurrency symbol
            
        Returns:
            Recommended strategy info
        """
        try:
            # Get market regime analysis
            market_analysis = self.market_analyzer.analyze_market(symbol)
            
            # Get recommended strategy
            recommended_strategy = self.market_analyzer.get_recommended_strategy(market_analysis["regime"])
            
            # Optimize parameters for current market conditions
            optimized_params = self.optimize_parameters(
                recommended_strategy["type"],
                recommended_strategy["parameters"],
                symbol,
                market_analysis
            )
            
            return {
                "name": recommended_strategy["name"],
                "type": recommended_strategy["type"],
                "parameters": optimized_params,
                "confidence": market_analysis["confidence"]
            }
        
        except Exception as e:
            self.logger.error(f"Failed to get optimal strategy for {symbol}: {str(e)}")
            
            # Return default strategy
            return {
                "name": "Conservative Trend Following",
                "type": "trend",
                "parameters": {
                    "short_ema": 9,
                    "long_ema": 21
                },
                "confidence": 50
            }
    
    def optimize_parameters(self, type_str: str, base_params: Dict[str, Any], symbol: str, market_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Optimize strategy parameters for current market conditions
        
        Args:
            type_str: Strategy type
            base_params: Base parameters
            symbol: Cryptocurrency symbol
            market_analysis: Market analysis results
            
        Returns:
            Optimized parameters
        """
        volatility = market_analysis["volatility"]
        trend_strength = market_analysis["trend_strength"]
        regime = market_analysis["regime"]
        
        if type_str == "trend":
            # Adjust EMA periods based on volatility and trend strength
            if volatility > 0.03:
                # Higher volatility = shorter periods to react faster
                return {
                    "short_ema": max(5, base_params["short_ema"] - 2),
                    "long_ema": max(15, base_params["long_ema"] - 5)
                }
            elif trend_strength > 70:
                # Strong trend = longer periods to avoid noise
                return {
                    "short_ema": base_params["short_ema"] + 1,
                    "long_ema": base_params["long_ema"] + 2
                }
            else:
                return base_params
        
        elif type_str == "mean_reversion":
            # Adjust grid width and levels based on volatility
            width = 1.5
            if volatility > 0.03:
                width = 3.0
            elif volatility > 0.01:
                width = 2.0
            
            levels = 12
            if volatility > 0.03:
                levels = 6
            elif volatility > 0.01:
                levels = 10
            
            return {
                "width": width,
                "levels": levels
            }
        
        elif type_str == "market_making":
            # Adjust spread based on volatility
            spread = 0.3
            if volatility > 0.03:
                spread = 0.8
            elif volatility > 0.01:
                spread = 0.5
            
            return {
                "spread": spread,
                "order_size": base_params.get("order_size", 5)
            }
        
        else:
            return base_params
    
    async def get_signal(self, symbol: str, price: float) -> Optional[Dict[str, Any]]:
        """
        Get trading signal for a symbol using active strategy
        
        Args:
            symbol: Cryptocurrency symbol
            price: Current price
            
        Returns:
            Trading signal or None if no signal
        """
        try:
            # Check if we have an active strategy for this symbol
            active_strategy = None
            strategy_type = None
            
            for key, strategy in self.active_strategies.items():
                type_str, sym = key.split('_')
                if sym == symbol:
                    active_strategy = strategy
                    strategy_type = type_str
                    break
            
            # If no active strategy, get optimal strategy
            if not active_strategy:
                optimal = await self.get_optimal_strategy(symbol)
                
                # Activate the optimal strategy
                self.activate_strategy(
                    optimal["name"],
                    optimal["type"],
                    optimal["parameters"],
                    [symbol]
                )
                
                # Get the newly activated strategy
                key = f"{optimal['type']}_{symbol}"
                active_strategy = self.active_strategies.get(key)
                strategy_type = optimal["type"]
            
            # Get technical analysis
            technicals = self.market_analyzer.analyze_technicals(symbol)
            
            # Get trading signal from strategy
            return active_strategy.get_signal(price, technicals) if active_strategy else None
        
        except Exception as e:
            self.logger.error(f"Failed to get signal for {symbol}: {str(e)}")
            return None
    
    async def execute_signal(self, signal: Dict[str, Any], simulation: bool = True) -> Dict[str, Any]:
        """
        Execute a trading signal
        
        Args:
            signal: Trading signal
            simulation: Whether to simulate the trade
            
        Returns:
            Trade execution result
        """
        try:
            result = {
                "success": True,
                "simulation": simulation,
                "trade_id": self.generate_trade_id(),
                "symbol": signal["symbol"],
                "action": signal["action"],
                "price": signal["price"],
                "quantity": signal["quantity"],
                "timestamp": datetime.now().isoformat()
            }
            
            if simulation:
                # In simulation mode, just log the trade
                self.logger.info(f"SIMULATION: {signal['action']} {signal['symbol']} @ {signal['price']}")
                
                # Update performance metrics
                self.update_performance(signal["symbol"], signal["action"], signal)
                
                return result
            else:
                # In live mode, execute the trade on the exchange
                trade_result = self.api_service.execute_trade(
                    signal["symbol"],
                    signal["action"],
                    signal["quantity"],
                    simulation=False
                )
                
                # Update performance metrics
                self.update_performance(signal["symbol"], signal["action"], signal)
                
                return {**result, **trade_result}
        
        except Exception as e:
            self.logger.error(f"Failed to execute signal: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def update_performance(self, symbol: str, action: str, signal: Dict[str, Any]):
        """
        Update strategy performance metrics
        
        Args:
            symbol: Cryptocurrency symbol
            action: Trade action (buy, sell)
            signal: Trading signal
        """
        # Find the strategy for this symbol
        strategy_type = None
        
        for key in self.active_strategies:
            type_str, sym = key.split('_')
            if sym == symbol:
                strategy_type = type_str
                break
        
        if not strategy_type:
            return
        
        key = f"{strategy_type}_{symbol}"
        
        # Update performance metrics
        metrics = self.performance.get(key, {
            "trades": 0,
            "wins": 0,
            "losses": 0,
            "profit_loss": 0,
            "return": 0
        })
        
        metrics["trades"] += 1
        
        # For simplicity, we'll assume each sell action completes a trade cycle
        if action == "sell" and "profit_loss" in signal:
            if signal["profit_loss"] > 0:
                metrics["wins"] += 1
            else:
                metrics["losses"] += 1
            
            metrics["profit_loss"] += signal["profit_loss"]
            
            if "total_investment" in signal and signal["total_investment"] > 0:
                metrics["return"] = (metrics["profit_loss"] / signal["total_investment"]) * 100
        
        self.performance[key] = metrics
        
        # Add to trade history
        self.trades.append({
            "id": self.generate_trade_id(),
            "symbol": symbol,
            "action": action,
            "price": signal["price"],
            "quantity": signal["quantity"],
            "timestamp": datetime.now().isoformat(),
            "strategy": strategy_type
        })
    
    def get_performance(self, type_str: str, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get strategy performance metrics
        
        Args:
            type_str: Strategy type
            symbol: Cryptocurrency symbol
            
        Returns:
            Performance metrics or None if not found
        """
        key = f"{type_str}_{symbol}"
        return self.performance.get(key)
    
    def update_risk_settings(self, settings: Dict[str, Any]):
        """
        Update risk management settings
        
        Args:
            settings: Risk management settings
        """
        self.risk_settings.update(settings)
        
        # Update settings for all active strategies
        for strategy in self.active_strategies.values():
            strategy.set_risk_management(self.risk_settings)
    
    def generate_trade_id(self) -> str:
        """
        Generate a unique trade ID
        
        Returns:
            Unique trade ID
        """
        return f"trade_{uuid.uuid4().hex}"
    
    async def backtest(self, type_str: str, parameters: Dict[str, Any], symbol: str, 
                    start_date: str, end_date: str, initial_capital: float) -> Dict[str, Any]:
        """
        Backtest a strategy on historical data
        
        Args:
            type_str: Strategy type
            parameters: Strategy parameters
            symbol: Cryptocurrency symbol
            start_date: Start date (ISO format)
            end_date: End date (ISO format)
            initial_capital: Initial capital
            
        Returns:
            Backtest results
        """
        try:
            if type_str not in self.strategies:
                raise ValueError(f"Strategy type {type_str} not found")
            
            # Create strategy instance
            strategy = self.strategies[type_str](f"Backtest {type_str}", parameters)
            
            # Apply risk management
            strategy.set_risk_management(self.risk_settings)
            
            # Get historical data
            # For simplicity, we'll use the CoinGecko API with a days parameter
            # In a real system, you'd use a proper date range
            start_timestamp = datetime.fromisoformat(start_date).timestamp()
            end_timestamp = datetime.fromisoformat(end_date).timestamp()
            days = int((end_timestamp - start_timestamp) / (24 * 60 * 60)) + 1
            
            historical_data = self.api_service.get_historical_data(symbol, str(days))
            
            if not historical_data or not historical_data.get("prices") or len(historical_data["prices"]) == 0:
                raise ValueError("No historical data available")
            
            # Filter data by date range
            start_datetime = datetime.fromisoformat(start_date)
            end_datetime = datetime.fromisoformat(end_date)
            
            filtered_prices = [
                item for item in historical_data["prices"]
                if start_datetime <= datetime.fromisoformat(item["time"]) <= end_datetime
            ]
            
            # Run backtest
            capital = initial_capital
            in_position = False
            entry_price = 0
            entry_quantity = 0
            trades = []
            
            # Simulate trading
            for i in range(50, len(filtered_prices)):  # Start at 50 to have enough data for indicators
                current_price = filtered_prices[i]["value"]
                current_time = filtered_prices[i]["time"]
                
                # Create a window of prices for technical analysis
                price_window = [item["value"] for item in filtered_prices[i-50:i+1]]
                
                # Generate synthetic technical data
                technicals = self.generate_technicals(price_window, current_price, symbol)
                
                # Get signal
                signal = strategy.get_signal(current_price, technicals)
                
                if signal:
                    if signal["action"] == "buy" and not in_position:
                        # Calculate quantity based on position size
                        position_size = capital * (self.risk_settings["max_position_size"] / 100)
                        entry_quantity = position_size / current_price
                        entry_price = current_price
                        
                        # Record trade
                        trade_id = self.generate_trade_id()
                        trades.append({
                            "id": trade_id,
                            "time": current_time,
                            "action": "buy",
                            "price": current_price,
                            "quantity": entry_quantity,
                            "value": position_size
                        })
                        
                        # Update capital
                        capital -= position_size
                        in_position = True
                    
                    elif signal["action"] == "sell" and in_position:
                        # Calculate exit value
                        exit_value = entry_quantity * current_price
                        profit_loss = exit_value - (entry_quantity * entry_price)
                        
                        # Record trade
                        trade_id = self.generate_trade_id()
                        trades.append({
                            "id": trade_id,
                            "time": current_time,
                            "action": "sell",
                            "price": current_price,
                            "quantity": entry_quantity,
                            "value": exit_value,
                            "profit_loss": profit_loss
                        })
                        
                        # Update capital
                        capital += exit_value
                        in_position = False
                
                # Apply stop loss if in position
                if in_position and current_price <= entry_price * (1 - self.risk_settings["stop_loss"] / 100):
                    # Stop loss triggered
                    exit_value = entry_quantity * current_price
                    profit_loss = exit_value - (entry_quantity * entry_price)
                    
                    # Record trade
                    trade_id = self.generate_trade_id()
                    trades.append({
                        "id": trade_id,
                        "time": current_time,
                        "action": "sell",
                        "price": current_price,
                        "quantity": entry_quantity,
                        "value": exit_value,
                        "profit_loss": profit_loss,
                        "stop_loss": True
                    })
                    
                    # Update capital
                    capital += exit_value
                    in_position = False
                
                # Apply take profit if in position
                if in_position and current_price >= entry_price * (1 + self.risk_settings["take_profit"] / 100):
                    # Take profit triggered
                    exit_value = entry_quantity * current_price
                    profit_loss = exit_value - (entry_quantity * entry_price)
                    
                    # Record trade
                    trade_id = self.generate_trade_id()
                    trades.append({
                        "id": trade_id,
                        "time": current_time,
                        "action": "sell",
                        "price": current_price,
                        "quantity": entry_quantity,
                        "value": exit_value,
                        "profit_loss": profit_loss,
                        "take_profit": True
                    })
                    
                    # Update capital
                    capital += exit_value
                    in_position = False
            
            # Close any open position at the end
            if in_position:
                last_price = filtered_prices[-1]["value"]
                exit_value = entry_quantity * last_price
                profit_loss = exit_value - (entry_quantity * entry_price)
                
                # Record trade
                trade_id = self.generate_trade_id()
                trades.append({
                    "id": trade_id,
                    "time": filtered_prices[-1]["time"],
                    "action": "sell",
                    "price": last_price,
                    "quantity": entry_quantity,
                    "value": exit_value,
                    "profit_loss": profit_loss
                })
                
                # Update capital
                capital += exit_value
            
            # Calculate performance metrics
            final_capital = capital
            total_return = ((final_capital - initial_capital) / initial_capital) * 100
            
            # Count wins and losses
            wins = 0
            losses = 0
            total_profit = 0
            total_loss = 0
            
            buy_trades = [t for t in trades if t["action"] == "buy"]
            sell_trades = [t for t in trades if t["action"] == "sell"]
            
            for i in range(min(len(buy_trades), len(sell_trades))):
                if "profit_loss" in sell_trades[i]:
                    profit_loss = sell_trades[i]["profit_loss"]
                    
                    if profit_loss > 0:
                        wins += 1
                        total_profit += profit_loss
                    else:
                        losses += 1
                        total_loss += abs(profit_loss)
            
            total_trades = wins + losses
            win_rate = (wins / total_trades) * 100 if total_trades > 0 else 0
            profit_factor = total_profit / total_loss if total_loss > 0 else (total_profit > 0 and 100 or 0)
            
            # Calculate drawdown
            max_drawdown = 0
            peak = initial_capital
            trough = initial_capital
            
            cumulative_capital = initial_capital
            equity_curve = [{"time": start_date, "value": initial_capital}]
            
            for trade in trades:
                if trade["action"] == "buy":
                    cumulative_capital -= trade["value"]
                else:
                    cumulative_capital += trade["value"]
                
                equity_curve.append({
                    "time": trade["time"],
                    "value": cumulative_capital
                })
                
                # Update peak and trough
                if cumulative_capital > peak:
                    peak = cumulative_capital
                    trough = peak  # Reset trough when a new peak is reached
                elif cumulative_capital < trough:
                    trough = cumulative_capital
                    
                    # Calculate drawdown
                    drawdown = ((peak - trough) / peak) * 100
                    if drawdown > max_drawdown:
                        max_drawdown = drawdown
            
            # Return backtest results
            return {
                "strategy": {
                    "type": type_str,
                    "parameters": parameters
                },
                "period": {
                    "start": start_date,
                    "end": end_date
                },
                "initial_capital": initial_capital,
                "final_capital": final_capital,
                "total_return": total_return,
                "trades": trades,
                "metrics": {
                    "trades": total_trades,
                    "wins": wins,
                    "losses": losses,
                    "win_rate": win_rate,
                    "profit_factor": profit_factor,
                    "max_drawdown": max_drawdown
                },
                "equity_curve": equity_curve
            }
        
        except Exception as e:
            self.logger.error(f"Backtest failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def generate_technicals(self, prices: List[float], current_price: float, symbol: str) -> Dict[str, Any]:
        """
        Generate synthetic technical indicators for backtesting
        
        Args:
            prices: Array of historical prices
            current_price: Current price
            symbol: Cryptocurrency symbol
            
        Returns:
            Technical indicators
        """
        # Use numpy for calculations
        prices_array = np.array(prices)
        
        # Calculate EMAs
        short_ema = self.calculate_ema(prices_array, 9)
        medium_ema = self.calculate_ema(prices_array, 21)
        long_ema = self.calculate_ema(prices_array, 50)
        
        # Calculate RSI
        rsi = self.calculate_rsi(prices_array, 14)
        
        # Calculate MACD
        macd = self.calculate_macd(prices_array, 12, 26, 9)
        
        # Calculate Bollinger Bands
        bollinger = self.calculate_bollinger_bands(prices_array, 20, 2)
        
        return {
            "symbol": symbol,
            "price": current_price,
            "ema": {
                "short": short_ema,
                "medium": medium_ema,
                "long": long_ema
            },
            "rsi": rsi,
            "macd": macd,
            "bollinger": bollinger,
            "signal": "neutral",  # Will be determined by the strategy
            "timestamp": datetime.now().isoformat()
        }
    
    def calculate_ema(self, prices: np.ndarray, period: int) -> float:
        """Calculate EMA for backtesting"""
        if len(prices) < period:
            return prices[-1]
        
        # Calculate simple moving average (SMA) for the initial value
        sma = np.mean(prices[:period])
        
        # Calculate the multiplier
        multiplier = 2 / (period + 1)
        
        # Calculate EMA
        ema = sma
        for i in range(period, len(prices)):
            ema = (prices[i] - ema) * multiplier + ema
        
        return float(ema)
    
    def calculate_rsi(self, prices: np.ndarray, period: int) -> float:
        """Calculate RSI for backtesting"""
        if len(prices) <= period:
            return 50
        
        # Calculate price changes
        deltas = np.diff(prices)
        
        # Calculate gains and losses
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        # Calculate average gain and loss
        avg_gain = np.mean(gains[:period])
        avg_loss = np.mean(losses[:period])
        
        # Calculate RS values for the remaining periods
        for i in range(period, len(deltas)):
            avg_gain = ((avg_gain * (period - 1)) + gains[i]) / period
            avg_loss = ((avg_loss * (period - 1)) + losses[i]) / period
        
        # Calculate RSI
        if avg_loss == 0:
            return 100
        
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))
    
    def calculate_macd(self, prices: np.ndarray, fast_period: int, slow_period: int, signal_period: int) -> Dict[str, float]:
        """Calculate MACD for backtesting"""
        # Calculate fast and slow EMAs
        fast_ema = self.calculate_ema(prices, fast_period)
        slow_ema = self.calculate_ema(prices, slow_period)
        
        # Calculate MACD line
        macd_line = fast_ema - slow_ema
        
        # Generate simple MACD history
        macd_history = np.full(signal_period, macd_line)
        
        # Calculate signal line
        signal_line = np.mean(macd_history)
        
        return {
            "value": float(macd_line),
            "signal": float(signal_line),
            "histogram": float(macd_line - signal_line)
        }
    
    def calculate_bollinger_bands(self, prices: np.ndarray, period: int, deviations: int) -> Dict[str, float]:
        """Calculate Bollinger Bands for backtesting"""
        if len(prices) < period:
            price = prices[-1]
            return {
                "upper": price * 1.02,
                "middle": price,
                "lower": price * 0.98
            }
        
        # Calculate the SMA (middle band)
        recent_prices = prices[-period:]
        sma = np.mean(recent_prices)
        
        # Calculate standard deviation
        std_dev = np.std(recent_prices)
        
        # Calculate upper and lower bands
        upper_band = sma + (std_dev * deviations)
        lower_band = sma - (std_dev * deviations)
        
        return {
            "upper": float(upper_band),
            "middle": float(sma),
            "lower": float(lower_band)
        }
