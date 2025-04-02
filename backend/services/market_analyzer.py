"""
Market Analyzer module for Crypto Trading Bot
Analyzes market conditions and detects market regimes
"""
import time
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Union
from datetime import datetime

class MarketAnalyzer:
    """Analyzes cryptocurrency market conditions and provides trading signals"""
    
    def __init__(self):
        """Initialize the market analyzer with indicators configuration"""
        # Technical indicators configuration
        self.indicators = {
            "ema": {
                "short": 9,
                "medium": 21,
                "long": 50
            },
            "rsi": {
                "period": 14,
                "oversold": 30,
                "overbought": 70
            },
            "macd": {
                "fast": 12,
                "slow": 26,
                "signal": 9
            },
            "atr": {
                "period": 14
            },
            "bollinger": {
                "period": 20,
                "deviations": 2
            }
        }
        
        # Market regime thresholds
        self.regime_thresholds = {
            "volatility": {
                "low": 0.005,  # 0.5%
                "high": 0.02   # 2%
            },
            "trend_strength": {
                "weak": 20,
                "strong": 50
            }
        }
        
        # Cache for analysis results
        self.cache = {
            "regime_detection": {},
            "technical_analysis": {}
        }
        
        # Cache expiration (in seconds)
        self.cache_expiration = {
            "regime_detection": 300,  # 5 minutes
            "technical_analysis": 300  # 5 minutes
        }
        
        self.logger = logging.getLogger(__name__)
    
    def analyze_market(self, symbol: str, historical_data: Optional[Dict[str, List[Dict[str, Any]]]] = None) -> Dict[str, Any]:
        """
        Analyze market conditions and detect regime
        
        Args:
            symbol: Cryptocurrency symbol (e.g., bitcoin)
            historical_data: Optional pre-fetched historical data
            
        Returns:
            Market analysis results
        """
        cache_key = f"regime_{symbol}"
        
        # Check cache first
        if cache_key in self.cache["regime_detection"]:
            cached_data = self.cache["regime_detection"][cache_key]
            if time.time() - cached_data["timestamp"] < self.cache_expiration["regime_detection"]:
                return cached_data["data"]
        
        try:
            # Use provided historical data or fetch it from API service
            if not historical_data:
                # This function should be implemented by the API service
                # For now, we'll handle it differently in testing vs. production
                from flask import current_app
                if current_app:
                    historical_data = current_app.api_service.get_historical_data(symbol, "30")
                else:
                    # Fallback to direct import for testing
                    from services.api_service import ApiService
                    api_service = ApiService()
                    historical_data = api_service.get_historical_data(symbol, "30")
            
            if not historical_data or not historical_data.get("prices") or len(historical_data["prices"]) == 0:
                raise ValueError("No historical data available")
            
            # Extract prices for analysis
            prices = [item["value"] for item in historical_data["prices"]]
            
            # Calculate volatility
            volatility = self.calculate_volatility(prices)
            
            # Calculate trend strength
            trend_strength = self.calculate_trend_strength(prices)
            
            # Detect market regime
            regime = self.detect_regime(volatility, trend_strength)
            
            # Calculate confidence
            confidence = self.calculate_confidence(volatility, trend_strength, regime)
            
            # Create analysis result
            result = {
                "symbol": symbol,
                "regime": regime,
                "volatility": volatility,
                "trend_strength": trend_strength,
                "confidence": confidence,
                "timestamp": datetime.now().isoformat()
            }
            
            # Cache the result
            self.cache["regime_detection"][cache_key] = {
                "data": result,
                "timestamp": time.time()
            }
            
            return result
        
        except Exception as e:
            self.logger.error(f"Failed to analyze market for {symbol}: {str(e)}")
            
            # Return cached data if available, even if expired
            if cache_key in self.cache["regime_detection"]:
                return self.cache["regime_detection"][cache_key]["data"]
            
            # Return default analysis if no data is available
            return {
                "symbol": symbol,
                "regime": "unknown",
                "volatility": 0,
                "trend_strength": 0,
                "confidence": 0,
                "timestamp": datetime.now().isoformat()
            }
    
    def calculate_volatility(self, prices: List[float]) -> float:
        """
        Calculate price volatility (standard deviation of returns)
        
        Args:
            prices: Array of prices
            
        Returns:
            Volatility value
        """
        if len(prices) < 2:
            return 0
        
        # Convert to numpy array
        prices_array = np.array(prices)
        
        # Calculate returns
        returns = np.diff(prices_array) / prices_array[:-1]
        
        # Calculate standard deviation
        volatility = np.std(returns)
        
        return float(volatility)
    
    def calculate_trend_strength(self, prices: List[float]) -> float:
        """
        Calculate trend strength using ADX-like indicator
        
        Args:
            prices: Array of prices
            
        Returns:
            Trend strength value (0-100)
        """
        if len(prices) < 14:
            return 0
        
        # Simplified ADX calculation for demonstration
        # In a real system, this would be a proper ADX calculation
        
        # Calculate price direction
        price_diff = np.diff(prices)
        up_moves = np.sum(price_diff > 0)
        down_moves = np.sum(price_diff < 0)
        
        # Calculate trend consistency
        total_moves = up_moves + down_moves
        dominant_moves = max(up_moves, down_moves)
        
        if total_moves == 0:
            return 0
        
        # Normalize to 0-100 scale
        trend_strength = (dominant_moves / total_moves) * 100
        
        return float(trend_strength)
    
    def detect_regime(self, volatility: float, trend_strength: float) -> str:
        """
        Detect market regime based on volatility and trend strength
        
        Args:
            volatility: Volatility value
            trend_strength: Trend strength value
            
        Returns:
            Market regime (trending, sideways, volatile)
        """
        if volatility > self.regime_thresholds["volatility"]["high"]:
            return "volatile"
        elif trend_strength > self.regime_thresholds["trend_strength"]["strong"]:
            return "trending"
        else:
            return "sideways"
    
    def calculate_confidence(self, volatility: float, trend_strength: float, regime: str) -> float:
        """
        Calculate confidence level for regime detection
        
        Args:
            volatility: Volatility value
            trend_strength: Trend strength value
            regime: Detected regime
            
        Returns:
            Confidence value (0-100)
        """
        if regime == "volatile":
            # Higher volatility = higher confidence for volatile regime
            volatility_ratio = min(volatility / (self.regime_thresholds["volatility"]["high"] * 2), 1)
            return volatility_ratio * 100
        
        elif regime == "trending":
            # Higher trend strength = higher confidence for trending regime
            return min(trend_strength, 100)
        
        elif regime == "sideways":
            # Lower volatility and lower trend strength = higher confidence for sideways regime
            volatility_factor = 1 - min(volatility / self.regime_thresholds["volatility"]["high"], 1)
            trend_factor = 1 - min(trend_strength / self.regime_thresholds["trend_strength"]["strong"], 1)
            return (volatility_factor * trend_factor) * 100
        
        else:
            return 0
    
    def get_recommended_strategy(self, regime: str) -> Dict[str, Any]:
        """
        Get recommended trading strategy based on market regime
        
        Args:
            regime: Market regime (trending, sideways, volatile)
            
        Returns:
            Recommended strategy
        """
        if regime == "trending":
            return {
                "name": "Trend Following",
                "type": "trend",
                "parameters": {
                    "short_ema": self.indicators["ema"]["short"],
                    "long_ema": self.indicators["ema"]["medium"]
                }
            }
        
        elif regime == "sideways":
            return {
                "name": "Mean Reversion",
                "type": "mean_reversion",
                "parameters": {
                    "width": 2.0,
                    "levels": 10
                }
            }
        
        elif regime == "volatile":
            return {
                "name": "Market Making",
                "type": "market_making",
                "parameters": {
                    "spread": 0.5,
                    "order_size": 5
                }
            }
        
        else:
            return {
                "name": "Conservative",
                "type": "conservative",
                "parameters": {
                    "short_ema": self.indicators["ema"]["short"],
                    "long_ema": self.indicators["ema"]["long"]
                }
            }
    
    def analyze_technicals(self, symbol: str, historical_data: Optional[Dict[str, List[Dict[str, Any]]]] = None) -> Dict[str, Any]:
        """
        Perform technical analysis on a cryptocurrency
        
        Args:
            symbol: Cryptocurrency symbol (e.g., bitcoin)
            historical_data: Optional pre-fetched historical data
            
        Returns:
            Technical analysis results
        """
        cache_key = f"technicals_{symbol}"
        
        # Check cache first
        if cache_key in self.cache["technical_analysis"]:
            cached_data = self.cache["technical_analysis"][cache_key]
            if time.time() - cached_data["timestamp"] < self.cache_expiration["technical_analysis"]:
                return cached_data["data"]
        
        try:
            # Use provided historical data or fetch it from API service
            if not historical_data:
                # This function should be implemented by the API service
                # For now, we'll handle it differently in testing vs. production
                from flask import current_app
                if current_app:
                    historical_data = current_app.api_service.get_historical_data(symbol, "30")
                else:
                    # Fallback to direct import for testing
                    from services.api_service import ApiService
                    api_service = ApiService()
                    historical_data = api_service.get_historical_data(symbol, "30")
            
            if not historical_data or not historical_data.get("prices") or len(historical_data["prices"]) == 0:
                raise ValueError("No historical data available")
            
            # Extract prices for analysis
            prices = [item["value"] for item in historical_data["prices"]]
            
            # Calculate EMA indicators
            short_ema = self.calculate_ema(prices, self.indicators["ema"]["short"])
            medium_ema = self.calculate_ema(prices, self.indicators["ema"]["medium"])
            long_ema = self.calculate_ema(prices, self.indicators["ema"]["long"])
            
            # Calculate RSI
            rsi = self.calculate_rsi(prices, self.indicators["rsi"]["period"])
            
            # Calculate MACD
            macd = self.calculate_macd(
                prices,
                self.indicators["macd"]["fast"],
                self.indicators["macd"]["slow"],
                self.indicators["macd"]["signal"]
            )
            
            # Calculate Bollinger Bands
            bollinger = self.calculate_bollinger_bands(
                prices,
                self.indicators["bollinger"]["period"],
                self.indicators["bollinger"]["deviations"]
            )
            
            # Determine overall signal
            current_price = prices[-1]
            signal = self.determine_signal(current_price, short_ema, medium_ema, rsi, macd)
            
            # Create analysis result
            result = {
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
                "signal": signal,
                "timestamp": datetime.now().isoformat()
            }
            
            # Cache the result
            self.cache["technical_analysis"][cache_key] = {
                "data": result,
                "timestamp": time.time()
            }
            
            return result
        
        except Exception as e:
            self.logger.error(f"Failed to analyze technicals for {symbol}: {str(e)}")
            
            # Return cached data if available, even if expired
            if cache_key in self.cache["technical_analysis"]:
                return self.cache["technical_analysis"][cache_key]["data"]
            
            # Return empty analysis if no data is available
            return {
                "symbol": symbol,
                "price": 0,
                "ema": {"short": 0, "medium": 0, "long": 0},
                "rsi": 0,
                "macd": {"value": 0, "signal": 0, "histogram": 0},
                "bollinger": {"upper": 0, "middle": 0, "lower": 0},
                "signal": "neutral",
                "timestamp": datetime.now().isoformat()
            }
    
    def calculate_ema(self, prices: List[float], period: int) -> float:
        """
        Calculate Exponential Moving Average (EMA)
        
        Args:
            prices: Array of prices
            period: EMA period
            
        Returns:
            EMA value
        """
        if len(prices) < period:
            return prices[-1]
        
        prices_array = np.array(prices)
        
        # Calculate simple moving average (SMA) for the initial value
        sma = np.mean(prices_array[:period])
        
        # Calculate the multiplier
        multiplier = 2 / (period + 1)
        
        # Calculate EMA
        ema = sma
        for i in range(period, len(prices_array)):
            ema = (prices_array[i] - ema) * multiplier + ema
        
        return float(ema)
    
    def calculate_rsi(self, prices: List[float], period: int) -> float:
        """
        Calculate Relative Strength Index (RSI)
        
        Args:
            prices: Array of prices
            period: RSI period
            
        Returns:
            RSI value
        """
        if len(prices) <= period:
            return 50  # Default value if not enough data
        
        prices_array = np.array(prices)
        deltas = np.diff(prices_array)
        
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
        rsi = 100 - (100 / (1 + rs))
        
        return float(rsi)
    
    def calculate_macd(self, prices: List[float], fast_period: int, slow_period: int, signal_period: int) -> Dict[str, float]:
        """
        Calculate Moving Average Convergence Divergence (MACD)
        
        Args:
            prices: Array of prices
            fast_period: Fast EMA period
            slow_period: Slow EMA period
            signal_period: Signal EMA period
            
        Returns:
            MACD, signal line, and histogram values
        """
        if len(prices) < max(fast_period, slow_period) + signal_period:
            return {
                "value": 0,
                "signal": 0,
                "histogram": 0
            }
        
        # Calculate fast and slow EMAs
        fast_ema = self.calculate_ema(prices, fast_period)
        slow_ema = self.calculate_ema(prices, slow_period)
        
        # Calculate MACD line
        macd_line = fast_ema - slow_ema
        
        # Generate MACD history for signal line calculation
        macd_history = []
        for i in range(slow_period - 1, len(prices)):
            fast = self.calculate_ema(prices[:i+1], fast_period)
            slow = self.calculate_ema(prices[:i+1], slow_period)
            macd_history.append(fast - slow)
        
        # Calculate signal line
        signal_line = self.calculate_ema(macd_history, signal_period)
        
        # Calculate histogram
        histogram = macd_line - signal_line
        
        return {
            "value": float(macd_line),
            "signal": float(signal_line),
            "histogram": float(histogram)
        }
    
    def calculate_bollinger_bands(self, prices: List[float], period: int, deviations: int) -> Dict[str, float]:
        """
        Calculate Bollinger Bands
        
        Args:
            prices: Array of prices
            period: Bollinger Bands period
            deviations: Number of standard deviations
            
        Returns:
            Upper, middle, and lower band values
        """
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
    
    def determine_signal(self, price: float, short_ema: float, medium_ema: float, rsi: float, macd: Dict[str, float]) -> str:
        """
        Determine overall trading signal based on technical indicators
        
        Args:
            price: Current price
            short_ema: Short-term EMA
            medium_ema: Medium-term EMA
            rsi: RSI value
            macd: MACD values
            
        Returns:
            Trading signal (buy, sell, neutral)
        """
        bullish_signals = 0
        bearish_signals = 0
        
        # EMA crossover
        if short_ema > medium_ema:
            bullish_signals += 1
        elif short_ema < medium_ema:
            bearish_signals += 1
        
        # RSI
        if rsi < self.indicators["rsi"]["oversold"]:
            bullish_signals += 1
        elif rsi > self.indicators["rsi"]["overbought"]:
            bearish_signals += 1
        
        # MACD
        if macd["histogram"] > 0:
            bullish_signals += 1
        elif macd["histogram"] < 0:
            bearish_signals += 1
        
        # Price relative to EMAs
        if price > short_ema and price > medium_ema:
            bullish_signals += 1
        elif price < short_ema and price < medium_ema:
            bearish_signals += 1
        
        # Determine overall signal
        if bullish_signals > bearish_signals and bullish_signals >= 3:
            return "buy"
        elif bearish_signals > bullish_signals and bearish_signals >= 3:
            return "sell"
        else:
            return "neutral"
