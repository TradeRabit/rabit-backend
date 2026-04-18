"""Model-based intent routing for user messages."""
import json
from typing import Any, Dict, List, Optional, Sequence, Set

from pydantic import BaseModel, Field


INTENT_VALUES = {
    "market_analysis",
    "trade_setup",
    "position_management",
    "portfolio_review",
    "market_scan",
    "news_impact",
    "position_sizing",
    "broker_execution",
    "trade_review",
    "macro_context",
    "regulatory_check",
    "preference_update",
    "context_reset",
    "emotional_check",
    "memory_create",
    "memory_lookup",
    "memory_delete",
    "research",
    "plan_or_strategy",
    "education",
    "journal_debrief",
    "alert_setup",
    "general_chat",
}

CONFIDENCE_VALUES = {"high", "medium", "low"}
TOOL_GROUP_VALUES = {
    "market",
    "research",
    "chart",
    "monitoring",
    "memory",
    "portfolio",
    "execution",
    "ui",
}
RESPONSE_LANGUAGE_VALUES = {"english", "match_user"}
ANALYSIS_MODE_VALUES = {
    "technical",
    "fundamental",
    "news",
    "mixed",
    "memory",
    "sentiment",
    "macro",
    "regulatory",
    "operational",
    "portfolio",
    "psychological",
    "general",
}
ANALYSIS_SCOPE_VALUES = {
    "bias_only",
    "full_setup",
    "risk_review",
    "comparison",
    "scenario_planning",
    "correlation",
    "liquidity",
    "debrief",
    "portfolio_review",
    "market_scan",
    "general",
}
INDICATOR_PREFERENCE_VALUES = {
    "auto",
    "price_action_only",
    "indicator_light",
    "indicator_heavy",
    "user_specified",
}
USER_GOAL_TYPE_VALUES = {
    "ask",
    "explain",
    "analyze",
    "compare",
    "recommend",
    "plan",
    "monitor",
    "confirmation",
    "second_opinion",
    "scenario_planning",
    "timing_decision",
    "sizing",
    "reflect",
    "learn_path",
    "remember",
    "delete",
    "decision_support",
    "execution_prep",
    "risk_review",
    "reset_preferences",
    "reset_context",
    "clarify",
}

TOOL_GROUPS: Dict[str, Set[str]] = {
    "market": {"get_price"},
    "research": {
        "web_search",
        "get_latest_news",
        "search_news_by_keywords",
        "get_trending_news",
        "search_news_by_symbols",
        "get_monitoring_status",
    },
    "chart": {name for name in (
        "tv_get_state",
        "tv_set_symbol",
        "tv_set_timeframe",
        "tv_set_chart_type",
        "tv_scroll_to_date",
        "tv_get_quote",
        "tv_get_ohlcv",
        "tv_get_indicator_values",
        "tv_add_indicator",
        "tv_remove_indicator",
        "tv_set_indicator_inputs",
        "tv_draw_line",
        "tv_draw_horizontal_line",
        "tv_clear_drawings",
        "tv_create_alert",
        "tv_list_alerts",
        "tv_delete_alert",
        "tv_capture_screenshot",
    )},
    "monitoring": {
        "add_price_alert",
        "remove_price_alert",
        "list_price_alerts",
        "get_price_alert",
        "get_price_monitor_stats",
        "start_price_monitor",
        "stop_price_monitor",
        "start_news_monitoring",
        "stop_news_monitoring",
        "get_monitoring_status",
    },
    "memory": {
        "add_user_memory",
        "get_user_memory",
        "delete_user_memory",
        "clear_user_memories",
    },
    "portfolio": {
        "backpack_get_balances",
        "backpack_get_collateral",
        "backpack_get_open_orders",
        "backpack_get_order_history",
        "backpack_get_fill_history",
        "backpack_get_positions",
        "backpack_get_position_history",
        "drift_get_account_context",
        "drift_get_account_snapshot",
        "drift_get_balances",
        "drift_get_collateral",
        "drift_get_open_orders",
        "drift_get_order_history",
        "drift_get_fill_history",
        "drift_get_positions",
        "drift_get_open_positions",
        "drift_get_position_history",
    },
    "execution": {
        "backpack_get_open_orders",
        "backpack_place_order",
        "backpack_cancel_order",
        "drift_get_open_orders",
    },
    "ui": {
        "show_thinking_summary",
        "show_plan",
        "show_hint",
    },
}

INTENT_TO_GROUPS: Dict[str, Set[str]] = {
    "market_analysis": {"market", "research", "chart", "monitoring", "ui"},
    "trade_setup": {"market", "chart", "monitoring", "research", "ui"},
    "position_management": {"market", "chart", "monitoring", "research", "portfolio", "execution", "ui"},
    "portfolio_review": {"market", "chart", "research", "memory", "portfolio", "ui"},
    "market_scan": {"market", "chart", "research", "monitoring", "ui"},
    "news_impact": {"research", "market", "chart", "ui"},
    "position_sizing": {"market", "chart", "portfolio", "ui"},
    "broker_execution": {"market", "monitoring", "portfolio", "execution", "ui"},
    "trade_review": {"market", "chart", "research", "memory", "portfolio", "ui"},
    "macro_context": {"research", "market", "ui"},
    "regulatory_check": {"research", "ui"},
    "preference_update": {"memory", "ui"},
    "context_reset": {"memory", "ui"},
    "emotional_check": {"memory", "ui"},
    "memory_create": {"memory", "ui"},
    "memory_lookup": {"memory", "ui"},
    "memory_delete": {"memory", "ui"},
    "research": {"research", "market", "chart", "ui"},
    "plan_or_strategy": {"market", "research", "chart", "monitoring", "memory", "ui"},
    "education": {"research", "market", "chart", "ui"},
    "journal_debrief": {"market", "chart", "research", "memory", "ui"},
    "alert_setup": {"market", "chart", "monitoring", "ui"},
    "general_chat": {"market", "research", "chart", "monitoring", "memory", "portfolio", "ui"},
}

INTENT_GUIDANCE: Dict[str, str] = {
    "market_analysis": "The user's primary intent is market analysis. Prefer analysis, research, and chart-reading tools before giving conclusions.",
    "trade_setup": "The user's primary intent is building or managing a trade setup. Prefer price, chart, and monitoring tools, and stay focused on actionable setup details.",
    "position_management": "The user's primary intent is managing an existing position. Focus on stop logic, take-profit logic, invalidation, and position handling rather than fresh entries.",
    "portfolio_review": "The user's primary intent is reviewing total portfolio health. Focus on exposure, concentration, diversification, and portfolio-level risk rather than one trade only.",
    "market_scan": "The user's primary intent is hunting for opportunities across multiple assets. Focus on screening, ranking, and identifying promising setups rather than deep-diving one asset too early.",
    "news_impact": "The user's primary intent is understanding how a specific event or headline could move the market. Focus on event-driven impact, scenarios, and reaction pathways.",
    "position_sizing": "The user's primary intent is sizing a position. Focus on risk budget, sizing logic, and the relationship between stop distance and position size.",
    "broker_execution": "The user's primary intent is troubleshooting execution or order behavior. Focus on fills, slippage, order state, and operational trading issues.",
    "trade_review": "The user's primary intent is reviewing a recently completed trade. Focus on entry quality, exit quality, mistakes, timing, and lessons learned.",
    "macro_context": "The user's primary intent is understanding the bigger macro environment. Focus on regime, economic backdrop, and how macro conditions influence strategy.",
    "regulatory_check": "The user's primary intent is checking legal, compliance, tax, or regulatory impact. Focus on rules, limits, and practical implications while staying cautious.",
    "preference_update": "The user wants to update how the agent behaves or what it remembers as a preference. Focus on stable preference changes and saving them cleanly.",
    "context_reset": "The user wants to reset conversation or working context. Focus on clearing or shifting context instead of continuing previous assumptions.",
    "emotional_check": "The user's primary intent is reflecting on trading psychology. Focus on emotional state, discipline, FOMO, revenge-trading risk, and decision hygiene.",
    "memory_create": "The user wants a stable fact or preference remembered. Prefer memory tools and avoid unrelated research unless needed for clarification.",
    "memory_lookup": "The user wants previously saved memory recalled. Prefer memory lookup before broader research.",
    "memory_delete": "The user wants saved memory removed. Prefer memory deletion and use hints if the target is ambiguous.",
    "research": "The user's primary intent is research. Prefer web search and news tools, then summarize findings clearly.",
    "plan_or_strategy": "The user wants a strategy or step-by-step plan. Prefer showing a plan and use supporting tools only when helpful.",
    "education": "The user's primary intent is learning. Prefer explanation, clear definitions, and teaching over action-oriented trading suggestions.",
    "journal_debrief": "The user's primary intent is reviewing past decisions or performance. Focus on reflection, mistakes, process quality, and lessons learned.",
    "alert_setup": "The user's primary intent is setting or managing alerts. Prefer monitoring tools and clear trigger conditions.",
    "general_chat": "The user's request is broad or mixed. Use judgment and keep the tool usage focused on the most relevant path.",
}


class AgentIntentContext(BaseModel):
    """Structured intent routing output."""

    intent: str = Field(default="general_chat")
    user_goal_type: str = Field(default="ask")
    goal_summary: str = Field(default="")
    analysis_mode: str = Field(default="general")
    analysis_scope: str = Field(default="general")
    indicator_preference: str = Field(default="auto")
    need_indicator_confirmation: bool = Field(default=False)
    inferred_indicator_hint: str = Field(default="")
    confidence: str = Field(default="low")
    preferred_tool_groups: List[str] = Field(default_factory=list)
    routing_reason: str = Field(default="")
    response_language: str = Field(default="english")
    should_clarify: bool = Field(default=False)
    clarification_reason: str = Field(default="")
    suggested_hint_title: str = Field(default="")
    suggested_hint_options: List[Dict[str, str]] = Field(default_factory=list)

    @property
    def allowed_tool_names(self) -> Optional[Set[str]]:
        """Return allowed tool names or None for unrestricted fallback."""
        if self.confidence not in {"high", "medium"}:
            return None

        groups = self.preferred_tool_groups or list(
            INTENT_TO_GROUPS.get(self.intent, {"ui"})
        )
        allowed: Set[str] = set()
        for group in groups:
            allowed.update(TOOL_GROUPS.get(group, set()))
        return allowed or None

    @property
    def system_guidance(self) -> str:
        """Return intent-specific behavior guidance."""
        return INTENT_GUIDANCE.get(self.intent, INTENT_GUIDANCE["general_chat"])

    @property
    def goal_guidance(self) -> str:
        """Return user-goal-specific response guidance."""
        mapping = {
            "ask": "Answer the user's question directly and avoid unnecessary expansion.",
            "explain": "Focus on explanation and understanding instead of action planning.",
            "analyze": "Focus on analysis, evidence, and interpretation before conclusions.",
            "compare": "Structure the response as a comparison with clear tradeoffs.",
            "recommend": "Provide a recommendation with supporting reasoning and risks.",
            "plan": "Provide a structured plan or sequence of steps.",
            "monitor": "Focus on alerting, monitoring setup, triggers, and follow-up conditions.",
            "confirmation": "Treat the user's existing thesis seriously and evaluate whether it holds up.",
            "second_opinion": "Act as a careful second opinion that tests the user's current idea rather than starting from zero.",
            "scenario_planning": "Explore plausible what-if scenarios and explain consequences clearly.",
            "timing_decision": "Focus on whether to act now, wait, or require confirmation before acting.",
            "sizing": "Focus on position size, risk budget, and capital allocation logic.",
            "reflect": "Focus on reflection, process review, and improvement rather than prediction.",
            "learn_path": "Focus on what the user should learn next and why.",
            "remember": "Focus on storing durable user information correctly.",
            "delete": "Focus on removing the requested saved information safely.",
            "decision_support": "Help the user make a decision with scenarios, evidence, and risk framing.",
            "execution_prep": "Prepare the user for execution with concrete levels, prerequisites, and checks.",
            "risk_review": "Review the setup primarily through downside, invalidation, and risk controls.",
            "reset_preferences": "Focus on updating long-lived preferences or behavior settings cleanly.",
            "reset_context": "Focus on wiping or shifting the active context so future replies do not rely on stale assumptions.",
            "clarify": "Use the minimum clarification needed to unblock the task.",
        }
        return mapping.get(
            self.user_goal_type,
            "Stay focused on the user's practical outcome and avoid drifting.",
        )

    @property
    def language_guidance(self) -> str:
        """Return language behavior guidance for the agent."""
        if self.response_language == "match_user":
            return (
                "The user is clearly communicating in a non-English language. "
                "Reply in the user's language."
            )
        return (
            "Default to English. Only switch languages when the user's message clearly "
            "shows a stable preference for another language."
        )

    @property
    def analysis_guidance(self) -> str:
        """Return analysis-mode guidance."""
        mode_mapping = {
            "technical": "Prefer technical analysis and chart-based evidence first.",
            "fundamental": "Prefer fundamental reasoning, project context, and broader market drivers.",
            "news": "Prefer recent news, catalysts, and narrative-sensitive analysis.",
            "mixed": "Blend technical and contextual analysis instead of relying on one lens.",
            "memory": "Prefer the user's stored context and saved preferences where relevant.",
            "sentiment": "Prefer mood, fear-greed, positioning, and market-tone signals.",
            "macro": "Prefer macro regime, rates, liquidity, and top-down context.",
            "regulatory": "Prefer legal, tax, compliance, and rules-oriented reasoning.",
            "operational": "Prefer execution, platform behavior, order mechanics, and trading operations context.",
            "portfolio": "Prefer portfolio-wide exposure, allocation, and diversification reasoning.",
            "psychological": "Prefer emotional discipline, behavioral bias, and decision-quality framing.",
            "general": "Choose the lightest analysis approach that still answers the user well.",
        }
        scope_mapping = {
            "bias_only": "Keep the output focused on directional bias and high-level setup quality.",
            "full_setup": "Provide a more complete setup including context, levels, and invalidation.",
            "risk_review": "Emphasize downside, invalidation, and whether the setup is worth taking.",
            "comparison": "Organize the response as a structured comparison.",
            "scenario_planning": "Explore hypothetical paths and explain how outcomes change under different scenarios.",
            "correlation": "Focus on the relationship between assets or markets rather than isolated performance.",
            "liquidity": "Focus on fill quality, depth, volume, and whether size can be executed cleanly.",
            "debrief": "Focus on what happened, why it happened, and how to improve the process.",
            "portfolio_review": "Focus on the portfolio as a whole instead of one isolated trade.",
            "market_scan": "Focus on screening and narrowing candidates before deep analysis.",
            "general": "Use judgment on how deep the analysis should go.",
        }
        indicator_mapping = {
            "auto": "Choose indicators or pure price action only when they genuinely improve the answer.",
            "price_action_only": "Prefer price action first and avoid unnecessary indicators.",
            "indicator_light": "Use a small number of high-signal indicators only.",
            "indicator_heavy": "A broader indicator set is acceptable if it stays coherent and justified.",
            "user_specified": "Honor the user's specified indicators or indicator family closely.",
        }

        return " ".join(
            [
                mode_mapping.get(self.analysis_mode, mode_mapping["general"]),
                scope_mapping.get(self.analysis_scope, scope_mapping["general"]),
                indicator_mapping.get(
                    self.indicator_preference,
                    indicator_mapping["auto"],
                ),
                (
                    f"Inferred indicator hint: {self.inferred_indicator_hint}."
                    if self.inferred_indicator_hint
                    else ""
                ),
                (
                    "If indicator choice is still too ambiguous and materially affects the answer, "
                    "use show_hint before proceeding."
                    if self.need_indicator_confirmation
                    else ""
                ),
            ]
        ).strip()

    @property
    def clarification_guidance(self) -> str:
        """Return ambiguity-handling guidance for the agent."""
        if not self.should_clarify:
            return (
                "Do not interrupt the flow for minor typos, slang, or light ambiguity. "
                "Infer the most likely meaning and answer directly."
            )

        if self.suggested_hint_options:
            options = ", ".join(
                f"{option.get('id', 'option')}: {option.get('text', '')}"
                for option in self.suggested_hint_options
            )
            return (
                "The request is too ambiguous to answer safely without clarification. "
                f"Use show_hint with clickable options. Suggested title: "
                f"{self.suggested_hint_title or 'Clarify your request'}. "
                f"Suggested options: {options}"
            )

        return (
            "The request is too ambiguous to answer safely without clarification. "
            "Use show_hint with 2-4 short clickable options before continuing."
        )

    @classmethod
    def fallback(cls, reason: str = "") -> "AgentIntentContext":
        """Return a safe fallback intent."""
        return cls(
            intent="general_chat",
            user_goal_type="ask",
            goal_summary="Handle the user's request in a general way.",
            analysis_mode="general",
            analysis_scope="general",
            indicator_preference="auto",
            need_indicator_confirmation=False,
            confidence="low",
            preferred_tool_groups=sorted(INTENT_TO_GROUPS["general_chat"]),
            routing_reason=reason or "Fallback because routing was unavailable.",
            response_language="english",
            should_clarify=False,
        )


def _extract_json_object(text: str) -> Optional[Dict[str, Any]]:
    """Extract the first JSON object from a text blob."""
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    candidate = text[start : end + 1]
    try:
        parsed = json.loads(candidate)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def _normalize_groups(groups: Sequence[str], intent: str) -> List[str]:
    """Normalize tool group values and apply sane defaults."""
    normalized = [group for group in groups if group in TOOL_GROUP_VALUES]
    if normalized:
        return sorted(set(normalized))
    return sorted(INTENT_TO_GROUPS.get(intent, {"ui"}))


def _normalize_response_language(value: Any) -> str:
    """Normalize response language preference."""
    normalized = str(value or "english").strip().lower()
    if normalized in RESPONSE_LANGUAGE_VALUES:
        return normalized
    return "english"


def _normalize_enum(value: Any, allowed: set[str], default: str) -> str:
    """Normalize a simple lowercase enum string."""
    normalized = str(value or default).strip().lower()
    if normalized in allowed:
        return normalized
    return default


def _normalize_user_goal_type(value: Any) -> str:
    """Normalize user goal type."""
    return _normalize_enum(value, USER_GOAL_TYPE_VALUES, "ask")


def _normalize_hint_options(value: Any) -> List[Dict[str, str]]:
    """Normalize suggested hint options into a simple id/text list."""
    if not isinstance(value, list):
        return []

    options: List[Dict[str, str]] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        option_id = str(item.get("id", "")).strip()
        option_text = str(item.get("text", "")).strip()
        if not option_id or not option_text:
            continue
        options.append({"id": option_id, "text": option_text})
    return options


def parse_intent_response(raw_text: str) -> AgentIntentContext:
    """Parse model text into structured intent context."""
    payload = _extract_json_object(raw_text)
    if payload is None:
        return AgentIntentContext.fallback("Intent router returned non-JSON output.")

    intent = str(payload.get("intent", "general_chat")).strip()
    if intent not in INTENT_VALUES:
        intent = "general_chat"
    user_goal_type = _normalize_user_goal_type(payload.get("user_goal_type"))
    analysis_mode = _normalize_enum(payload.get("analysis_mode"), ANALYSIS_MODE_VALUES, "general")
    analysis_scope = _normalize_enum(
        payload.get("analysis_scope"),
        ANALYSIS_SCOPE_VALUES,
        "general",
    )
    indicator_preference = _normalize_enum(
        payload.get("indicator_preference"),
        INDICATOR_PREFERENCE_VALUES,
        "auto",
    )
    need_indicator_confirmation = bool(payload.get("need_indicator_confirmation", False))
    inferred_indicator_hint = str(payload.get("inferred_indicator_hint", "")).strip()

    confidence = str(payload.get("confidence", "low")).strip().lower()
    if confidence not in CONFIDENCE_VALUES:
        confidence = "low"

    goal_summary = str(payload.get("goal_summary", "")).strip()
    routing_reason = str(payload.get("routing_reason", "")).strip()
    preferred_tool_groups = _normalize_groups(
        payload.get("preferred_tool_groups", []),
        intent,
    )
    response_language = _normalize_response_language(payload.get("response_language"))
    should_clarify = bool(payload.get("should_clarify", False))
    clarification_reason = str(payload.get("clarification_reason", "")).strip()
    suggested_hint_title = str(payload.get("suggested_hint_title", "")).strip()
    suggested_hint_options = _normalize_hint_options(payload.get("suggested_hint_options", []))

    return AgentIntentContext(
        intent=intent,
        user_goal_type=user_goal_type,
        goal_summary=goal_summary,
        analysis_mode=analysis_mode,
        analysis_scope=analysis_scope,
        indicator_preference=indicator_preference,
        need_indicator_confirmation=need_indicator_confirmation,
        inferred_indicator_hint=inferred_indicator_hint,
        confidence=confidence,
        preferred_tool_groups=preferred_tool_groups,
        routing_reason=routing_reason,
        response_language=response_language,
        should_clarify=should_clarify,
        clarification_reason=clarification_reason,
        suggested_hint_title=suggested_hint_title,
        suggested_hint_options=suggested_hint_options,
    )


def build_intent_prompt(
    user_input: str,
    history: Sequence[Dict[str, Any]],
    market_context: Optional[Dict[str, Any]] = None,
) -> str:
    """Build a compact routing prompt for the classifier model call."""
    recent_history = []
    for item in history[-4:]:
        role = str(item.get("role", "user"))
        content = item.get("content", "")
        recent_history.append(f"{role}: {content}")

    history_text = "\n".join(recent_history) if recent_history else "(no prior history)"
    market_context_text = json.dumps(market_context or {}, ensure_ascii=False)
    return f"""
Classify the user's primary intent for a trading assistant.

Behavior rules for routing:
- Default the final assistant response language to English.
- Set response_language to "match_user" only when the user is clearly speaking another language consistently.
- Minor typos, slang, shorthand, and light mixed-language phrasing should usually be inferred without clarification.
- Set should_clarify to true only when the request is too ambiguous, too incomplete, or too risky to continue confidently.
- If should_clarify is true, provide a short suggested_hint_title and 2-4 clickable suggested_hint_options.
- Avoid clarification for obvious intent even when spelling is imperfect.
- Set user_goal_type to describe the outcome the user wants, not just the topic they mention.
- Infer the likely analysis_mode and indicator_preference when the user does not specify them directly.
- Prefer agent inference before clarification. Only set need_indicator_confirmation to true when the indicator choice materially changes the answer and remains too ambiguous.

Valid intents:
- market_analysis
- trade_setup
- position_management
- portfolio_review
- market_scan
- news_impact
- position_sizing
- broker_execution
- trade_review
- macro_context
- regulatory_check
- preference_update
- context_reset
- emotional_check
- memory_create
- memory_lookup
- memory_delete
- research
- plan_or_strategy
- education
- journal_debrief
- alert_setup
- general_chat

Valid confidence values:
- high
- medium
- low

Valid preferred_tool_groups:
- market
- research
- chart
- monitoring
- memory
- ui

Valid user_goal_type values:
- ask
- explain
- analyze
- compare
- recommend
- plan
- monitor
- confirmation
- second_opinion
- scenario_planning
- timing_decision
- sizing
- reflect
- learn_path
- remember
- delete
- decision_support
- execution_prep
- risk_review
- reset_preferences
- reset_context
- clarify

Valid analysis_mode values:
- technical
- fundamental
- news
- mixed
- memory
- sentiment
- macro
- regulatory
- operational
- portfolio
- psychological
- general

Valid analysis_scope values:
- bias_only
- full_setup
- risk_review
- comparison
- scenario_planning
- correlation
- liquidity
- debrief
- portfolio_review
- market_scan
- general

Valid indicator_preference values:
- auto
- price_action_only
- indicator_light
- indicator_heavy
- user_specified

Important combination routing patterns:
- comparison requests should usually map to intent=market_analysis, user_goal_type=compare, analysis_scope=comparison
- scenario-planning requests should usually map to plan_or_strategy or portfolio_review with user_goal_type=scenario_planning and analysis_scope=scenario_planning
- second-opinion requests should usually map to market_analysis with user_goal_type=second_opinion instead of inventing a new intent
- opportunity-timing requests should usually map to trade_setup or position_management with user_goal_type=timing_decision
- liquidity-check requests should usually map to market_analysis with analysis_scope=liquidity
- correlation-check requests should usually map to market_analysis with analysis_scope=correlation
- knowledge-gap or "what should I learn next" requests should usually map to education with user_goal_type=learn_path
- prefer these combinations instead of inventing extra top-level intents unless the user's request clearly belongs to an existing explicit intent above

Return only JSON with this exact shape:
{{
  "intent": "market_analysis",
  "user_goal_type": "analyze",
  "goal_summary": "short summary",
  "analysis_mode": "technical",
  "analysis_scope": "full_setup",
  "indicator_preference": "indicator_light",
  "need_indicator_confirmation": false,
  "inferred_indicator_hint": "trend indicators",
  "confidence": "high",
  "preferred_tool_groups": ["market", "chart"],
  "routing_reason": "brief explanation",
  "response_language": "english",
  "should_clarify": false,
  "clarification_reason": "",
  "suggested_hint_title": "",
  "suggested_hint_options": [
    {{"id": "analysis", "text": "Market analysis"}},
    {{"id": "setup", "text": "Trade setup"}}
  ]
}}

Recent conversation:
{history_text}

Frontend market context:
{market_context_text}

Latest user message:
{user_input}
""".strip()
