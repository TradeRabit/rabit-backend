"""Model-based intent routing for user messages."""
import json
from typing import Any, Dict, List, Optional, Sequence, Set

from pydantic import BaseModel, Field


INTENT_VALUES = {
    "market_analysis",
    "trade_setup",
    "memory_create",
    "memory_lookup",
    "memory_delete",
    "research",
    "plan_or_strategy",
    "general_chat",
}

CONFIDENCE_VALUES = {"high", "medium", "low"}
TOOL_GROUP_VALUES = {"market", "research", "chart", "monitoring", "memory", "ui"}
RESPONSE_LANGUAGE_VALUES = {"english", "match_user"}
USER_GOAL_TYPE_VALUES = {
    "ask",
    "explain",
    "analyze",
    "compare",
    "recommend",
    "plan",
    "monitor",
    "remember",
    "delete",
    "decision_support",
    "execution_prep",
    "risk_review",
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
    "ui": {
        "show_thinking_summary",
        "show_plan",
        "show_hint",
    },
}

INTENT_TO_GROUPS: Dict[str, Set[str]] = {
    "market_analysis": {"market", "research", "chart", "monitoring", "ui"},
    "trade_setup": {"market", "chart", "monitoring", "research", "ui"},
    "memory_create": {"memory", "ui"},
    "memory_lookup": {"memory", "ui"},
    "memory_delete": {"memory", "ui"},
    "research": {"research", "market", "chart", "ui"},
    "plan_or_strategy": {"market", "research", "chart", "monitoring", "memory", "ui"},
    "general_chat": {"market", "research", "chart", "monitoring", "memory", "ui"},
}

INTENT_GUIDANCE: Dict[str, str] = {
    "market_analysis": "The user's primary intent is market analysis. Prefer analysis, research, and chart-reading tools before giving conclusions.",
    "trade_setup": "The user's primary intent is building or managing a trade setup. Prefer price, chart, and monitoring tools, and stay focused on actionable setup details.",
    "memory_create": "The user wants a stable fact or preference remembered. Prefer memory tools and avoid unrelated research unless needed for clarification.",
    "memory_lookup": "The user wants previously saved memory recalled. Prefer memory lookup before broader research.",
    "memory_delete": "The user wants saved memory removed. Prefer memory deletion and use hints if the target is ambiguous.",
    "research": "The user's primary intent is research. Prefer web search and news tools, then summarize findings clearly.",
    "plan_or_strategy": "The user wants a strategy or step-by-step plan. Prefer showing a plan and use supporting tools only when helpful.",
    "general_chat": "The user's request is broad or mixed. Use judgment and keep the tool usage focused on the most relevant path.",
}


class AgentIntentContext(BaseModel):
    """Structured intent routing output."""

    intent: str = Field(default="general_chat")
    user_goal_type: str = Field(default="ask")
    goal_summary: str = Field(default="")
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
            "remember": "Focus on storing durable user information correctly.",
            "delete": "Focus on removing the requested saved information safely.",
            "decision_support": "Help the user make a decision with scenarios, evidence, and risk framing.",
            "execution_prep": "Prepare the user for execution with concrete levels, prerequisites, and checks.",
            "risk_review": "Review the setup primarily through downside, invalidation, and risk controls.",
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


def _normalize_user_goal_type(value: Any) -> str:
    """Normalize user goal type."""
    normalized = str(value or "ask").strip().lower()
    if normalized in USER_GOAL_TYPE_VALUES:
        return normalized
    return "ask"


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
        confidence=confidence,
        preferred_tool_groups=preferred_tool_groups,
        routing_reason=routing_reason,
        response_language=response_language,
        should_clarify=should_clarify,
        clarification_reason=clarification_reason,
        suggested_hint_title=suggested_hint_title,
        suggested_hint_options=suggested_hint_options,
    )


def build_intent_prompt(user_input: str, history: Sequence[Dict[str, Any]]) -> str:
    """Build a compact routing prompt for the classifier model call."""
    recent_history = []
    for item in history[-4:]:
        role = str(item.get("role", "user"))
        content = item.get("content", "")
        recent_history.append(f"{role}: {content}")

    history_text = "\n".join(recent_history) if recent_history else "(no prior history)"
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

Valid intents:
- market_analysis
- trade_setup
- memory_create
- memory_lookup
- memory_delete
- research
- plan_or_strategy
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
- remember
- delete
- decision_support
- execution_prep
- risk_review
- clarify

Return only JSON with this exact shape:
{{
  "intent": "market_analysis",
  "user_goal_type": "analyze",
  "goal_summary": "short summary",
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

Latest user message:
{user_input}
""".strip()
