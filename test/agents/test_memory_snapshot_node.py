from types import SimpleNamespace

import pytest

from agents.core.graph_executor import AgentNodeExecutionContext
from agents.core.pipeline import AgentPipelineNodePlan
from agents.intent_router import AgentIntentContext
from agents.nodes.memory_snapshot import run_memory_snapshot_node


@pytest.mark.asyncio
async def test_memory_snapshot_recalls_relevant_memory():
    async def fake_tool(name, arguments):
        assert name == "get_user_memory"
        assert arguments["query"] == "Remember my preferences"
        return SimpleNamespace(success=True, data={"success": True, "results": [{"memory": "User prefers SOL"}]}, error=None)

    context = AgentNodeExecutionContext(
        agent=object(),
        user_input="Remember my preferences",
        messages=[],
        system_prompt="base prompt",
        intent_context=AgentIntentContext(intent="memory_lookup", confidence="high"),
        market_context={},
        call_tool=fake_tool,
    )
    plan = AgentPipelineNodePlan(name="memory_snapshot", config={"memory_limit": 5})

    result = await run_memory_snapshot_node(context, plan)

    assert result.status == "completed"
    assert result.metadata["memory_results"]["results"][0]["memory"] == "User prefers SOL"
    assert "Internal memory-snapshot node observations:" in result.system_prompt_addition
