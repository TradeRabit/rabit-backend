"""Composable agent graph execution primitives."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Dict, List, Optional

from agents.core.pipeline import AgentPipelineNodePlan


NodeHandler = Callable[
    ["AgentNodeExecutionContext", AgentPipelineNodePlan],
    Awaitable["AgentPipelineNodeResult"],
]


@dataclass
class AgentNodeExecutionContext:
    """Mutable context shared across pipeline nodes."""

    agent: Any
    user_input: str
    messages: List[Dict[str, Any]]
    system_prompt: str
    intent_context: Any
    market_context: Dict[str, Any]
    event_emitter: Optional[Callable[..., Awaitable[None]]] = None
    observations: Dict[str, Any] = field(default_factory=dict)
    tool_failure_count: int = 0
    call_tool: Optional[Callable[[str, Dict[str, Any]], Awaitable[Any]]] = None


@dataclass
class AgentPipelineNodeResult:
    """One node execution result."""

    status: str = "completed"
    summary: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    system_prompt_addition: str = ""
    appended_messages: List[Dict[str, Any]] = field(default_factory=list)


class AgentGraphExecutor:
    """Execute a planned sequence of pipeline nodes."""

    def __init__(self, node_handlers: Dict[str, NodeHandler]):
        self._node_handlers = dict(node_handlers)

    async def execute(
        self,
        *,
        plans: List[AgentPipelineNodePlan],
        context: AgentNodeExecutionContext,
    ) -> AgentNodeExecutionContext:
        """Run all planned nodes in order."""
        for plan in plans:
            handler = self._node_handlers.get(plan.name)
            if handler is None:
                plan.status = "skipped"
                if not plan.summary:
                    plan.summary = f"No runtime node registered for '{plan.name}'."
                continue

            if plan.instruction:
                context.system_prompt = (
                    f"{context.system_prompt}\n\n"
                    f"Pipeline node instruction ({plan.name}): {plan.instruction}"
                )
                context.observations.setdefault("_node_instructions", {})[plan.name] = plan.instruction

            result = await handler(context, plan)
            plan.status = result.status
            if result.summary:
                plan.summary = result.summary
            if result.metadata:
                plan.metadata.update(result.metadata)

            if result.system_prompt_addition:
                context.system_prompt = (
                    f"{context.system_prompt}\n\n{result.system_prompt_addition}"
                )

            if result.appended_messages:
                context.messages.extend(result.appended_messages)

            context.observations[plan.name] = {
                "status": result.status,
                "summary": result.summary,
                **result.metadata,
            }

        return context


def build_default_graph_executor() -> AgentGraphExecutor:
    """Build the default graph executor with currently supported nodes."""
    from agents.nodes.chart_analysis import run_chart_analysis_node
    from agents.nodes.clarification_prep import run_clarification_prep_node
    from agents.nodes.execution_snapshot import run_execution_snapshot_node
    from agents.nodes.general_fallback import run_general_fallback_node
    from agents.nodes.memory_snapshot import run_memory_snapshot_node
    from agents.nodes.market_snapshot import run_market_snapshot_node
    from agents.nodes.portfolio_snapshot import run_portfolio_snapshot_node
    from agents.nodes.research_snapshot import run_research_snapshot_node
    from agents.nodes.response_composer import run_response_composer_node

    return AgentGraphExecutor(
        {
            "clarification_prep": run_clarification_prep_node,
            "general_fallback": run_general_fallback_node,
            "chart_analysis": run_chart_analysis_node,
            "market_snapshot": run_market_snapshot_node,
            "research_snapshot": run_research_snapshot_node,
            "portfolio_snapshot": run_portfolio_snapshot_node,
            "execution_snapshot": run_execution_snapshot_node,
            "memory_snapshot": run_memory_snapshot_node,
            "response_composer": run_response_composer_node,
        }
    )
