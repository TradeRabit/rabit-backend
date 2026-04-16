"""Screenshot tool for TradingView"""
from typing import Dict, Any
from .client import get_client
from utils.logger import get_logger

logger = get_logger(__name__)


VALID_REGIONS = ["full", "chart", "indicators"]


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
    }
    
    for key, suggestion in suggestions.items():
        if key.lower() in error.lower():
            return suggestion
    
    return "Check the error message and adjust parameters accordingly"


async def tv_capture_screenshot(region: str = "chart") -> Dict[str, Any]:
    """
    Capture chart screenshot
    
    Args:
        region: Screenshot region (full, chart, indicators)
        
    Returns:
        Success status with screenshot path/URL
    """
    # Validate region
    if region not in VALID_REGIONS:
        return {
            "success": False,
            "error": f"Invalid region: '{region}'",
            "operation": "CAPTURE_SCREENSHOT",
            "provided": region,
            "valid_options": VALID_REGIONS,
            "suggestion": f"Use one of: {', '.join(VALID_REGIONS)}"
        }
    
    logger.info(f"Capturing screenshot: {region}")
    client = get_client()
    
    response = await client.send_command("CAPTURE_SCREENSHOT", {"region": region})
    result = _normalize_response(response, "CAPTURE_SCREENSHOT")
    
    if result["success"]:
        result["message"] = f"Captured {region} screenshot"
        result["region"] = region
        if result.get("data", {}).get("screenshot_url"):
            result["screenshot_url"] = result["data"]["screenshot_url"]
    
    return result
