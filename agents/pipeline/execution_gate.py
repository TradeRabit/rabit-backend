"""Generic live-execution gate for Phantom-first runtime flows."""
from typing import Any, Dict, Optional


DEFAULT_EXECUTION_GATE: Dict[str, Any] = {
    "enabled": False,
    "exchange": "phantom",
    "market_type": "auto",
}


def normalize_execution_gate(config: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Normalize one generic execution gate payload."""
    payload = dict(DEFAULT_EXECUTION_GATE)
    if not config:
        return payload

    exchange = str(config.get("exchange") or "phantom").strip().lower() or "phantom"
    market_type = str(config.get("market_type") or "auto").strip().lower() or "auto"

    payload["enabled"] = bool(config.get("enabled", False))
    payload["exchange"] = exchange
    payload["market_type"] = market_type
    return payload


def merge_legacy_execution_gates(execution_gate: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Normalize the current Phantom-first execution gate payload."""
    return normalize_execution_gate(execution_gate)


def get_execution_gate_guidance(config: Optional[Dict[str, Any]]) -> str:
    """Return prompt guidance for the current execution gate."""
    normalized = normalize_execution_gate(config)
    if normalized["enabled"]:
        return (
            f"Live execution gate is enabled for {normalized['exchange']} "
            f"with market_type={normalized['market_type']}. "
            "Only discuss live execution paths when dedicated execution tooling exists and policy allows it."
        )
    return (
        "Live execution gate is disabled for this request. "
        "You may discuss trade ideas and planning, but do not imply that live orders can be placed right now."
    )
