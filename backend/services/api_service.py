"""
API Service module for Crypto Trading Bot
Handles connections to external cryptocurrency APIs
"""
import os
import time
import json
import logging
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
from requests.exceptions import RequestException
from cryptography.fernet import Fernet

class ApiService:
    """Service for interacting with external cryptocurrency APIs"""
    
    def __init__(self):
        """Initialize the API service with base URLs and cache"""
        # Base URLs for various APIs
        self.logger = logging.getLogger(__name__)
        self.api_urls = {
            "coingecko": "https://api.coingecko.com/api/v3",
            "binance": "https://api.binance.com/api/v3",
            "kraken": "https://api.kraken.com/0/public",
            "coinbase": "https://api.exchange.coinbase.com"
        }
        
        # Cache for API responses
        self.cache = {
            "market_data": {},
            "historical_data": {}
        }
        
        # Cache expiration (in seconds)
        self.cache_expiration = {
            "market_data": 30,  # 30 seconds
            "historical_data": 300  # 5 minutes
        }
        
        # Exchange API keys - will be set by the user
        self.exchange_keys = {
            "binance": {"api_key": None, "api_secret": None, "enabled": False},
            "kraken": {"api_key": None, "api_secret": None, "enabled": False},
            "coinbase": {"api_key": None, "api_secret": None, "enabled": False}
        }
        
        # Set up encryption for API keys
        self._setup_encryption()
        
        # Load API keys from environment if available
        self._load_api_keys_from_env()
        
        self.active_exchange = None
        self.logger = logging.getLogger(__name__)
    
    def _setup_encryption(self):
        """Set up encryption for API keys"""
        key = os.environ.get("API_KEY_ENCRYPTION_KEY")
        if not key:
            key = Fernet.generate_key()
            self.logger.warning("No API_KEY_ENCRYPTION_KEY found. Generated a temporary one.")
        
        self.cipher = Fernet(key if isinstance(key, bytes) else key.encode())
    
    def _load_api_keys_from_env(self):
        """Load API keys from environment variables"""
        for exchange in self.exchange_keys:
            api_key = os.environ.get(f"{exchange.upper()}_API_KEY")
            api_secret = os.environ.get(f"{exchange.upper()}_API_SECRET")
            
            if api_key and api_secret:
                self.set_exchange_keys(exchange, api_key, api_secret)
    
    def set_exchange_keys(self, exchange: str, api_key: str, api_secret: str) -> bool:
        """
        Set API keys for an exchange
        
        Args:
            exchange: Exchange name (binance, kraken, coinbase)
            api_key: API key
            api_secret: API secret
            
        Returns:
            Success status
        """
        if exchange not in self.exchange_keys:
            self.logger.error(f"Exchange {exchange} not supported")
            return False
        
        # Encrypt API keys
        encrypted_key = self.cipher.encrypt(api_key.encode()).decode()
        encrypted_secret = self.cipher.encrypt(api_secret.encode()).decode()
        
        self.exchange_keys[exchange] = {
            "api_key": encrypted_key,
            "api_secret": encrypted_secret,
            "enabled": True
        }
        
        # Set as active exchange if none is active
        if not self.active_exchange:
            self.active_exchange = exchange
        
        return True
    
    def get_exchange_keys(self, exchange: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Get decrypted API keys for an exchange
        
        Args:
            exchange: Exchange name
            
        Returns:
            Tuple of (api_key, api_secret) or (None, None) if not set
        """
        if exchange not in self.exchange_keys or not self.exchange_keys[exchange]["enabled"]:
            return None, None
        
        # Decrypt API keys
        encrypted_key = self.exchange_keys[exchange]["api_key"]
        encrypted_secret = self.exchange_keys[exchange]["api_secret"]
        
        if not encrypted_key or not encrypted_secret:
            return None, None
        
        api_key = self.cipher.decrypt(encrypted_key.encode()).decode()
        api_secret = self.cipher.decrypt(encrypted_secret.encode()).decode()
        
        return api_key, api_secret
    
    def set_active_exchange(self, exchange: str) -> bool:
        """
        Set active exchange for trading
        
        Args:
            exchange: Exchange name
            
        Returns:
            Success status
        """
        if exchange not in self.exchange_keys or not self.exchange_keys[exchange]["enabled"]:
            self.logger.error(f"Exchange {exchange} not configured")
            return False
        
        self.active_exchange = exchange
        return True
    
    def get_top_markets(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get top cryptocurrency market data
        
        Args:
            limit: Number of cryptocurrencies to fetch
            
        Returns:
            List of cryptocurrency market data
        """
        cache_key = f"top_markets_{limit}"
        
        # Check cache first
        if cache_key in self.cache["market_data"]:
            cached_data = self.cache["market_data"][cache_key]
            if time.time() - cached_data["timestamp"] < self.cache_expiration["market_data"]:
                return cached_data["data"]
        
        try:
            response = requests.get(
                f"{self.api_urls['coingecko']}/coins/markets",
                params={
                    "vs_currency": "usd",
                    "order": "market_cap_desc",
                    "per_page": limit,
                    "page": 1,
                    "sparkline": "false",
                    "price_change_percentage": "24h"
                },
                timeout=10
            )
            
            response.raise_for_status()
            data = response.json()
            
            # Add market regime (this would be calculated by the market analyzer)
            # For now, we'll just assign random regimes for demonstration purposes
            import random
            regimes = ["trending", "sideways", "volatile"]
            
            enhanced_data = []
            for coin in data:
                coin_regime = random.choice(regimes)
                enhanced_data.append({
                    **coin,
                    "regime": coin_regime,
                    "confidence": round(random.random() * 100)
                })
            
            # Cache the result
            self.cache["market_data"][cache_key] = {
                "data": enhanced_data,
                "timestamp": time.time()
            }
            
            return enhanced_data
        
        except RequestException as e:
            self.logger.error(f"Failed to fetch market data: {str(e)}")
            
            # Return cached data if available, even if expired
            if cache_key in self.cache["market_data"]:
                return self.cache["market_data"][cache_key]["data"]
            
            # Return empty list if no data is available
            return []
    
    def get_historical_data(self, coin_id: str, days: str = "30") -> Dict[str, List[Dict[str, Any]]]:
        """
        Get historical price data for a cryptocurrency
        
        Args:
            coin_id: Coin ID (e.g., bitcoin, ethereum)
            days: Number of days (1, 7, 30, 90, 365, max)
            
        Returns:
            Historical price data
        """
        cache_key = f"{coin_id}_{days}"
        
        # Check cache first
        if cache_key in self.cache["historical_data"]:
            cached_data = self.cache["historical_data"][cache_key]
            if time.time() - cached_data["timestamp"] < self.cache_expiration["historical_data"]:
                return cached_data["data"]
        
        try:
            response = requests.get(
                f"{self.api_urls['coingecko']}/coins/{coin_id}/market_chart",
                params={"vs_currency": "usd", "days": days},
                timeout=10
            )
            
            response.raise_for_status()
            data = response.json()
            
            # Process the data for charting
            processed_data = {
                "prices": [
                    {"time": datetime.fromtimestamp(timestamp / 1000).isoformat(), "value": price}
                    for timestamp, price in data["prices"]
                ],
                "market_caps": [
                    {"time": datetime.fromtimestamp(timestamp / 1000).isoformat(), "value": market_cap}
                    for timestamp, market_cap in data["market_caps"]
                ],
                "total_volumes": [
                    {"time": datetime.fromtimestamp(timestamp / 1000).isoformat(), "value": volume}
                    for timestamp, volume in data["total_volumes"]
                ]
            }
            
            # Cache the result
            self.cache["historical_data"][cache_key] = {
                "data": processed_data,
                "timestamp": time.time()
            }
            
            return processed_data
        
        except RequestException as e:
            self.logger.error(f"Failed to fetch historical data for {coin_id}: {str(e)}")
            
            # Return cached data if available, even if expired
            if cache_key in self.cache["historical_data"]:
                return self.cache["historical_data"][cache_key]["data"]
            
            # Return empty object if no data is available
            return {"prices": [], "market_caps": [], "total_volumes": []}
    
    def get_coin_details(self, coin_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a cryptocurrency
        
        Args:
            coin_id: Coin ID (e.g., bitcoin, ethereum)
            
        Returns:
            Detailed coin information
        """
        cache_key = f"coin_details_{coin_id}"
        
        # Check cache first
        if cache_key in self.cache["market_data"]:
            cached_data = self.cache["market_data"][cache_key]
            if time.time() - cached_data["timestamp"] < self.cache_expiration["market_data"]:
                return cached_data["data"]
        
        try:
            response = requests.get(
                f"{self.api_urls['coingecko']}/coins/{coin_id}",
                params={
                    "localization": "false",
                    "tickers": "false",
                    "market_data": "true",
                    "community_data": "false",
                    "developer_data": "false",
                    "sparkline": "false"
                },
                timeout=10
            )
            
            response.raise_for_status()
            data = response.json()
            
            # Cache the result
            self.cache["market_data"][cache_key] = {
                "data": data,
                "timestamp": time.time()
            }
            
            return data
        
        except RequestException as e:
            self.logger.error(f"Failed to fetch details for {coin_id}: {str(e)}")
            
            # Return cached data if available, even if expired
            if cache_key in self.cache["market_data"]:
                return self.cache["market_data"][cache_key]["data"]
            
            # Return None if no data is available
            return None
    
    def get_multiple_prices(self, coin_ids: List[str]) -> Dict[str, Any]:
        """
        Get price data for multiple cryptocurrencies
        
        Args:
            coin_ids: List of coin IDs
            
        Returns:
            Price data for the specified coins
        """
        if not coin_ids:
            return {}
        
        cache_key = f"multiple_prices_{'_'.join(coin_ids)}"
        
        # Check cache first
        if cache_key in self.cache["market_data"]:
            cached_data = self.cache["market_data"][cache_key]
            if time.time() - cached_data["timestamp"] < self.cache_expiration["market_data"]:
                return cached_data["data"]
        
        try:
            response = requests.get(
                f"{self.api_urls['coingecko']}/simple/price",
                params={
                    "ids": ",".join(coin_ids),
                    "vs_currencies": "usd",
                    "include_market_cap": "true",
                    "include_24hr_vol": "true",
                    "include_24hr_change": "true"
                },
                timeout=10
            )
            
            response.raise_for_status()
            data = response.json()
            
            # Cache the result
            self.cache["market_data"][cache_key] = {
                "data": data,
                "timestamp": time.time()
            }
            
            return data
        
        except RequestException as e:
            self.logger.error(f"Failed to fetch multiple prices: {str(e)}")
            
            # Return cached data if available, even if expired
            if cache_key in self.cache["market_data"]:
                return self.cache["market_data"][cache_key]["data"]
            
            # Return empty object if no data is available
            return {}
    
    def get_correlations(self, base_coin: str) -> List[Dict[str, Any]]:
        """
        Get correlations between a base coin and other coins
        
        Args:
            base_coin: Base coin ID (e.g., bitcoin)
            
        Returns:
            Array of correlated cryptocurrencies
        """
        # In a real system, this would use historical price data to calculate correlations
        # For demonstration, we'll generate random correlation data
        import random
        
        cache_key = f"correlations_{base_coin}"
        
        # Check cache first
        if cache_key in self.cache["market_data"]:
            cached_data = self.cache["market_data"][cache_key]
            if time.time() - cached_data["timestamp"] < self.cache_expiration["market_data"]:
                return cached_data["data"]
        
        try:
            # Get top markets first
            top_markets = self.get_top_markets(100)
            
            # Filter out the base coin
            other_coins = [coin for coin in top_markets if coin["id"] != base_coin]
            
            # Generate correlation data
            correlations = []
            for coin in other_coins:
                correlation_score = 0.5 + (random.random() * 0.5)  # Random correlation between 0.5 and 1.0
                performance_delta = (random.random() * 40) - 20  # Random performance delta between -20% and +20%
                
                correlations.append({
                    "id": coin["id"],
                    "symbol": coin["symbol"].upper(),
                    "name": coin["name"],
                    "correlation_score": correlation_score,
                    "performance_delta": performance_delta,
                    "current_price": coin["current_price"],
                    "volume": coin["total_volume"],
                    "market_cap": coin["market_cap"]
                })
            
            # Sort by correlation score (descending)
            correlations.sort(key=lambda x: x["correlation_score"], reverse=True)
            
            # Cache the result
            self.cache["market_data"][cache_key] = {
                "data": correlations,
                "timestamp": time.time()
            }
            
            return correlations
        
        except Exception as e:
            self.logger.error(f"Failed to get correlations for {base_coin}: {str(e)}")
            
            # Return cached data if available, even if expired
            if cache_key in self.cache["market_data"]:
                return self.cache["market_data"][cache_key]["data"]
            
            # Return empty array if no data is available
            return []
    
    def execute_trade(self, symbol: str, side: str, quantity: float, simulation: bool = True) -> Dict[str, Any]:
        """
        Execute a trade on the active exchange
        
        Args:
            symbol: Trading pair symbol (e.g., BTCUSDT)
            side: Trade side (buy or sell)
            quantity: Trade quantity
            simulation: Whether to simulate the trade
            
        Returns:
            Trade execution result
        """
        if simulation:
            # Simulate trade
            import random
            price = random.uniform(30000, 40000) if "BTC" in symbol else random.uniform(1000, 2000)
            return {
                "success": True,
                "simulation": True,
                "symbol": symbol,
                "side": side,
                "quantity": quantity,
                "price": price,
                "value": price * quantity,
                "timestamp": datetime.now().isoformat()
            }
        else:
            # Real trade execution
            if not self.active_exchange or not self.exchange_keys[self.active_exchange]["enabled"]:
                raise ValueError("No active exchange configured for trading")
            
            # Get API keys
            api_key, api_secret = self.get_exchange_keys(self.active_exchange)
            
            # Execute trade based on the active exchange
            # This would involve calling the exchange-specific API
            # For now, we'll just return a simulated trade
            self.logger.info(f"Executing {side} trade for {quantity} {symbol}")
            
            # Placeholder for real trading logic
            
            return {
                "success": True,
                "simulation": False,
                "symbol": symbol,
                "side": side,
                "quantity": quantity,
                "timestamp": datetime.now().isoformat()
            }
