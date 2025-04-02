"""
Helper utilities for Crypto Trading Bot
"""
import logging
import numpy as np
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Union

# Configure logging
def setup_logger(name: str, level: str = 'INFO') -> logging.Logger:
    """
    Set up a logger with the specified name and level
    
    Args:
        name: Logger name
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        
    Returns:
        Logger instance
    """
    logger = logging.getLogger(name)
    
    # Convert level string to logging level
    level_map = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }
    log_level = level_map.get(level.upper(), logging.INFO)
    logger.setLevel(log_level)
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(console_handler)
    
    return logger

# Date and time utilities
def utc_now() -> datetime:
    """
    Get current UTC datetime
    
    Returns:
        Current UTC datetime
    """
    return datetime.now(timezone.utc)

def iso_to_datetime(iso_str: str) -> datetime:
    """
    Convert ISO 8601 string to datetime
    
    Args:
        iso_str: ISO 8601 datetime string
        
    Returns:
        Datetime object
    """
    return datetime.fromisoformat(iso_str.replace('Z', '+00:00'))

# Financial calculation utilities
def calculate_returns(prices: List[float]) -> List[float]:
    """
    Calculate percentage returns from a series of prices
    
    Args:
        prices: List of prices
        
    Returns:
        List of percentage returns
    """
    if len(prices) < 2:
        return []
    
    return [(prices[i] - prices[i-1]) / prices[i-1] * 100 for i in range(1, len(prices))]

def calculate_sharpe_ratio(returns: List[float], risk_free_rate: float = 0.0) -> float:
    """
    Calculate the Sharpe ratio
    
    Args:
        returns: List of percentage returns
        risk_free_rate: Risk-free rate (annualized)
        
    Returns:
        Sharpe ratio
    """
    if not returns:
        return 0.0
    
    # Convert to numpy array
    returns_array = np.array(returns)
    
    # Calculate statistics
    mean_return = np.mean(returns_array)
    std_dev = np.std(returns_array)
    
    if std_dev == 0:
        return 0.0
    
    # Calculate annualized Sharpe ratio (assuming daily returns)
    sharpe = (mean_return - risk_free_rate) / std_dev * np.sqrt(252)
    
    return float(sharpe)

def calculate_drawdown(equity_curve: List[float]) -> tuple:
    """
    Calculate maximum drawdown
    
    Args:
        equity_curve: List of equity values over time
        
    Returns:
        Tuple of (maximum drawdown percentage, peak, trough)
    """
    if not equity_curve:
        return 0.0, 0.0, 0.0
    
    max_drawdown = 0.0
    peak = equity_curve[0]
    trough = equity_curve[0]
    current_peak = equity_curve[0]
    
    for value in equity_curve:
        if value > current_peak:
            current_peak = value
        
        # Calculate drawdown
        drawdown = (current_peak - value) / current_peak * 100
        
        if drawdown > max_drawdown:
            max_drawdown = drawdown
            peak = current_peak
            trough = value
    
    return max_drawdown, peak, trough

# Data transformation utilities
def group_by_interval(data: List[Dict[str, Any]], time_key: str, interval: str = 'day') -> Dict[str, List[Dict[str, Any]]]:
    """
    Group data by time interval
    
    Args:
        data: List of dictionaries containing time data
        time_key: Key for the time field in each dictionary
        interval: Time interval (day, hour, minute)
        
    Returns:
        Dictionary with intervals as keys and lists of data as values
    """
    result = {}
    
    for item in data:
        # Convert time to datetime
        dt = iso_to_datetime(item[time_key])
        
        # Generate interval key
        if interval == 'day':
            key = dt.strftime('%Y-%m-%d')
        elif interval == 'hour':
            key = dt.strftime('%Y-%m-%d %H:00')
        elif interval == 'minute':
            key = dt.strftime('%Y-%m-%d %H:%M')
        else:
            key = dt.strftime('%Y-%m-%d')
        
        # Add item to result
        if key not in result:
            result[key] = []
        
        result[key].append(item)
    
    return result

# Error handling
def safe_request(func):
    """
    Decorator for safe API requests with error handling
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger = logging.getLogger("api")
            logger.error(f"API request failed: {str(e)}")
            return None
    
    return wrapper
