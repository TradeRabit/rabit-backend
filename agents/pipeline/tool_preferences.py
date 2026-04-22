"""Frontend-controlled assist tool preferences."""
from typing import Any, Dict, Final, Optional, Set


DEFAULT_TOOL_PREFERENCES: Final[Dict[str, Any]] = {
    "web_search_enabled": True,
    "memory_enabled": True,
    "plan_enabled": True,
    "auto_execute_enabled": False,
}

WEB_SEARCH_TOOL_NAMES: Final[Set[str]] = {
    "web_search",
    "get_latest_news",
    "search_news_by_keywords",
    "get_trending_news",
    "search_news_by_symbols",
}

MEMORY_TOOL_NAMES: Final[Set[str]] = {
    "add_user_memory",
    "get_user_memory",
    "delete_user_memory",
    "clear_user_memories",
}

PLAN_TOOL_NAMES: Final[Set[str]] = {
    "show_plan",
}

AUTO_EXECUTE_TOOL_NAMES: Final[Set[str]] = {
}


def normalize_tool_preferences(config: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Normalize frontend tool-preference config."""
    payload = dict(DEFAULT_TOOL_PREFERENCES)
    if not config:
        return payload

    payload["web_search_enabled"] = bool(config.get("web_search_enabled", True))
    payload["memory_enabled"] = bool(config.get("memory_enabled", True))
    payload["plan_enabled"] = bool(config.get("plan_enabled", True))
    payload["auto_execute_enabled"] = bool(config.get("auto_execute_enabled", False))
    return payload


def get_blocked_tool_names(config: Optional[Dict[str, Any]]) -> Set[str]:
    """Return the tool names blocked by the current preferences."""
    normalized = normalize_tool_preferences(config)
    blocked: Set[str] = set()

    if not normalized["web_search_enabled"]:
        blocked.update(WEB_SEARCH_TOOL_NAMES)

    if not normalized["memory_enabled"]:
        blocked.update(MEMORY_TOOL_NAMES)

    if not normalized["plan_enabled"]:
        blocked.update(PLAN_TOOL_NAMES)

    if not normalized["auto_execute_enabled"]:
        blocked.update(AUTO_EXECUTE_TOOL_NAMES)

    return blocked


def get_tool_preferences_guidance(config: Optional[Dict[str, Any]]) -> str:
    """Return prompt guidance describing the selected frontend tool preferences."""
    normalized = normalize_tool_preferences(config)
    guidance = [
        (
            "Web search and live news tools are enabled."
            if normalized["web_search_enabled"]
            else "Web search and live news tools are disabled for this request. Do not search the web or fetch live headlines."
        ),
        (
            "Long-term memory is enabled."
            if normalized["memory_enabled"]
            else "Long-term memory is disabled for this request. Do not recall, create, or delete durable memory."
        ),
        (
            "Plan output is enabled. When the request has multiple meaningful steps, prefer structured planning."
            if normalized["plan_enabled"]
            else "Plan output is disabled for this request. Do not emit explicit frontend plan tooling unless the user clearly asks for it."
        ),
        (
            "Auto execution is enabled for this request. Live execution may only happen through dedicated execution tools and only when exchange policy allows it."
            if normalized["auto_execute_enabled"]
            else "Auto execution is disabled for this request. Discuss execution ideas safely, but do not place or cancel live orders."
        ),
    ]
    return " ".join(guidance)
