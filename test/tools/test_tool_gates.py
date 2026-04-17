import asyncio

from agents.tools import tool_registry
from agents.tools.core.runtime_context import reset_current_user_id, set_current_user_id
from agents.tools.market.web_search import web_search
from agents.tools.memory.mem0_tools import add_user_memory
from agents.tools_registry.register_tools import register_trading_tools


def test_register_trading_tools_respects_web_search_and_memory_gates(monkeypatch):
    monkeypatch.setattr("agents.tools_registry.register_tools.register_tradingview_tools", lambda: None)
    monkeypatch.setattr("agents.tools_registry.register_tools.settings.WEB_SEARCH_ENABLED", False)
    monkeypatch.setattr("agents.tools_registry.register_tools.settings.MEMORY_TOOLS_ENABLED", False)

    register_trading_tools()
    registered = {tool.name for tool in tool_registry.list_tools()}

    assert "get_price" in registered
    assert "web_search" not in registered
    assert "add_user_memory" not in registered
    assert "get_user_memory" not in registered
    assert "delete_user_memory" not in registered
    assert "clear_user_memories" not in registered


def test_web_search_returns_disabled_when_gate_is_closed(monkeypatch):
    monkeypatch.setattr("agents.tools.market.web_search.settings.WEB_SEARCH_ENABLED", False)
    monkeypatch.setattr("agents.tools.market.web_search._web_search_client", None)

    result = web_search("BTC", max_results=1)

    assert result["success"] is False
    assert "disabled by configuration" in result["error"]


def test_memory_tools_raise_when_gate_is_closed(monkeypatch):
    monkeypatch.setattr("agents.tools.memory.mem0_tools.settings.MEMORY_TOOLS_ENABLED", False)

    token = set_current_user_id("user-1")
    try:
        try:
            asyncio.run(add_user_memory("remember this"))
        except ValueError as exc:
            assert "disabled by configuration" in str(exc)
        else:
            raise AssertionError("Expected memory tool gate to block add_user_memory")
    finally:
        reset_current_user_id(token)
