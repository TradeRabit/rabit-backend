"""Chart control tools for TradingView"""
from typing import Dict, Any
from .client import get_client
from utils.logger import get_logger
import re
from datetime import datetime

logger = get_logger(__name__)


def _normalize_response(response: Dict[str, Any], operation: str) -> Dict[str, Any]:
    """Normalize response format for consistency"""
    if not response.get("success"):
        # Add helpful context to errors
        error_msg = response.get("error", "Unknown error")
        return {
            "success": False,
            "error": error_msg,
            "operation": operation,
            "suggestion": _get_error_suggestion(operation, error_msg)
        }
    
    # Success response with normalized data
    return {
        "success": True,
        "operation": operation,
        "data": response.get("data", {}),
        "message": f"{operation} completed successfully"
    }


def _get_error_suggestion(operation: str, error: str) -> str:
    """Get helpful suggestion based on error"""
    suggestions = {
        "Cannot connect": "Make sure TradingView chart is running at localhost:3000 and API server at localhost:3001",
        "timeout": "Chart may be loading. Wait a few seconds and try again",
        "Invalid": "Check the parameter format and try again with valid values",
        "not found": "The requested resource doesn't exist. Verify the ID or name",
    }
    
    for key, suggestion in suggestions.items():
        if key.lower() in error.lower():
            return suggestion
    
    return "Check the error message and adjust parameters accordingly"


async def tv_get_state() -> Dict[str, Any]:
    """
    Get current chart state (symbol, timeframe, chart type, indicators)
    
    Returns:
        Chart state information with normalized format
    """
    logger.info("Getting chart state")
    client = get_client()
    response = await client.send_command("GET_STATE")
    
    result = _normalize_response(response, "GET_STATE")
    
    # Add helpful info to success response
    if result["success"] and result.get("data"):
        data = result["data"]
        result["summary"] = f"Chart showing {data.get('symbol', 'unknown')} on {data.get('timeframe', 'unknown')} timeframe"
        result["indicators_count"] = len(data.get("indicators", []))
    
    return result


async def tv_set_symbol(symbol: str) -> Dict[str, Any]:
    """
    Change chart symbol
    
    Args:
        symbol: Trading symbol (e.g., BTC, ETH, SOL)
        
    Returns:
        Success status with normalized format
    """
    # Validate input
    if not symbol or not isinstance(symbol, str):
        return {
            "success": False,
            "error": "Symbol must be a non-empty string",
            "operation": "SET_SYMBOL",
            "provided": symbol,
            "suggestion": "Provide a valid symbol like 'BTC', 'ETH', 'SOL', etc."
        }
    
    # Normalize symbol
    symbol = symbol.upper().strip()
    
    # Remove common suffixes if present
    symbol = re.sub(r'(USDT|USD|PERP)$', '', symbol)
    
    logger.info(f"Setting symbol to {symbol}")
    client = get_client()
    response = await client.send_command("SET_SYMBOL", {"symbol": symbol})
    
    result = _normalize_response(response, "SET_SYMBOL")
    if result["success"]:
        result["message"] = f"Chart symbol changed to {symbol}"
        result["symbol"] = symbol
    
    return result


async def tv_set_timeframe(timeframe: str) -> Dict[str, Any]:
    """
    Change chart timeframe
    
    Args:
        timeframe: Timeframe (1, 5, 15, 30, 60, 240, D, W, M)
        
    Returns:
        Success status with normalized format
    """
    # Normalize timeframe
    timeframe = str(timeframe).upper().strip()
    
    # Map common variations
    timeframe_map = {
        "1M": "1", "1MIN": "1",
        "5M": "5", "5MIN": "5",
        "15M": "15", "15MIN": "15",
        "30M": "30", "30MIN": "30",
        "1H": "60", "1HOUR": "60",
        "4H": "240", "4HOUR": "240",
        "1D": "D", "DAILY": "D", "DAY": "D",
        "1W": "W", "WEEKLY": "W", "WEEK": "W",
        "1M": "M", "MONTHLY": "M", "MONTH": "M",
    }
    
    timeframe = timeframe_map.get(timeframe, timeframe)
    
    # Validate timeframe
    valid_timeframes = ["1", "5", "15", "30", "60", "240", "D", "W", "M"]
    if timeframe not in valid_timeframes:
        return {
            "success": False,
            "error": f"Invalid timeframe: '{timeframe}'",
            "operation": "SET_TIMEFRAME",
            "provided": timeframe,
            "valid_options": valid_timeframes,
            "suggestion": "Use one of: 1 (1min), 5 (5min), 15 (15min), 30 (30min), 60 (1hour), 240 (4hour), D (daily), W (weekly), M (monthly)"
        }
    
    logger.info(f"Setting timeframe to {timeframe}")
    client = get_client()
    response = await client.send_command("SET_TIMEFRAME", {"timeframe": timeframe})
    
    result = _normalize_response(response, "SET_TIMEFRAME")
    if result["success"]:
        timeframe_labels = {
            "1": "1 minute", "5": "5 minutes", "15": "15 minutes",
            "30": "30 minutes", "60": "1 hour", "240": "4 hours",
            "D": "daily", "W": "weekly", "M": "monthly"
        }
        result["message"] = f"Chart timeframe changed to {timeframe_labels.get(timeframe, timeframe)}"
        result["timeframe"] = timeframe
    
    return result


async def tv_set_chart_type(chart_type: str) -> Dict[str, Any]:
    """
    Change chart type
    
    Args:
        chart_type: Chart type (Candles, Line, Area, HeikinAshi, Bars)
        
    Returns:
        Success status with normalized format
    """
    # Normalize chart type
    chart_type = chart_type.strip()
    
    # Map common variations
    type_map = {
        "candle": "Candles",
        "candlestick": "Candles",
        "bar": "Bars",
        "heikin": "HeikinAshi",
        "heikin ashi": "HeikinAshi",
        "ha": "HeikinAshi",
    }
    
    chart_type = type_map.get(chart_type.lower(), chart_type)
    
    # Validate chart type
    valid_types = ["Candles", "Line", "Area", "HeikinAshi", "Bars"]
    if chart_type not in valid_types:
        return {
            "success": False,
            "error": f"Invalid chart type: '{chart_type}'",
            "operation": "SET_CHART_TYPE",
            "provided": chart_type,
            "valid_options": valid_types,
            "suggestion": "Use one of: Candles (default), Line, Area, HeikinAshi, Bars"
        }
    
    logger.info(f"Setting chart type to {chart_type}")
    client = get_client()
    response = await client.send_command("SET_CHART_TYPE", {"chart_type": chart_type})
    
    result = _normalize_response(response, "SET_CHART_TYPE")
    if result["success"]:
        result["message"] = f"Chart type changed to {chart_type}"
        result["chart_type"] = chart_type
    
    return result


async def tv_scroll_to_date(date: str) -> Dict[str, Any]:
    """
    Scroll chart to specific date
    
    Args:
        date: ISO date string (e.g., "2024-01-15")
        
    Returns:
        Success status with normalized format
    """
    # Validate date format
    try:
        parsed_date = datetime.fromisoformat(date.replace('Z', '+00:00'))
        date = parsed_date.strftime("%Y-%m-%d")
    except ValueError:
        return {
            "success": False,
            "error": f"Invalid date format: '{date}'",
            "operation": "SCROLL_TO_DATE",
            "provided": date,
            "expected_format": "YYYY-MM-DD (e.g., '2024-01-15')",
            "suggestion": "Use ISO date format: YYYY-MM-DD"
        }
    
    logger.info(f"Scrolling to date {date}")
    client = get_client()
    response = await client.send_command("SCROLL_TO_DATE", {"date": date})
    
    result = _normalize_response(response, "SCROLL_TO_DATE")
    if result["success"]:
        result["message"] = f"Chart scrolled to {date}"
        result["date"] = date
    
    return result

