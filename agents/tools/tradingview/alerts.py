"""Alert management tools for TradingView"""
from typing import Dict, Any
from .client import get_client
from utils.logger import get_logger

logger = get_logger(__name__)


VALID_CONDITIONS = ["crossing", "greater_than", "less_than"]


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
        "not found": "Alert not found. Use tv_list_alerts() to see available alerts",
    }
    
    for key, suggestion in suggestions.items():
        if key.lower() in error.lower():
            return suggestion
    
    return "Check the error message and adjust parameters accordingly"


async def tv_create_alert(
    condition: str,
    price: float,
    message: str = ""
) -> Dict[str, Any]:
    """
    Create price alert
    
    Args:
        condition: Alert condition (crossing, greater_than, less_than)
        price: Price level
        message: Alert message
        
    Returns:
        Success status with alert ID
    """
    # Validate condition
    if condition not in VALID_CONDITIONS:
        return {
            "success": False,
            "error": f"Invalid condition: '{condition}'",
            "operation": "CREATE_ALERT",
            "provided": condition,
            "valid_options": VALID_CONDITIONS,
            "suggestion": f"Use one of: {', '.join(VALID_CONDITIONS)}"
        }
    
    # Validate price
    try:
        price = float(price)
    except (ValueError, TypeError):
        return {
            "success": False,
            "error": f"Price must be a numeric value, got: {type(price).__name__}",
            "operation": "CREATE_ALERT",
            "provided": price,
            "suggestion": "Provide a valid numeric price, e.g., 95000.50"
        }
    
    logger.info(f"Creating alert: {condition} {price}")
    client = get_client()
    
    response = await client.send_command("CREATE_ALERT", {
        "condition": condition,
        "price": price,
        "message": str(message) if message else ""
    })
    
    result = _normalize_response(response, "CREATE_ALERT")
    
    if result["success"]:
        result["message"] = f"Created {condition} alert at {price}"
        result["condition"] = condition
        result["price"] = price
        if result.get("data", {}).get("alert_id"):
            result["alert_id"] = result["data"]["alert_id"]
    
    return result


async def tv_list_alerts() -> Dict[str, Any]:
    """
    List all active alerts
    
    Returns:
        List of alerts
    """
    logger.info("Listing alerts")
    client = get_client()
    
    response = await client.send_command("LIST_ALERTS")
    result = _normalize_response(response, "LIST_ALERTS")
    
    if result["success"] and result.get("data"):
        alerts = result["data"].get("alerts", [])
        result["summary"] = f"Found {len(alerts)} active alerts"
        result["alerts_count"] = len(alerts)
    
    return result


async def tv_delete_alert(alert_id: str) -> Dict[str, Any]:
    """
    Delete alert by ID
    
    Args:
        alert_id: Alert ID to delete
        
    Returns:
        Success status
    """
    # Validate alert_id
    if not alert_id or not isinstance(alert_id, str):
        return {
            "success": False,
            "error": "Alert ID must be a non-empty string",
            "operation": "DELETE_ALERT",
            "provided": alert_id,
            "suggestion": "Get alert_id from tv_list_alerts() first"
        }
    
    logger.info(f"Deleting alert: {alert_id}")
    client = get_client()
    
    response = await client.send_command("DELETE_ALERT", {"alert_id": alert_id})
    result = _normalize_response(response, "DELETE_ALERT")
    
    if result["success"]:
        result["message"] = f"Deleted alert: {alert_id}"
        result["alert_id"] = alert_id
    
    return result
