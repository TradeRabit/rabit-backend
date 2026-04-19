"""Screenshot tool for TradingView."""
import base64
from typing import Dict, Any, Optional

import aiohttp

from .client import get_client
from agents.tools.core.runtime_context import get_current_event_emitter
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


async def _download_screenshot_asset(screenshot_url: str) -> Optional[Dict[str, Any]]:
    """Fetch a screenshot URL so the agent can receive the actual image block."""
    if not screenshot_url:
        return None

    timeout = aiohttp.ClientTimeout(total=10)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(screenshot_url) as response:
                if response.status != 200:
                    logger.warning(
                        "TradingView screenshot fetch returned status %s for %s",
                        response.status,
                        screenshot_url,
                    )
                    return None

                content_type = (response.headers.get("Content-Type") or "image/png").split(";")[0].strip()
                if not content_type.startswith("image/"):
                    logger.warning(
                        "TradingView screenshot fetch returned non-image content type %s for %s",
                        content_type,
                        screenshot_url,
                    )
                    return None

                payload = await response.read()
                if not payload:
                    return None

                return {
                    "content_type": content_type,
                    "data_base64": base64.b64encode(payload).decode("ascii"),
                    "size_bytes": len(payload),
                }
    except Exception as exc:
        logger.warning("Failed to fetch TradingView screenshot asset from %s: %s", screenshot_url, exc)
        return None


async def _emit_screenshot_event(payload: Dict[str, Any]) -> bool:
    """Emit a screenshot event to the current streaming consumer when available."""
    emitter = get_current_event_emitter()
    if emitter is None:
        return False

    await emitter("chart_screenshot", payload)
    return True


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
        screenshot_url = result.get("data", {}).get("screenshot_url")
        if screenshot_url:
            result["screenshot_url"] = screenshot_url
            agent_image = await _download_screenshot_asset(screenshot_url)
            if agent_image:
                result["data"]["agent_image"] = agent_image
                result["agent_image_available"] = True
            else:
                result["agent_image_available"] = False

            event_payload = {
                "type": "chart_screenshot",
                "region": region,
                "screenshot_url": screenshot_url,
                "agent_image_available": result["agent_image_available"],
            }
            result["streamed"] = await _emit_screenshot_event(event_payload)
        else:
            result["agent_image_available"] = False
            result["streamed"] = False
    
    return result
