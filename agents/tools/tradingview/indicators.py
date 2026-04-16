"""Indicator management tools for TradingView"""
from typing import Dict, Any, Optional
from .client import get_client
from utils.logger import get_logger

logger = get_logger(__name__)


# Map common short names to full names
INDICATOR_MAP = {
    "RSI": "Relative Strength Index",
    "MACD": "MACD",
    "BB": "Bollinger Bands",
    "EMA": "Moving Average Exponential",
    "SMA": "Moving Average",
    "Volume": "Volume",
    "Stochastic": "Stochastic",
    "ATR": "Average True Range",
    "ADX": "Average Directional Index",
    "CCI": "Commodity Channel Index",
    "MFI": "Money Flow Index",
    "OBV": "On Balance Volume",
    "VWAP": "VWAP",
    "Ichimoku": "Ichimoku Cloud",
    "Parabolic SAR": "Parabolic SAR",
    "Williams %R": "Williams %R"
}


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
        "not found": "Indicator not found. Use common names like 'RSI', 'MACD', 'BB', or full names",
        "Invalid": "Check the parameter format and try again with valid values",
    }
    
    for key, suggestion in suggestions.items():
        if key.lower() in error.lower():
            return suggestion
    
    return "Check the error message and adjust parameters accordingly"


async def tv_add_indicator(indicator: str, inputs: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Add indicator to chart
    
    Args:
        indicator: Full indicator name (e.g., "Relative Strength Index", "MACD", "Bollinger Bands")
        inputs: Optional input overrides (e.g., {"length": 20})
        
    Returns:
        Success status with entity_id
    """
    # Validate indicator
    if not indicator or not isinstance(indicator, str):
        return {
            "success": False,
            "error": "Indicator name must be a non-empty string",
            "operation": "ADD_INDICATOR",
            "provided": indicator,
            "available_indicators": list(INDICATOR_MAP.keys()),
            "suggestion": f"Use one of the common indicators: {', '.join(list(INDICATOR_MAP.keys())[:5])}, etc."
        }
    
    # Use full name if short name provided
    full_indicator = INDICATOR_MAP.get(indicator.upper(), indicator)
    
    logger.info(f"Adding indicator: {full_indicator}")
    client = get_client()
    
    params = {"indicator": full_indicator}
    if inputs:
        if not isinstance(inputs, dict):
            return {
                "success": False,
                "error": f"Inputs must be a dictionary, got: {type(inputs).__name__}",
                "operation": "ADD_INDICATOR",
                "provided": inputs,
                "suggestion": "Provide inputs as a dictionary, e.g., {'length': 20, 'source': 'close'}"
            }
        params["inputs"] = inputs
    
    response = await client.send_command("ADD_INDICATOR", params)
    result = _normalize_response(response, "ADD_INDICATOR")
    
    # Add helpful info
    if result["success"]:
        result["message"] = f"Added indicator: {full_indicator}"
        result["indicator"] = full_indicator
        if result.get("data", {}).get("entity_id"):
            result["entity_id"] = result["data"]["entity_id"]
    
    return result


async def tv_remove_indicator(entity_id: str) -> Dict[str, Any]:
    """
    Remove indicator from chart
    
    Args:
        entity_id: Entity ID of indicator (from tv_get_state)
        
    Returns:
        Success status
    """
    # Validate entity_id
    if not entity_id or not isinstance(entity_id, str):
        return {
            "success": False,
            "error": "Entity ID must be a non-empty string",
            "operation": "REMOVE_INDICATOR",
            "provided": entity_id,
            "suggestion": "Get entity_id from tv_get_state() first, then use it to remove the indicator"
        }
    
    logger.info(f"Removing indicator: {entity_id}")
    client = get_client()
    
    response = await client.send_command("REMOVE_INDICATOR", {"entity_id": entity_id})
    result = _normalize_response(response, "REMOVE_INDICATOR")
    
    if result["success"]:
        result["message"] = f"Removed indicator: {entity_id}"
        result["entity_id"] = entity_id
    
    return result


async def tv_set_indicator_inputs(entity_id: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Change indicator input values
    
    Args:
        entity_id: Entity ID of indicator (from tv_get_state)
        inputs: Input overrides (e.g., {"length": 50, "source": "close"})
        
    Returns:
        Success status
    """
    # Validate entity_id
    if not entity_id or not isinstance(entity_id, str):
        return {
            "success": False,
            "error": "Entity ID must be a non-empty string",
            "operation": "SET_INDICATOR_INPUTS",
            "provided": entity_id,
            "suggestion": "Get entity_id from tv_get_state() first"
        }
    
    # Validate inputs
    if not inputs or not isinstance(inputs, dict):
        return {
            "success": False,
            "error": f"Inputs must be a non-empty dictionary, got: {type(inputs).__name__}",
            "operation": "SET_INDICATOR_INPUTS",
            "provided": inputs,
            "suggestion": "Provide inputs as a dictionary, e.g., {'length': 50, 'source': 'close'}"
        }
    
    logger.info(f"Setting indicator inputs for {entity_id}: {inputs}")
    client = get_client()
    
    response = await client.send_command("SET_INDICATOR_INPUTS", {
        "entity_id": entity_id,
        "inputs": inputs
    })
    
    result = _normalize_response(response, "SET_INDICATOR_INPUTS")
    
    if result["success"]:
        result["message"] = f"Updated indicator {entity_id} inputs"
        result["entity_id"] = entity_id
        result["inputs"] = inputs
    
    return result
