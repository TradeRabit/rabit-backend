"""
Interval/Timeframe utilities for OHLC data
"""
from typing import Dict, List


# All supported intervals
SUPPORTED_INTERVALS = [
    # Minutes
    "1m", "3m", "5m", "15m", "30m",
    # Hours
    "1h", "2h", "4h", "6h", "8h", "12h",
    # Days
    "1d", "3d",
    # Weeks
    "1w",
    # Months
    "1M"
]


def get_interval_ms(interval: str) -> int:
    """
    Get interval duration in milliseconds
    
    Args:
        interval: Interval string (e.g., '1m', '5m', '1h', '1d')
        
    Returns:
        Duration in milliseconds
    """
    intervals = {
        # Minutes
        "1m": 60 * 1000,
        "3m": 3 * 60 * 1000,
        "5m": 5 * 60 * 1000,
        "15m": 15 * 60 * 1000,
        "30m": 30 * 60 * 1000,
        # Hours
        "1h": 60 * 60 * 1000,
        "2h": 2 * 60 * 60 * 1000,
        "4h": 4 * 60 * 60 * 1000,
        "6h": 6 * 60 * 60 * 1000,
        "8h": 8 * 60 * 60 * 1000,
        "12h": 12 * 60 * 60 * 1000,
        # Days
        "1d": 24 * 60 * 60 * 1000,
        "3d": 3 * 24 * 60 * 60 * 1000,
        # Weeks
        "1w": 7 * 24 * 60 * 60 * 1000,
        # Months (approximate)
        "1M": 30 * 24 * 60 * 60 * 1000,
    }
    return intervals.get(interval, 60 * 60 * 1000)  # Default to 1h


def get_interval_seconds(interval: str) -> int:
    """
    Get interval duration in seconds
    
    Args:
        interval: Interval string
        
    Returns:
        Duration in seconds
    """
    return get_interval_ms(interval) // 1000


def is_valid_interval(interval: str) -> bool:
    """
    Check if interval is valid
    
    Args:
        interval: Interval string
        
    Returns:
        True if valid, False otherwise
    """
    return interval in SUPPORTED_INTERVALS


def get_interval_category(interval: str) -> str:
    """
    Get interval category (minute, hour, day, week, month)
    
    Args:
        interval: Interval string
        
    Returns:
        Category name
    """
    if interval.endswith('m'):
        return "minute"
    elif interval.endswith('h'):
        return "hour"
    elif interval.endswith('d'):
        return "day"
    elif interval.endswith('w'):
        return "week"
    elif interval.endswith('M'):
        return "month"
    return "unknown"


def get_intervals_by_category() -> Dict[str, List[str]]:
    """
    Get intervals grouped by category
    
    Returns:
        Dictionary with category as key and list of intervals as value
    """
    return {
        "minute": ["1m", "3m", "5m", "15m", "30m"],
        "hour": ["1h", "2h", "4h", "6h", "8h", "12h"],
        "day": ["1d", "3d"],
        "week": ["1w"],
        "month": ["1M"]
    }


def format_interval_human(interval: str) -> str:
    """
    Format interval for human reading
    
    Args:
        interval: Interval string (e.g., '1m', '4h', '1d')
        
    Returns:
        Human-readable string (e.g., '1 minute', '4 hours', '1 day')
    """
    mapping = {
        "1m": "1 minute",
        "3m": "3 minutes",
        "5m": "5 minutes",
        "15m": "15 minutes",
        "30m": "30 minutes",
        "1h": "1 hour",
        "2h": "2 hours",
        "4h": "4 hours",
        "6h": "6 hours",
        "8h": "8 hours",
        "12h": "12 hours",
        "1d": "1 day",
        "3d": "3 days",
        "1w": "1 week",
        "1M": "1 month"
    }
    return mapping.get(interval, interval)
