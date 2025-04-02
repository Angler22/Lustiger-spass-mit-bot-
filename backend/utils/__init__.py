"""
Utilities package initialization.
This package contains helper utilities for the Crypto Trading Bot.
"""

from .helpers import (
    setup_logger,
    utc_now,
    iso_to_datetime,
    calculate_returns,
    calculate_sharpe_ratio,
    calculate_drawdown,
    group_by_interval,
    safe_request
)

# Export utility functions
__all__ = [
    'setup_logger',
    'utc_now',
    'iso_to_datetime',
    'calculate_returns',
    'calculate_sharpe_ratio',
    'calculate_drawdown',
    'group_by_interval',
    'safe_request'
]
