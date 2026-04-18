"""Runtime context shared by agent tools during one agent request."""
from typing import Any, Awaitable, Callable, Dict, Optional
from contextvars import ContextVar, Token

_current_user_id: ContextVar[Optional[str]] = ContextVar("current_user_id", default=None)
_current_event_emitter: ContextVar[
    Optional[Callable[[str, dict], Awaitable[None]]]
] = ContextVar("current_event_emitter", default=None)
_current_backpack_execution: ContextVar[Optional[Dict[str, Any]]] = ContextVar(
    "current_backpack_execution",
    default=None,
)
_current_drift_execution: ContextVar[Optional[Dict[str, Any]]] = ContextVar(
    "current_drift_execution",
    default=None,
)
_current_market_context: ContextVar[Optional[Dict[str, Any]]] = ContextVar(
    "current_market_context",
    default=None,
)


def set_current_user_id(user_id: Optional[str]) -> Token:
    """Set the current user ID for tool execution."""
    return _current_user_id.set(user_id)


def reset_current_user_id(token: Token) -> None:
    """Reset the current user ID after tool execution finishes."""
    _current_user_id.reset(token)


def get_current_user_id() -> Optional[str]:
    """Return the active user ID for the current request context."""
    return _current_user_id.get()


def set_current_event_emitter(
    emitter: Optional[Callable[[str, dict], Awaitable[None]]],
) -> Token:
    """Set the current event emitter for UI/event tools."""
    return _current_event_emitter.set(emitter)


def reset_current_event_emitter(token: Token) -> None:
    """Reset the current event emitter."""
    _current_event_emitter.reset(token)


def get_current_event_emitter() -> Optional[Callable[[str, dict], Awaitable[None]]]:
    """Return the active event emitter for the current request context."""
    return _current_event_emitter.get()


def set_current_backpack_execution(config: Optional[Dict[str, Any]]) -> Token:
    """Set the current Backpack execution config for tool execution."""
    return _current_backpack_execution.set(config)


def reset_current_backpack_execution(token: Token) -> None:
    """Reset the current Backpack execution config."""
    _current_backpack_execution.reset(token)


def get_current_backpack_execution() -> Optional[Dict[str, Any]]:
    """Return the active Backpack execution config for the current request context."""
    return _current_backpack_execution.get()


def set_current_drift_execution(config: Optional[Dict[str, Any]]) -> Token:
    """Set the current Drift execution config for tool execution."""
    return _current_drift_execution.set(config)


def reset_current_drift_execution(token: Token) -> None:
    """Reset the current Drift execution config."""
    _current_drift_execution.reset(token)


def get_current_drift_execution() -> Optional[Dict[str, Any]]:
    """Return the active Drift execution config for the current request context."""
    return _current_drift_execution.get()


def set_current_market_context(config: Optional[Dict[str, Any]]) -> Token:
    """Set the current frontend market context for tool execution."""
    return _current_market_context.set(config)


def reset_current_market_context(token: Token) -> None:
    """Reset the current frontend market context."""
    _current_market_context.reset(token)


def get_current_market_context() -> Optional[Dict[str, Any]]:
    """Return the active frontend market context for the current request context."""
    return _current_market_context.get()
