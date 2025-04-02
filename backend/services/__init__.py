"""
Services package initialization.
This package contains core service modules for the Crypto Trading Bot.
"""

from .api_service import ApiService
from .market_analyzer import MarketAnalyzer
from .strategy_manager import StrategyManager, Strategy, TrendFollowingStrategy, MeanReversionStrategy, MarketMakingStrategy, ArbitrageStrategy

# Export services and strategy classes
__all__ = [
    'ApiService',
    'MarketAnalyzer',
    'StrategyManager',
    'Strategy',
    'TrendFollowingStrategy',
    'MeanReversionStrategy',
    'MarketMakingStrategy',
    'ArbitrageStrategy'
]
