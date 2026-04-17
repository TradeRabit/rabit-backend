"""Runtime context shared by agent tools during one agent request."""
from typing import Awaitable, Callable, Optional
from contextvars import ContextVar, Token

_current_user_id: ContextVar[Optional[str]] = ContextVar("current_user_id", default=None)
_current_event_emitter: ContextVar[
    Optional[Callable[[str, dict], Awaitable[None]]]
] = ContextVar("current_event_emitter", default=None)


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
