from agents.intent_router import AgentIntentContext, parse_intent_response
from agents.tools import ToolDefinition, ToolParameter, ToolRegistry


def test_parse_intent_response_builds_allowed_tool_names():
    context = parse_intent_response(
        """
        {
          "intent": "memory_lookup",
          "user_goal_type": "remember",
          "goal_summary": "Find saved user preferences",
          "confidence": "high",
          "preferred_tool_groups": ["memory", "ui"],
          "routing_reason": "User is asking to recall saved information",
          "response_language": "match_user",
          "should_clarify": true,
          "clarification_reason": "Need to know which memory bucket the user means",
          "suggested_hint_title": "What memory do you want to review?",
          "suggested_hint_options": [
            {"id": "risk", "text": "Risk preferences"},
            {"id": "profile", "text": "Profile details"}
          ]
        }
        """
    )

    assert context.intent == "memory_lookup"
    assert context.user_goal_type == "remember"
    assert "get_user_memory" in context.allowed_tool_names
    assert "show_hint" in context.allowed_tool_names
    assert "get_price" not in context.allowed_tool_names
    assert context.response_language == "match_user"
    assert context.should_clarify is True
    assert context.suggested_hint_options[0]["id"] == "risk"


def test_parse_intent_response_falls_back_on_invalid_payload():
    context = parse_intent_response("not-json")

    assert context.intent == "general_chat"
    assert context.user_goal_type == "ask"
    assert context.confidence == "low"
    assert context.allowed_tool_names is None
    assert context.response_language == "english"
    assert context.should_clarify is False


def test_tool_registry_can_filter_schema_by_allowed_names():
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="tool_a",
            description="A",
            parameters=[ToolParameter(name="query", type="string", description="q", required=True)],
            function=None,
        )
    )
    registry.register(
        ToolDefinition(
            name="tool_b",
            description="B",
            parameters=[],
            function=None,
        )
    )

    schema = registry.get_tools_schema(allowed_names={"tool_b"})

    assert [item["name"] for item in schema] == ["tool_b"]
