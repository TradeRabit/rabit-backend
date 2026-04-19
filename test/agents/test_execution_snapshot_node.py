from types import SimpleNamespace

import pytest

from agents.core.graph_executor import AgentNodeExecutionContext
from agents.core.pipeline import AgentPipelineNodePlan
from agents.intent_router import AgentIntentContext
from agents.nodes.execution_snapshot import run_execution_snapshot_node


class DummyAgent:
    last_backpack_execution = {"enabled": True, "exchange": "backpack"}
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
    assert "Internal execution-snapshot node observations:" in result.system_prompt_addition
