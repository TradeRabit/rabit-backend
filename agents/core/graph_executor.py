"""Composable agent graph execution primitives."""
from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Dict, List, Optional

from agents.pipeline.pipeline import AgentPipelineNodePlan
from config.settings import settings


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
    scope_id: Optional[str] = None
    user_id: Optional[str] = None
    event_emitter: Optional[Callable[..., Awaitable[None]]] = None
    observations: Dict[str, Any] = field(default_factory=dict)
    tool_failure_count: int = 0
    call_tool: Optional[Callable[[str, Dict[str, Any]], Awaitable[Any]]] = None
    persist_artifact: Optional[Callable[..., Optional[Dict[str, Any]]]] = None


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

    def _resolve_symbol_from_context(self, context: AgentNodeExecutionContext) -> Optional[str]:
        """Resolve one symbol from prior observations, market context, or request text."""
        chart_observation = context.observations.get("chart_analysis", {})
        for key in ("effective_symbol", "requested_symbol", "resolved_symbol"):
            value = str(chart_observation.get(key) or "").strip().upper()
            if value:
                return value

        market_symbol = str((context.market_context or {}).get("symbol") or "").strip().upper()
        if market_symbol:
            return market_symbol

        text = (context.user_input or "").upper()
        for symbol in [item.strip().upper() for item in settings.TRADING_ASSETS if item.strip()]:
            if re.search(rf"\b{re.escape(symbol)}\b", text):
                return symbol
        return None

    def _preflight_plan(
        self,
        *,
        plan: AgentPipelineNodePlan,
        context: AgentNodeExecutionContext,
    ) -> Optional[AgentPipelineNodeResult]:
        """Return a skip result when node dependencies are not satisfied."""
        if plan.depends_on:
            missing_dependencies = [
                name
                for name in plan.depends_on
                if name not in context.observations
                or str((context.observations.get(name) or {}).get("status") or "") in {"skipped", "failed"}
            ]
            if missing_dependencies:
                return AgentPipelineNodeResult(
                    status="skipped",
                    summary=f"Skipped {plan.name} because dependencies were unavailable.",
                    metadata={
                        "dependency_reason": "missing_dependencies",
                        "missing_dependencies": missing_dependencies,
                        "retryable": False,
                    },
                )

        required_observation_nodes = list(plan.config.get("requires_observation_nodes", []))
        if required_observation_nodes:
            available = [
                name
                for name in required_observation_nodes
                if name in context.observations
                and str((context.observations.get(name) or {}).get("status") or "") not in {"skipped", "failed"}
            ]
            if not available:
                return AgentPipelineNodeResult(
                    status="skipped",
                    summary=f"Skipped {plan.name} because no upstream observations were available.",
                    metadata={
                        "dependency_reason": "no_upstream_observations",
                        "required_observation_nodes": required_observation_nodes,
                        "retryable": False,
                    },
                )

        if plan.config.get("requires_symbol_resolution") and not self._resolve_symbol_from_context(context):
            return AgentPipelineNodeResult(
                status="skipped",
                summary=f"Skipped {plan.name} because no asset symbol could be resolved.",
                metadata={
                    "dependency_reason": "missing_symbol",
                    "retryable": False,
                },
            )

        return None

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
                context.observations[plan.name] = {
                    "status": plan.status,
                    "summary": plan.summary,
                    "retryable": False,
                }
                continue

            preflight_result = self._preflight_plan(plan=plan, context=context)
            if preflight_result is not None:
                plan.status = preflight_result.status
                plan.summary = preflight_result.summary or plan.summary
                if preflight_result.metadata:
                    plan.metadata.update(preflight_result.metadata)
                context.observations[plan.name] = {
                    "status": preflight_result.status,
                    "summary": preflight_result.summary,
                    **preflight_result.metadata,
                }
                continue

            if plan.instruction:
                context.system_prompt = (
                    f"{context.system_prompt}\n\n"
                    f"Pipeline node instruction ({plan.name}): {plan.instruction}"
                )
                context.observations.setdefault("_node_instructions", {})[plan.name] = plan.instruction

            max_attempts = 1 + max(0, int(plan.retry_attempts or 0))
            attempt_count = 0
            retry_count = 0
            retry_delays: List[float] = []
            result: Optional[AgentPipelineNodeResult] = None

            while attempt_count < max_attempts:
                attempt_count += 1
                result = await handler(context, plan)
                retryable = bool(result.metadata.get("retryable", result.status in {"degraded", "failed"}))
                should_retry = (
                    attempt_count < max_attempts
                    and retryable
                    and result.status in set(plan.retry_on_statuses or [])
                )
                if not should_retry:
                    break

                retry_count += 1
                delay = max(0.0, float(plan.retry_backoff_seconds or 0.0)) * retry_count
                retry_delays.append(delay)
                if delay:
                    await asyncio.sleep(delay)

            assert result is not None
            plan.status = result.status
            if result.summary:
                plan.summary = result.summary
            normalized_metadata = dict(result.metadata or {})
            normalized_metadata.update(
                {
                    "attempt_count": attempt_count,
                    "retry_count": retry_count,
                    "retry_delays": retry_delays,
                }
            )
            if result.metadata:
                plan.metadata.update(normalized_metadata)
            else:
                plan.metadata.update(normalized_metadata)

            if result.system_prompt_addition:
                context.system_prompt = (
                    f"{context.system_prompt}\n\n{result.system_prompt_addition}"
                )

            if result.appended_messages:
                context.messages.extend(result.appended_messages)

            context.observations[plan.name] = {
                "status": result.status,
                "summary": result.summary,
                **normalized_metadata,
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
    from agents.nodes.risk_review import run_risk_review_node
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
            "risk_review": run_risk_review_node,
            "response_composer": run_response_composer_node,
        }
    )
