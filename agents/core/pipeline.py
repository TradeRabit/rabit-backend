"""Agent pipeline trace models and dispatch planning."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from agents.intent_router import AgentIntentContext


SPECIALIST_TARGET_MARKET = "market_specialist"
SPECIALIST_TARGET_EXECUTION = "execution_specialist"
SPECIALIST_TARGET_PORTFOLIO = "portfolio_specialist"
SPECIALIST_TARGET_MEMORY = "memory_specialist"
SPECIALIST_TARGET_RESEARCH = "research_specialist"
SPECIALIST_TARGET_GENERAL = "general_specialist"
SPECIALIST_TARGET_CLARIFICATION = "clarification_gate"
PIPELINE_NODE_CLARIFICATION_PREP = "clarification_prep"
PIPELINE_NODE_GENERAL_FALLBACK = "general_fallback"
PIPELINE_NODE_CHART_ANALYSIS = "chart_analysis"
PIPELINE_NODE_MARKET_SNAPSHOT = "market_snapshot"
PIPELINE_NODE_RESEARCH_SNAPSHOT = "research_snapshot"
PIPELINE_NODE_PORTFOLIO_SNAPSHOT = "portfolio_snapshot"
PIPELINE_NODE_EXECUTION_SNAPSHOT = "execution_snapshot"
PIPELINE_NODE_MEMORY_SNAPSHOT = "memory_snapshot"
PIPELINE_NODE_RESPONSE_COMPOSER = "response_composer"


INTENT_TO_SPECIALIST_TARGET = {
    "market_analysis": SPECIALIST_TARGET_MARKET,
    "trade_setup": SPECIALIST_TARGET_MARKET,
    "position_management": SPECIALIST_TARGET_PORTFOLIO,
    "portfolio_review": SPECIALIST_TARGET_PORTFOLIO,
    "market_scan": SPECIALIST_TARGET_MARKET,
    "news_impact": SPECIALIST_TARGET_RESEARCH,
    "position_sizing": SPECIALIST_TARGET_PORTFOLIO,
    "broker_execution": SPECIALIST_TARGET_EXECUTION,
    "trade_review": SPECIALIST_TARGET_MEMORY,
    "macro_context": SPECIALIST_TARGET_RESEARCH,
    "regulatory_check": SPECIALIST_TARGET_RESEARCH,
    "preference_update": SPECIALIST_TARGET_MEMORY,
    "context_reset": SPECIALIST_TARGET_MEMORY,
    "emotional_check": SPECIALIST_TARGET_MEMORY,
    "memory_create": SPECIALIST_TARGET_MEMORY,
    "memory_lookup": SPECIALIST_TARGET_MEMORY,
    "memory_delete": SPECIALIST_TARGET_MEMORY,
    "research": SPECIALIST_TARGET_RESEARCH,
    "plan_or_strategy": SPECIALIST_TARGET_RESEARCH,
    "education": SPECIALIST_TARGET_RESEARCH,
    "journal_debrief": SPECIALIST_TARGET_MEMORY,
    "alert_setup": SPECIALIST_TARGET_MARKET,
    "general_chat": SPECIALIST_TARGET_GENERAL,
}


class AgentPipelineStage(BaseModel):
    """One pipeline stage inside a single agent turn."""

    name: str
    status: str = "pending"
    summary: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentPipelineNodePlan(BaseModel):
    """One planned pipeline node in a composable execution graph."""

    name: str
    status: str = "planned"
    summary: str = ""
    instruction: str = ""
    config: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentPipelineTrace(BaseModel):
    """Serializable trace of one agent turn."""

    entry_agent: str
    router_agent: str = "intent_router"
    architecture_mode: str = "router_ready_single_runtime"
    selected_next_agent: str = SPECIALIST_TARGET_GENERAL
    next_agent_status: str = "planned_only"
    dispatch_reason: str = ""
    routing_intent: str = "general_chat"
    routing_confidence: str = "low"
    should_clarify: bool = False
    fallback_mode: str = "none"
    tool_failure_count: int = 0
    final_status: str = "pending"
    stages: List[AgentPipelineStage] = Field(default_factory=list)
    pipeline_nodes: List[AgentPipelineNodePlan] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)

    def update_stage(
        self,
        name: str,
        *,
        status: str,
        summary: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Create or update one stage in-place."""
        for stage in self.stages:
            if stage.name == name:
                stage.status = status
                if summary:
                    stage.summary = summary
                if metadata:
                    stage.metadata.update(metadata)
                return
        self.stages.append(
            AgentPipelineStage(
                name=name,
                status=status,
                summary=summary,
                metadata=metadata or {},
            )
        )

    def update_node(
        self,
        name: str,
        *,
        status: str,
        summary: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Create or update one pipeline node in-place."""
        for node in self.pipeline_nodes:
            if node.name == name:
                node.status = status
                if summary:
                    node.summary = summary
                if metadata:
                    node.metadata.update(metadata)
                return
        self.pipeline_nodes.append(
            AgentPipelineNodePlan(
                name=name,
                status=status,
                summary=summary,
                metadata=metadata or {},
            )
        )

    def record_tool_failure(self, tool_name: str, error: str) -> None:
        """Record one tool failure without losing the rest of the pipeline."""
        self.tool_failure_count += 1
        self.errors.append(f"{tool_name}: {error}")
        self.update_stage(
            "execution",
            status="degraded",
            summary="One or more tools failed but the agent continued.",
            metadata={
                "tool_failure_count": self.tool_failure_count,
            },
        )

    def mark_fallback(self, mode: str, reason: str) -> None:
        """Mark the whole turn as entering a fallback mode."""
        self.fallback_mode = mode
        if reason:
            self.errors.append(reason)

    def finalize(self, status: str) -> None:
        """Mark final status for the pipeline."""
        self.final_status = status

    def resolve_next_agent_status(self) -> str:
        """Derive a more honest next-agent execution status from the executed nodes."""
        node_names = {node.name for node in self.pipeline_nodes}
        if self.should_clarify and PIPELINE_NODE_CLARIFICATION_PREP in node_names:
            clarification_node = next(
                (node for node in self.pipeline_nodes if node.name == PIPELINE_NODE_CLARIFICATION_PREP),
                None,
            )
            if clarification_node and clarification_node.status == "completed":
                return "clarification_node_completed"

        if self.selected_next_agent == SPECIALIST_TARGET_GENERAL and PIPELINE_NODE_GENERAL_FALLBACK in node_names:
            general_node = next(
                (node for node in self.pipeline_nodes if node.name == PIPELINE_NODE_GENERAL_FALLBACK),
                None,
            )
            if general_node and general_node.status == "completed":
                return "general_node_completed"

        effective_nodes = [
            node for node in self.pipeline_nodes
            if node.name != PIPELINE_NODE_RESPONSE_COMPOSER
        ]
        if any(node.status in {"degraded", "failed"} for node in effective_nodes):
            return "represented_by_pipeline_nodes_degraded"
        if any(node.status == "completed" for node in effective_nodes):
            return "represented_by_pipeline_nodes"
        return "planned_only"


def resolve_specialist_target(intent_context: AgentIntentContext) -> str:
    """Resolve the next planned specialist target without instantiating it yet."""
    if intent_context.should_clarify:
        return SPECIALIST_TARGET_CLARIFICATION

    if intent_context.confidence == "low":
        return SPECIALIST_TARGET_GENERAL

    return INTENT_TO_SPECIALIST_TARGET.get(
        intent_context.intent,
        SPECIALIST_TARGET_GENERAL,
    )


def should_plan_chart_analysis(
    intent_context: AgentIntentContext,
    user_input: str,
) -> bool:
    """Return whether this request should include the chart-analysis node."""
    if intent_context.should_clarify:
        return False

    if intent_context.confidence not in {"high", "medium"}:
        return False

    if "chart" not in set(intent_context.preferred_tool_groups or []):
        return False

    lowered = (user_input or "").lower()
    chart_keywords = {
        "chart",
        "indicator",
        "rsi",
        "macd",
        "bollinger",
        "bb",
        "ema",
        "sma",
        "stochastic",
        "atr",
        "adx",
        "tradingview",
    }
    keyword_match = any(keyword in lowered for keyword in chart_keywords)
    indicator_bias = (
        intent_context.indicator_preference != "auto"
        or intent_context.need_indicator_confirmation
        or bool(intent_context.inferred_indicator_hint)
    )

    return keyword_match or indicator_bias


def resolve_selected_next_agent(
    intent_context: AgentIntentContext,
    user_input: str,
) -> str:
    """Resolve the currently planned next agent target."""
    return resolve_specialist_target(intent_context)


def should_plan_market_snapshot(intent_context: AgentIntentContext) -> bool:
    """Return whether this request should include the market-snapshot node."""
    if intent_context.should_clarify:
        return False

    if intent_context.confidence not in {"high", "medium"}:
        return False

    preferred_groups = set(intent_context.preferred_tool_groups or [])
    return bool(preferred_groups.intersection({"market", "research"}))


def should_plan_research_snapshot(intent_context: AgentIntentContext) -> bool:
    """Return whether this request should include the research-snapshot node."""
    if intent_context.should_clarify:
        return False

    if intent_context.confidence not in {"high", "medium"}:
        return False

    return resolve_specialist_target(intent_context) == SPECIALIST_TARGET_RESEARCH


def should_plan_portfolio_snapshot(intent_context: AgentIntentContext) -> bool:
    """Return whether this request should include the portfolio-snapshot node."""
    if intent_context.should_clarify:
        return False
    if intent_context.confidence not in {"high", "medium"}:
        return False
    return resolve_specialist_target(intent_context) == SPECIALIST_TARGET_PORTFOLIO


def should_plan_execution_snapshot(intent_context: AgentIntentContext) -> bool:
    """Return whether this request should include the execution-snapshot node."""
    if intent_context.should_clarify:
        return False
    if intent_context.confidence not in {"high", "medium"}:
        return False
    return resolve_specialist_target(intent_context) == SPECIALIST_TARGET_EXECUTION


def should_plan_memory_snapshot(intent_context: AgentIntentContext) -> bool:
    """Return whether this request should include the memory-snapshot node."""
    if intent_context.should_clarify:
        return False
    if intent_context.confidence not in {"high", "medium"}:
        return False
    return resolve_specialist_target(intent_context) == SPECIALIST_TARGET_MEMORY


def build_pipeline_nodes(
    *,
    intent_context: AgentIntentContext,
    user_input: str,
) -> List[AgentPipelineNodePlan]:
    """Build a composable execution-node plan for one request."""
    nodes: List[AgentPipelineNodePlan] = []

    if intent_context.should_clarify:
        nodes.append(
            AgentPipelineNodePlan(
                name=PIPELINE_NODE_CLARIFICATION_PREP,
                summary="Prepare the minimum structured clarification before the main answer.",
                instruction=(
                    "Act as a clarification-prep specialist step. Focus on the minimum clarification needed to safely "
                    "continue. Prefer structured hint options when they are available."
                ),
                config={
                    "llm_allowed_tool_names": ["show_hint"],
                },
            )
        )
        nodes.append(
            AgentPipelineNodePlan(
                name=PIPELINE_NODE_RESPONSE_COMPOSER,
                summary="Use the accumulated node observations when forming the final response.",
                config={},
            )
        )
        return nodes

    if intent_context.confidence == "low":
        nodes.append(
            AgentPipelineNodePlan(
                name=PIPELINE_NODE_GENERAL_FALLBACK,
                summary="Prepare a safer low-confidence fallback mode before the main answer.",
                instruction=(
                    "Act as a general-fallback specialist step. Focus on uncertainty-aware behavior, avoid "
                    "over-committing, and prepare the final runtime to answer safely when routing confidence is low."
                ),
                config={
                    "llm_allowed_tool_names": [
                        "show_hint",
                        "show_plan",
                        "show_thinking_summary",
                    ],
                },
            )
        )

    if should_plan_chart_analysis(intent_context, user_input):
        nodes.append(
            AgentPipelineNodePlan(
                name=PIPELINE_NODE_CHART_ANALYSIS,
                summary="Inspect the active TradingView workspace before the main answer.",
                instruction=(
                    "Act as a chart-analysis specialist step. Focus on chart state, symbol/timeframe alignment, "
                    "temporary indicator setup, and indicator-value observation. Respect locked asset scope, "
                    "avoid chart-writing behavior, and gather only evidence that improves the final answer."
                ),
                config={
                    "allow_symbol_change_when_global": True,
                    "allow_indicator_add": True,
                    "allow_chart_write": False,
                    "max_steps": 4,
                    "llm_blocked_tool_names": [
                        "tv_draw_line",
                        "tv_draw_horizontal_line",
                        "tv_clear_drawings",
                        "tv_create_alert",
                        "tv_list_alerts",
                        "tv_delete_alert",
                    ],
                },
            )
        )

    if should_plan_market_snapshot(intent_context):
        nodes.append(
            AgentPipelineNodePlan(
                name=PIPELINE_NODE_MARKET_SNAPSHOT,
                summary="Gather live price and recent symbol headlines before the main answer.",
                instruction=(
                    "Act as a market-snapshot specialist step. Focus on read-only market context, "
                    "including live price state and recent asset-specific headlines. Reuse the chart-selected "
                    "symbol when available, stay compact, and gather only evidence that improves the final answer."
                ),
                config={
                    "max_headlines": 3,
                },
            )
        )

    if should_plan_research_snapshot(intent_context):
        nodes.append(
            AgentPipelineNodePlan(
                name=PIPELINE_NODE_RESEARCH_SNAPSHOT,
                summary="Gather compact news and web context before the main answer.",
                instruction=(
                    "Act as a research-snapshot specialist step. Focus on compact, high-signal context from "
                    "dedicated news tools plus web search. Prefer symbol-specific news first when the request is "
                    "asset-sensitive, otherwise prefer a compact trending-news view before broader search."
                ),
                config={
                    "max_headlines": 3,
                    "max_search_results": 3,
                },
            )
        )

    if should_plan_portfolio_snapshot(intent_context):
        nodes.append(
            AgentPipelineNodePlan(
                name=PIPELINE_NODE_PORTFOLIO_SNAPSHOT,
                summary="Gather balances, collateral, and positions before the main answer.",
                instruction=(
                    "Act as a portfolio-snapshot specialist step. Focus on read-only balances, collateral, and "
                    "position context from connected exchanges. Gather only the state needed to improve the final answer."
                ),
                config={},
            )
        )

    if should_plan_execution_snapshot(intent_context):
        nodes.append(
            AgentPipelineNodePlan(
                name=PIPELINE_NODE_EXECUTION_SNAPSHOT,
                summary="Gather execution readiness and current order state before the main answer.",
                instruction=(
                    "Act as an execution-snapshot specialist step. Focus on read-only execution readiness, open-order "
                    "state, and whether Backpack or Drift execution is enabled for this request."
                ),
                config={},
            )
        )

    if should_plan_memory_snapshot(intent_context):
        nodes.append(
            AgentPipelineNodePlan(
                name=PIPELINE_NODE_MEMORY_SNAPSHOT,
                summary="Recall relevant user memory before the main answer.",
                instruction=(
                    "Act as a memory-snapshot specialist step. Focus on recalling relevant stored user memory that "
                    "helps the final answer, without mutating or deleting memory."
                ),
                config={
                    "memory_limit": 5,
                },
            )
        )

    nodes.append(
        AgentPipelineNodePlan(
            name=PIPELINE_NODE_RESPONSE_COMPOSER,
            summary="Use the accumulated node observations when forming the final response.",
            config={},
        )
    )
    return nodes


def build_pipeline_trace(
    *,
    entry_agent: str,
    intent_context: AgentIntentContext,
    user_input: str = "",
) -> AgentPipelineTrace:
    """Build a default pipeline trace after routing."""
    selected_next_agent = resolve_selected_next_agent(intent_context, user_input)
    trace = AgentPipelineTrace(
        entry_agent=entry_agent,
        selected_next_agent=selected_next_agent,
        next_agent_status="planned_only",
        dispatch_reason=intent_context.routing_reason or intent_context.system_guidance,
        routing_intent=intent_context.intent,
        routing_confidence=intent_context.confidence,
        should_clarify=intent_context.should_clarify,
        pipeline_nodes=build_pipeline_nodes(
            intent_context=intent_context,
            user_input=user_input,
        ),
    )
    trace.update_stage(
        "intake",
        status="completed",
        summary="Accepted the request and normalized runtime context.",
    )
    trace.update_stage(
        "routing",
        status="completed" if intent_context.confidence != "low" else "degraded",
        summary=(
            f"Routed to intent '{intent_context.intent}' with confidence "
            f"'{intent_context.confidence}'."
        ),
        metadata={
            "intent": intent_context.intent,
            "user_goal_type": intent_context.user_goal_type,
            "analysis_mode": intent_context.analysis_mode,
            "analysis_scope": intent_context.analysis_scope,
            "preferred_tool_groups": intent_context.preferred_tool_groups,
        },
    )
    trace.update_stage(
        "dispatch",
        status="completed",
        summary=f"Planned next agent target '{selected_next_agent}'.",
        metadata={
            "selected_next_agent": selected_next_agent,
            "specialist_agents_built": False,
            "pipeline_nodes": [node.name for node in trace.pipeline_nodes],
        },
    )
    trace.update_stage(
        "execution",
        status="pending",
        summary="Waiting for the active runtime to execute the request.",
    )
    trace.update_stage(
        "completion",
        status="pending",
        summary="Waiting for final response assembly.",
    )

    if intent_context.confidence == "low":
        trace.mark_fallback(
            "low_confidence_route",
            "The router returned low confidence, so the request falls back to the general runtime path.",
        )

    if intent_context.should_clarify:
        trace.mark_fallback(
            "clarification_required",
            intent_context.clarification_reason or "Clarification is required before safe execution.",
        )

    return trace
