# Intent Routing

This document explains how the backend classifies a user request before the main agent response is generated.

## Why Intent Routing Exists

The backend uses one adaptive `TradingAgent` runtime rather than separate agents for each task.

Intent routing helps the runtime decide:

- what kind of task the user is asking for
- what response shape is most useful
- which tool groups should be available
- whether clarification is actually needed

## Routing Output

The router currently produces a structured context with these key fields:

- `intent`
- `user_goal_type`
- `goal_summary`
- `analysis_mode`
- `analysis_scope`
- `indicator_preference`
- `need_indicator_confirmation`
- `inferred_indicator_hint`
- `confidence`
- `preferred_tool_groups`
- `routing_reason`
- `response_language`
- `should_clarify`
- `clarification_reason`
- `suggested_hint_title`
- `suggested_hint_options`

## Top-Level Intent Families

The current top-level intent families are:

- `market_analysis`
- `trade_setup`
- `position_management`
- `portfolio_review`
- `market_scan`
- `news_impact`
- `position_sizing`
- `broker_execution`
- `trade_review`
- `macro_context`
- `regulatory_check`
- `preference_update`
- `context_reset`
- `emotional_check`
- `memory_create`
- `memory_lookup`
- `memory_delete`
- `research`
- `plan_or_strategy`
- `education`
- `journal_debrief`
- `alert_setup`
- `general_chat`

## What `intent` Means

`intent` is the main domain of work.

Examples:

- `portfolio_review` means the user is asking at account or portfolio level
- `trade_setup` means the user is trying to form or refine a setup
- `broker_execution` means the user is dealing with execution or operational order behavior

## What `user_goal_type` Means

`user_goal_type` describes the shape of the outcome the user wants.

Examples:

- `analyze`
- `compare`
- `plan`
- `decision_support`
- `execution_prep`
- `risk_review`
- `second_opinion`
- `scenario_planning`

This matters because the same top-level intent can still need very different response shapes.

Example:

- `market_analysis + analyze`
- `market_analysis + compare`
- `market_analysis + second_opinion`

These are all still market analysis, but they should not respond the same way.

## What `analysis_mode` Means

`analysis_mode` is the high-level lens.

Examples:

- `technical`
- `fundamental`
- `news`
- `mixed`
- `macro`
- `portfolio`
- `psychological`
- `regulatory`

This helps the runtime decide how to frame the work even before specific tools are used.

## What `analysis_scope` Means

`analysis_scope` narrows the expected depth or angle.

Examples:

- `bias_only`
- `full_setup`
- `risk_review`
- `comparison`
- `scenario_planning`
- `portfolio_review`
- `market_scan`
- `liquidity`
- `correlation`

This lets the router keep the taxonomy compact without creating too many top-level intents.

## Combination-Only Patterns

Some patterns are intentionally not top-level intents.

They are represented as combinations instead:

- `comparison`
  - usually `market_analysis + user_goal_type=compare`
- `second_opinion`
  - usually `market_analysis + user_goal_type=second_opinion`
- `scenario_planning`
  - usually `plan_or_strategy` or `portfolio_review` plus `user_goal_type=scenario_planning`
- `opportunity_timing`
  - usually `trade_setup` or `position_management` plus `user_goal_type=timing_decision`
- `liquidity_check`
  - usually `market_analysis + analysis_scope=liquidity`
- `correlation_check`
  - usually `market_analysis + analysis_scope=correlation`
- `knowledge_gap`
  - usually `education + user_goal_type=learn_path`

This keeps the top-level taxonomy stable while still letting the router express useful nuance.

## Tool Group Filtering

After routing, the backend can narrow the available tool schema using tool groups.

Current groups are:

- `market`
- `research`
- `chart`
- `monitoring`
- `memory`
- `portfolio`
- `execution`
- `ui`

This means the router is not only descriptive. It also shapes the tool surface sent to the model.

## Clarification Behavior

The router also decides whether a request should be clarified.

The current behavior is intentionally conservative:

- minor typos should not trigger clarification
- shorthand should usually be inferred
- `show_hint` should only be used when ambiguity blocks a reliable answer

So `should_clarify` is for genuinely blocking ambiguity, not for every imperfect message.

## Response Language

The router can bias the response language through:

- `english`
- `match_user`

The backend policy is still English by default unless the user clearly prefers another language.

## Practical Mental Model

You can think of the routing model like this:

- `intent`: what domain of work is this
- `user_goal_type`: what kind of result does the user want
- `analysis_mode`: what lens should the agent use
- `analysis_scope`: how narrow or deep should the work be
- `preferred_tool_groups`: what tool surface should be available

## Related Documentation

- [Agents Index](../index.md)
- [Agent Runtime](../runtime/index.md)
- [Agent Context](../context/index.md)
- [Agent Platform Feature](../../features/agent/index.md)
