from types import SimpleNamespace

import pytest

from agents.core.graph_executor import AgentNodeExecutionContext
from agents.pipeline.pipeline import AgentPipelineNodePlan
from agents.pipeline.intent_router import AgentIntentContext
from agents.nodes.execution_snapshot import run_execution_snapshot_node


class DummyAgent:
    last_backpack_execution = {"enabled": True, "exchange": "backpack"}
    last_drift_execution = {"enabled": False, "exchange": "drift"}


class DisabledExecutionAgent:
    last_backpack_execution = {"enabled": False, "exchange": "backpack"}
    last_drift_execution = {"enabled": False, "exchange": "drift"}


@pytest.mark.asyncio
async def test_execution_snapshot_collects_readiness_and_open_orders():
    calls = []

    async def fake_tool(name, arguments):
        calls.append(name)
        return SimpleNamespace(success=True, data={"success": True, "tool": name}, error=None)

    context = AgentNodeExecutionContext(
        agent=DummyAgent(),
        user_input="Check execution readiness",
        messages=[],
        system_prompt="base prompt",
        intent_context=AgentIntentContext(intent="broker_execution", confidence="high"),
        market_context={},
        call_tool=fake_tool,
    )
    plan = AgentPipelineNodePlan(name="execution_snapshot", config={})

    result = await run_execution_snapshot_node(context, plan)

    assert result.status == "completed"
    assert result.metadata["execution_sections"]["backpack_execution"]["enabled"] is True
    assert "backpack_get_open_orders" in result.metadata["execution_sections"]
    assert "drift_get_open_orders" in result.metadata["execution_sections"]
    assert result.metadata["execution_gate_enabled"] is True
    assert "Internal execution-snapshot node observations:" in result.system_prompt_addition


@pytest.mark.asyncio
async def test_execution_snapshot_marks_disabled_gate_context():
    async def fake_tool(name, arguments):
        return SimpleNamespace(success=False, data={}, error=f"{name} unavailable")

    context = AgentNodeExecutionContext(
        agent=DisabledExecutionAgent(),
        user_input="Check execution readiness",
        messages=[],
        system_prompt="base prompt",
        intent_context=AgentIntentContext(intent="broker_execution", confidence="high"),
        market_context={},
        call_tool=fake_tool,
    )
    plan = AgentPipelineNodePlan(name="execution_snapshot", config={"execution_gate_enabled_preplan": False})

    result = await run_execution_snapshot_node(context, plan)

    assert result.status == "degraded"
    assert result.metadata["execution_gate_enabled"] is False
    assert result.metadata["retryable"] is True


@pytest.mark.asyncio
async def test_execution_snapshot_records_partial_success_when_one_tool_path_fails():
    async def fake_tool(name, arguments):
        if name == "backpack_get_open_orders":
            return SimpleNamespace(success=True, data={"success": True, "orders": []}, error=None)
        return SimpleNamespace(success=False, data={}, error="drift unavailable")

    context = AgentNodeExecutionContext(
        agent=DummyAgent(),
        user_input="Check execution readiness",
        messages=[],
        system_prompt="base prompt",
        intent_context=AgentIntentContext(intent="broker_execution", confidence="high"),
        market_context={},
        call_tool=fake_tool,
    )
    plan = AgentPipelineNodePlan(name="execution_snapshot", config={})

    result = await run_execution_snapshot_node(context, plan)

    assert result.status == "degraded"
    assert result.metadata["execution_gate_enabled"] is True
    assert "backpack_get_open_orders" in result.metadata["execution_sections"]
    assert result.metadata["retryable"] is True
