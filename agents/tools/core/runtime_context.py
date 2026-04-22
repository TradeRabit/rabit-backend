"""Runtime context shared by agent tools during one agent request."""
from typing import Any, Awaitable, Callable, Dict, Optional
from contextvars import ContextVar, Token

_current_user_id: ContextVar[Optional[str]] = ContextVar("current_user_id", default=None)
_current_scope_id: ContextVar[Optional[str]] = ContextVar("current_scope_id", default=None)
_current_event_emitter: ContextVar[
    Optional[Callable[[str, dict], Awaitable[None]]]
] = ContextVar("current_event_emitter", default=None)
_current_execution_gate: ContextVar[Optional[Dict[str, Any]]] = ContextVar(
    "current_execution_gate",
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


def set_current_scope_id(scope_id: Optional[str]) -> Token:
    """Set the current scope ID for tool execution."""
    return _current_scope_id.set(scope_id)


def reset_current_scope_id(token: Token) -> None:
    """Reset the current scope ID after tool execution finishes."""
    _current_scope_id.reset(token)


def get_current_scope_id() -> Optional[str]:
    """Return the active scope ID for the current request context."""
    return _current_scope_id.get()


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


def set_current_execution_gate(config: Optional[Dict[str, Any]]) -> Token:
    """Set the current generic execution gate for tool execution."""
    return _current_execution_gate.set(config)


def reset_current_execution_gate(token: Token) -> None:
    """Reset the current generic execution gate."""
    _current_execution_gate.reset(token)


def get_current_execution_gate() -> Optional[Dict[str, Any]]:
    """Return the active generic execution gate for the current request context."""
    return _current_execution_gate.get()


def set_current_market_context(config: Optional[Dict[str, Any]]) -> Token:
    """Set the current frontend market context for tool execution."""
    return _current_market_context.set(config)


def reset_current_market_context(token: Token) -> None:
    """Reset the current frontend market context."""
    _current_market_context.reset(token)


def get_current_market_context() -> Optional[Dict[str, Any]]:
    """Return the active frontend market context for the current request context."""
    return _current_market_context.get()
