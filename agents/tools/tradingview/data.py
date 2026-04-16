"""Data reading tools for TradingView"""
from typing import Dict, Any, Optional
from .client import get_client
from utils.logger import get_logger
import re

logger = get_logger(__name__)


def _normalize_response(response: Dict[str, Any], operation: str) -> Dict[str, Any]:
    """Normalize response format for consistency"""
    if not response.get("success"):
        error_msg = response.get("error", "Unknown error")
        return {
            "success": False,
            "error": error_msg,
            "operation": operation,
            "suggestion": _get_error_suggestion(operation, error_msg)
        }
    
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
        "not found": "The requested resource doesn't exist. Verify the symbol or indicator name",
    }
    
    for key, suggestion in suggestions.items():
        if key.lower() in error.lower():
            return suggestion
    
    return "Check the error message and adjust parameters accordingly"


async def tv_get_quote(symbol: Optional[str] = None) -> Dict[str, Any]:
    """
    Get real-time quote data (price, OHLC, volume)
    
    Args:
        symbol: Symbol to quote (optional, uses current chart symbol if not provided)
        
    Returns:
        Quote data with price, OHLC, volume
    """
    # Validate and normalize symbol
    if symbol:
        if not isinstance(symbol, str) or not symbol.strip():
            return {
                "success": False,
                "error": "Symbol must be a non-empty string",
                "operation": "GET_QUOTE",
                "provided": symbol,
                "suggestion": "Provide a valid symbol like 'BTC', 'ETH', 'SOL', etc."
            }
        symbol = symbol.upper().strip()
        # Remove common suffixes
        symbol = re.sub(r'(USDT|USD|PERP)$', '', symbol)
    
    logger.info(f"Getting quote for {symbol or 'current symbol'}")
    client = get_client()
    
    params = {}
    if symbol:
        params["symbol"] = symbol
    
    response = await client.send_command("GET_QUOTE", params)
    result = _normalize_response(response, "GET_QUOTE")
    
    # Add helpful summary
    if result["success"] and result.get("data"):
        data = result["data"]
        price = data.get("price", "N/A")
        result["summary"] = f"Quote for {data.get('symbol', 'unknown')}: ${price}"
    
    return result


async def tv_get_ohlcv(count: int = 100, summary: bool = True) -> Dict[str, Any]:
    """
    Get OHLCV candlestick data
    
    Args:
        count: Number of bars to retrieve (max 500, default 100)
        summary: Return summary stats instead of all bars (saves context)
        
    Returns:
        OHLCV data or summary statistics
    """
    # Validate count
    if not isinstance(count, int):
        try:
            count = int(count)
        except (ValueError, TypeError):
            return {
                "success": False,
                "error": f"Count must be an integer, got: {type(count).__name__}",
                "operation": "GET_OHLCV",
                "provided": count,
                "suggestion": "Provide an integer between 1 and 500"
            }
    
    if count > 500:
        logger.warning(f"Count {count} exceeds maximum 500, clamping to 500")
        count = 500
    if count < 1:
        logger.warning(f"Count {count} is less than 1, clamping to 1")
        count = 1
    
    logger.info(f"Getting OHLCV data (count={count}, summary={summary})")
    client = get_client()
    
    response = await client.send_command("GET_OHLCV", {
        "count": count,
        "summary": summary
    })
    
    result = _normalize_response(response, "GET_OHLCV")
    
    # Add helpful summary
    if result["success"] and result.get("data"):
        data = result["data"]
        if summary:
            result["summary"] = f"Retrieved {count} bars summary: High={data.get('high')}, Low={data.get('low')}"
        else:
            bars = data.get("bars", [])
            result["summary"] = f"Retrieved {len(bars)} OHLCV bars"
    
    return result


async def tv_get_indicator_values() -> Dict[str, Any]:
    """
    Get current values from all visible indicators
    
    Returns:
        Dictionary of indicator values (RSI, MACD, BB, EMA, etc.)
    """
    logger.info("Getting indicator values")
    client = get_client()
    
    response = await client.send_command("GET_INDICATOR_VALUES")
    result = _normalize_response(response, "GET_INDICATOR_VALUES")
    
    # Add helpful summary
    if result["success"] and result.get("data"):
        indicators = result["data"]
        result["summary"] = f"Retrieved values for {len(indicators)} indicators"
        result["indicators_list"] = list(indicators.keys())
    
    return result
