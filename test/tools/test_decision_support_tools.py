import asyncio
import sys
from types import SimpleNamespace

from agents.journal_debrief.database import TradeDebriefDatabase
from agents.journal_debrief.service import TradeDebriefService
from agents.tools import tool_registry
from agents.tools.core.runtime_context import (
    reset_current_market_context,
    reset_current_user_id,
    set_current_market_context,
    set_current_user_id,
)
from agents.tools.decision_support.decision_tools import (
    calculate_position_size,
    create_trade_debrief,
    scan_markets,
)
from agents.tools_registry.register_tools import register_trading_tools


def test_register_trading_tools_includes_decision_support_tools(monkeypatch):
    monkeypatch.setattr("agents.tools_registry.register_tools.register_tradingview_tools", lambda: None)
    monkeypatch.setattr("agents.tools_registry.register_tools.settings.WEB_SEARCH_ENABLED", False)
    monkeypatch.setattr("agents.tools_registry.register_tools.settings.MEMORY_TOOLS_ENABLED", False)

    register_trading_tools()
    registered = {tool.name for tool in tool_registry.list_tools()}

    assert "calculate_position_size" in registered
    assert "scan_markets" in registered
    assert "create_trade_debrief" in registered


def test_calculate_position_size_returns_deterministic_metrics():
    result = asyncio.run(
        calculate_position_size(
            entry_price=100.0,
            stop_price=95.0,
            account_equity=10_000.0,
            risk_percent=1.0,
            side="long",
            leverage=2.0,
            fee_bps=10.0,
        )
    )

    assert result["classification"] == "position_sizing"
    assert result["risk_amount"] == 100.0
    assert result["stop_distance"] == 5.0
    assert result["position_size_units"] == 20.0
    assert result["position_notional"] == 2000.0
    assert result["estimated_margin_required"] == 1000.0


class DummyCoinInfo:
    def __init__(self, name, categories):
        self.name = name
        self.categories = categories


class DummyMarketService:
    async def get_coin_info(self, symbol):
        data = {
            "SOL": DummyCoinInfo("Solana", ["Layer 1", "DeFi"]),
            "JUP": DummyCoinInfo("Jupiter", ["DeFi"]),
            "BTC": DummyCoinInfo("Bitcoin", ["Layer 1"]),
        }
        return data.get(symbol)


class DummyMarketHandler:
    def get_price(self, symbol):
        data = {
            "SOL": SimpleNamespace(
                price=150.0,
                change_24h=6.2,
                volume_24h=5_000_000.0,
                open_interest=2_000_000.0,
                funding_rate=0.0001,
            ),
            "JUP": SimpleNamespace(
                price=1.2,
                change_24h=3.1,
                volume_24h=7_500_000.0,
                open_interest=500_000.0,
                funding_rate=0.0002,
            ),
            "BTC": SimpleNamespace(
                price=80_000.0,
                change_24h=-1.5,
                volume_24h=20_000_000.0,
                open_interest=10_000_000.0,
                funding_rate=0.00005,
            ),
        }
        return data.get(symbol)


def test_scan_markets_uses_market_context_watchlist(monkeypatch):
    monkeypatch.setattr(
        "agents.tools.decision_support.decision_tools.get_market_service",
        lambda: DummyMarketService(),
    )
    monkeypatch.setitem(sys.modules, "main", SimpleNamespace(market_handler=DummyMarketHandler()))

    market_token = set_current_market_context({"watchlist_symbols": ["SOL", "JUP", "BTC"]})
    try:
        result = asyncio.run(
            scan_markets(
                category="DeFi",
                limit=2,
                sort_by="score",
                directional_bias="bullish",
                min_abs_change_24h=2.0,
            )
        )
    finally:
        reset_current_market_context(market_token)

    assert result["classification"] == "market_scan"
    assert result["matched"] == 2
    assert result["assets"][0]["symbol"] == "SOL"
    assert result["assets"][1]["symbol"] == "JUP"
    assert result["assets"][0]["rank"] == 1


def test_create_trade_debrief_persists_structured_entry(tmp_path, monkeypatch):
    service = TradeDebriefService(
        db=TradeDebriefDatabase(str(tmp_path / "trade_debriefs.json"))
    )
    monkeypatch.setattr(
        "agents.tools.decision_support.decision_tools.get_trade_debrief_service",
        lambda: service,
    )

    user_token = set_current_user_id("wallet:test-user")
    try:
        result = asyncio.run(
            create_trade_debrief(
                summary="Late breakout entry with weak RR.",
                exchange="drift",
                symbol="SOL-PERP",
                side="long",
                entry_price=150.0,
                exit_price=145.0,
                tags_csv="late_entry, oversized",
                lesson="Wait for retest before sizing up.",
            )
        )
    finally:
        reset_current_user_id(user_token)

    assert result["classification"] == "journal_debrief"
    assert result["entry"]["user_id"] == "wallet:test-user"
    assert result["entry"]["exchange"] == "drift"
    assert result["entry"]["symbol"] == "SOL-PERP"
    assert result["entry"]["outcome"] == "loss"
    assert result["entry"]["tags"] == ["late_entry", "oversized"]
    assert result["recent_entry_count"] == 1
