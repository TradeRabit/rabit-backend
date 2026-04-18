"""Normalize and describe Backpack execution policy for one agent request."""
from typing import Any, Dict, Optional

from config.settings import settings

DEFAULT_BACKPACK_EXECUTION: Dict[str, Any] = {
    "enabled": False,
    "exchange": "backpack",
}


def normalize_backpack_execution(config: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Normalize frontend Backpack execution config."""
    payload = dict(DEFAULT_BACKPACK_EXECUTION)
    if not config:
        return payload

    payload["enabled"] = bool(config.get("enabled", False))
    exchange = str(config.get("exchange", "backpack") or "backpack").strip().lower()
    payload["exchange"] = exchange or "backpack"
    return payload


def is_backpack_execution_allowed(config: Optional[Dict[str, Any]]) -> bool:
    """Return whether live Backpack execution is allowed for this request."""
    normalized = normalize_backpack_execution(config)
    return settings.BACKPACK_EXECUTION_ENABLED and normalized["enabled"]


def get_backpack_execution_guidance(config: Optional[Dict[str, Any]]) -> str:
    """Return runtime prompt guidance for Backpack execution safety."""
    normalized = normalize_backpack_execution(config)

    if not settings.BACKPACK_EXECUTION_ENABLED:
        return (
            "Backpack live trade execution is globally disabled by backend configuration. "
            "Do not place, cancel, or modify live Backpack orders."
        )

    if not normalized["enabled"]:
        return (
            "Backpack live trade execution is disabled for this request. "
            "You may discuss execution plans, but do not place, cancel, or modify live Backpack orders."
        )

    return (
        "Backpack live trade execution is enabled for this request. "
        "Only perform live Backpack execution through dedicated execution tools when they are available, "
        "and never pretend an order was placed if no execution tool actually ran."
    )
