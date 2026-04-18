from types import SimpleNamespace

from agents.openrouter.session_costs import (
    OpenRouterSessionCostDatabase,
    OpenRouterSessionCostService,
)


def test_openrouter_session_cost_service_accumulates_scope_usage(tmp_path):
    db = OpenRouterSessionCostDatabase(str(tmp_path / "openrouter_session_costs.json"))
    service = OpenRouterSessionCostService(db=db)
    service.models_db = SimpleNamespace(
        get_model=lambda model_id: SimpleNamespace(input_price=3.0, output_price=15.0)
    )

    service.record_usage(
        scope_id="chat-123",
        user_id="wallet:user-1",
        model_id="anthropic/claude-3.5-sonnet",
        usage={"input_tokens": 2_000, "output_tokens": 500},
        phase="intent_router",
    )
    service.record_usage(
        scope_id="chat-123",
        user_id="wallet:user-1",
        model_id="anthropic/claude-3.5-sonnet",
        usage={"input_tokens": 10_000, "output_tokens": 1_000},
        phase="response",
    )

    summary = service.get_scope_summary(scope_id="chat-123")

    assert summary is not None
    assert summary["scope_id"] == "chat-123"
    assert summary["user_id"] == "wallet:user-1"
    assert summary["total_calls"] == 2
    assert summary["total_input_tokens"] == 12_000
    assert summary["total_output_tokens"] == 1_500
    assert summary["total_tokens"] == 13_500
    assert summary["estimated_cost_usd"] == 0.0585
    assert summary["model_ids"] == ["anthropic/claude-3.5-sonnet"]
    assert [phase["phase"] for phase in summary["phases"]] == ["intent_router", "response"]
    assert summary["phases"][0]["calls"] == 1
    assert summary["phases"][1]["calls"] == 1
