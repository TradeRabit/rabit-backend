"""Normalize and describe Drift execution policy for one agent request."""
from typing import Any, Dict, Optional

from config.settings import settings

DEFAULT_DRIFT_EXECUTION: Dict[str, Any] = {
    "enabled": False,
    "exchange": "drift",
}


def normalize_drift_execution(config: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Normalize frontend Drift execution config."""
    payload = dict(DEFAULT_DRIFT_EXECUTION)
    if not config:
        return payload

    payload["enabled"] = bool(config.get("enabled", False))
    exchange = str(config.get("exchange", "drift") or "drift").strip().lower()
    payload["exchange"] = exchange or "drift"
    return payload


def is_drift_execution_allowed(config: Optional[Dict[str, Any]]) -> bool:
    """Return whether live Drift execution is allowed for this request."""
    normalized = normalize_drift_execution(config)
    return settings.DRIFT_EXECUTION_ENABLED and normalized["enabled"]


def get_drift_execution_guidance(config: Optional[Dict[str, Any]]) -> str:
    """Return runtime prompt guidance for Drift execution safety."""
    normalized = normalize_drift_execution(config)

    if not settings.DRIFT_EXECUTION_ENABLED:
        return (
            "Drift live trade execution is globally disabled by backend configuration. "
            "Do not place, cancel, or modify live Drift orders."
        )

    if not normalized["enabled"]:
        return (
            "Drift live trade execution is disabled for this request. "
            "You may discuss execution plans, but do not place, cancel, or modify live Drift orders."
        )

    return (
        "Drift live trade execution is enabled for this request. "
        "Only perform live Drift execution through dedicated execution tools when they are available, "
        "and never pretend an order was placed if no execution tool actually ran."
    )
