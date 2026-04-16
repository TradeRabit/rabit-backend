"""Drawing tools for TradingView"""
from typing import Dict, Any, Optional
from .client import get_client
from utils.logger import get_logger
from datetime import datetime
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
        "color": "Use hex color format like '#FD4C01' or '#FF0000'",
        "time": "Use ISO date format like '2024-01-15T10:30:00'",
    }
    
    for key, suggestion in suggestions.items():
        if key.lower() in error.lower():
            return suggestion
    
    return "Check the error message and adjust parameters accordingly"


def _validate_color(color: str) -> bool:
    """Validate hex color format"""
    return bool(re.match(r'^#[0-9A-Fa-f]{6}$', color))


def _validate_time(time_str: str) -> bool:
    """Validate ISO time format"""
    try:
        datetime.fromisoformat(time_str.replace('Z', '+00:00'))
        return True
    except ValueError:
        return False


async def tv_draw_line(
    price1: float,
    time1: str,
    price2: float,
    time2: str,
    color: str = "#FD4C01",
    width: int = 2
) -> Dict[str, Any]:
    """
    Draw trend line on chart
    
    Args:
        price1: Start price
        time1: Start time (ISO format)
        price2: End price
        time2: End time (ISO format)
        color: Line color (hex)
        width: Line width
        
    Returns:
        Success status with drawing ID
    """
    # Validate prices
    try:
        price1 = float(price1)
        price2 = float(price2)
    except (ValueError, TypeError):
        return {
            "success": False,
            "error": "Prices must be numeric values",
            "operation": "DRAW_LINE",
            "provided": {"price1": price1, "price2": price2},
            "suggestion": "Provide valid numeric prices, e.g., 95000.50"
        }
    
    # Validate times
    if not _validate_time(time1):
        return {
            "success": False,
            "error": f"Invalid time format for time1: '{time1}'",
            "operation": "DRAW_LINE",
            "provided": time1,
            "expected_format": "ISO format: YYYY-MM-DDTHH:MM:SS",
            "suggestion": "Use ISO time format like '2024-01-15T10:30:00'"
        }
    
    if not _validate_time(time2):
        return {
            "success": False,
            "error": f"Invalid time format for time2: '{time2}'",
            "operation": "DRAW_LINE",
            "provided": time2,
            "expected_format": "ISO format: YYYY-MM-DDTHH:MM:SS",
            "suggestion": "Use ISO time format like '2024-01-15T10:30:00'"
        }
    
    # Validate color
    if not _validate_color(color):
        return {
            "success": False,
            "error": f"Invalid color format: '{color}'",
            "operation": "DRAW_LINE",
            "provided": color,
            "expected_format": "Hex color: #RRGGBB",
            "suggestion": "Use hex color format like '#FD4C01' or '#FF0000'"
        }
    
    # Validate width
    if not isinstance(width, int) or width < 1 or width > 10:
        return {
            "success": False,
            "error": f"Width must be an integer between 1 and 10, got: {width}",
            "operation": "DRAW_LINE",
            "provided": width,
            "suggestion": "Use a width between 1 (thin) and 10 (thick)"
        }
    
    logger.info(f"Drawing trend line from ({time1}, {price1}) to ({time2}, {price2})")
    client = get_client()
    
    response = await client.send_command("DRAW_LINE", {
        "type": "trend_line",
        "point1": {"price": price1, "time": time1},
        "point2": {"price": price2, "time": time2},
        "color": color,
        "width": width
    })
    
    result = _normalize_response(response, "DRAW_LINE")
    
    if result["success"]:
        result["message"] = f"Drew trend line from {price1} to {price2}"
        if result.get("data", {}).get("drawing_id"):
            result["drawing_id"] = result["data"]["drawing_id"]
    
    return result


async def tv_draw_horizontal_line(
    price: float,
    color: str = "#FD4C01",
    width: int = 2,
    text: Optional[str] = None
) -> Dict[str, Any]:
    """
    Draw horizontal line at price level
    
    Args:
        price: Price level
        color: Line color (hex)
        width: Line width
        text: Optional label text
        
    Returns:
        Success status with drawing ID
    """
    # Validate price
    try:
        price = float(price)
    except (ValueError, TypeError):
        return {
            "success": False,
            "error": f"Price must be a numeric value, got: {type(price).__name__}",
            "operation": "DRAW_HORIZONTAL_LINE",
            "provided": price,
            "suggestion": "Provide a valid numeric price, e.g., 95000.50"
        }
    
    # Validate color
    if not _validate_color(color):
        return {
            "success": False,
            "error": f"Invalid color format: '{color}'",
            "operation": "DRAW_HORIZONTAL_LINE",
            "provided": color,
            "expected_format": "Hex color: #RRGGBB",
            "suggestion": "Use hex color format like '#FD4C01' or '#FF0000'"
        }
    
    # Validate width
    if not isinstance(width, int) or width < 1 or width > 10:
        return {
            "success": False,
            "error": f"Width must be an integer between 1 and 10, got: {width}",
            "operation": "DRAW_HORIZONTAL_LINE",
            "provided": width,
            "suggestion": "Use a width between 1 (thin) and 10 (thick)"
        }
    
    logger.info(f"Drawing horizontal line at {price}")
    client = get_client()
    
    params = {
        "type": "horizontal_line",
        "price": price,
        "color": color,
        "width": width
    }
    
    if text:
        params["text"] = str(text)
    
    response = await client.send_command("DRAW_HORIZONTAL_LINE", params)
    result = _normalize_response(response, "DRAW_HORIZONTAL_LINE")
    
    if result["success"]:
        result["message"] = f"Drew horizontal line at {price}"
        result["price"] = price
        if result.get("data", {}).get("drawing_id"):
            result["drawing_id"] = result["data"]["drawing_id"]
    
    return result


async def tv_clear_drawings() -> Dict[str, Any]:
    """
    Clear all drawings from chart
    
    Returns:
        Success status
    """
    logger.info("Clearing all drawings")
    client = get_client()
    
    response = await client.send_command("CLEAR_DRAWINGS")
    result = _normalize_response(response, "CLEAR_DRAWINGS")
    
    if result["success"]:
        result["message"] = "Cleared all drawings from chart"
    
    return result
