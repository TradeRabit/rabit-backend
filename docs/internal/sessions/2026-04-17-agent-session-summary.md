# Agent Session Summary

Date: 2026-04-17

This document summarizes the agent-related changes completed in this session so the implementation history is easier to follow without reading multiple plan files.

## Scope

The work in this session focused on improving the single `TradingAgent` entry point instead of introducing multiple runtime agents.

Main goals:
- make the agent support multimodal uploads
- add long-term memory with Mem0
- expose memory management through backend APIs and agent tools
- add tool gating for token efficiency
- add SSE streaming for agent output and UI events
- add agent-driven `plan` and `hint` tools for frontend rendering
- add model-based intent routing so the agent can adapt behavior to the user request
- improve ambiguity handling, typo tolerance, and default response language behavior
- support frontend-selected conversation styles
- support frontend-selected trading styles
- support frontend-selected market context and analysis hints

## Architecture Direction

The backend still uses one concrete runtime agent:
- `TradingAgent` is the entry point
- `BaseAgent` provides the common orchestration layer

Instead of hardcoding rigid flows, the agent now uses an intent-routing step before the main tool-enabled response generation. This keeps the architecture simple while making behavior more adaptive.

## Multimodal Upload Flow

Implemented:
- temporary upload API for image and PDF files
- attachment resolution before chat execution
- multimodal message payload construction for the model
- text-only memory summaries for uploaded files so conversation history stays lightweight

Result:
- users can upload files through `/api/agent/uploads`
- chat requests can reference uploaded `attachment_ids`
- the agent sees attachments as model content blocks, while conversation memory stores only a summary

## Mem0 Integration

Implemented:
- Mem0 client cleanup and backend integration
- support for add, search, list, delete-one, delete-all, and health check
- Mem0 context injection into the system prompt when `user_id` is available
- shutdown cleanup for the Mem0 client lifecycle

Backend memory endpoints added:
- `GET /api/memory/health`
- `GET /api/memory`
- `GET /api/memory/search`
- `POST /api/memory`
- `DELETE /api/memory/{memory_id}`
- `DELETE /api/memory`

Agent memory tools added:
- `add_user_memory`
- `get_user_memory`
- `delete_user_memory`
- `clear_user_memories`

## Tool Gates

Implemented token-saving gates at tool registration level:
- `WEB_SEARCH_ENABLED`
- `MEMORY_TOOLS_ENABLED`

Behavior:
- disabled tools are not included in the tool schema sent to the model
- this reduces prompt/tool overhead instead of failing only at execution time

Important note:
- `MEMORY_TOOLS_ENABLED` only disables the memory tools exposed to the agent
- Mem0 backend APIs and automatic memory context can still remain active

## SSE Streaming

Implemented a dedicated SSE endpoint:
- `POST /api/agent/chat/stream`

Supported stream events:
- `thinking_summary`
- `assistant_delta`
- `plan`
- `hint`
- `error`
- `done`

Behavior:
- `assistant_delta` streams partial assistant text
- `thinking_summary`, `plan`, and `hint` are emitted through agent tools
- `error` events include informative details for tool failures and agent failures
- `done` terminates the stream with request metadata and current intent metadata

## Frontend-Oriented UI Tools

Added agent tools for UI-driven interaction:
- `show_thinking_summary`
- `show_plan`
- `show_hint`

Purpose:
- `show_thinking_summary` gives the frontend a concise user-safe progress message
- `show_plan` provides structured step-by-step progress
- `show_hint` provides HITL-style clickable options for ambiguity resolution

These tools are agent-originated, not injected by the backend as fake system events.

## Conversation Styles

Added explicit frontend-controlled conversation style support through the chat request payload.

Supported styles:
- `normal`
- `learning`
- `concise`
- `explanatory`
- `formal`

Behavior:
- frontend can send the selected style with each agent request
- backend normalizes the value and stores the last used style on the agent
- the selected style is injected into the final system prompt as runtime guidance
- the selected style is returned in normal chat responses and SSE `done` events

Purpose:
- style selection changes how the agent communicates
- it does not replace intent routing and does not change the factual task itself

## Trading Styles

Added explicit frontend-controlled trading style support through the chat request payload.

Supported styles:
- `balanced`
- `price_action`
- `trend_following`
- `momentum_breakout`
- `mean_reversion`
- `smart_money`
- `risk_first`
- `systematic`

Behavior:
- frontend can send the selected trading style with each agent request
- backend normalizes the value and stores the last used trading style on the agent
- the selected trading style is injected into the final system prompt as runtime guidance
- the selected trading style is returned in normal chat responses and SSE `done` events

Purpose:
- trading style changes how the agent frames chart analysis, indicator preference, setup logic, and decisions
- it is separate from conversation style so UI can control tone and trading lens independently

## Market Context

Added optional frontend-controlled market context support through the chat request payload.

Supported ideas:
- `scope_mode` such as `locked_asset` or `global`
- current asset identity such as `asset_id`, `symbol`, and `asset_name`
- working context such as `exchange`, `timeframe`, `source_screen`, and watchlist symbols
- market-state hints such as `trend_bias`, `structure_position`, `volatility_regime`, `momentum_state`, and `summary`

Behavior:
- backend normalizes the context and stores the last used market context on the agent
- runtime prompt now includes both the raw normalized market context and a market-context guidance summary
- `locked_asset` acts as a strong focus bias unless the user explicitly asks to move elsewhere
- the normalized market context is returned in normal chat responses and SSE `done` events

## Exchange Execution Gates

Added optional frontend-controlled exchange execution gating through the chat request payload.

Supported ideas:
- `backpack_execution.enabled` lets frontend explicitly allow or disallow live Backpack trade execution per request
- `drift_execution.enabled` lets frontend explicitly allow or disallow live Drift trade execution per request

Behavior:
- backend also has global hard gates through `BACKPACK_EXECUTION_ENABLED` and `DRIFT_EXECUTION_ENABLED`
- live execution should only be considered allowed when both the global gate and request-level gate are enabled
- normalized execution-gate state is injected into the runtime system prompt
- normalized execution-gate state is returned in normal chat responses and SSE `done` events
- dedicated package paths now exist for exchange-specific account and execution work:
  - `agents/backpack_execution/`
  - `agents/drift_execution/`
  - `agents/tools/backpack_execution/`
  - `agents/tools/drift_execution/`

## Backpack Tools

Added the first Backpack-specific authenticated tool layer.

Current Backpack tools:
- `backpack_get_balances`
- `backpack_get_collateral`
- `backpack_get_open_orders`
- `backpack_get_order_history`
- `backpack_get_fill_history`
- `backpack_get_positions`
- `backpack_get_position_history`
- `backpack_place_order`
- `backpack_cancel_order`

Behavior:
- read-only Backpack tools work without the per-request execution gate, but they still require Backpack API credentials
- live Backpack execution tools require Backpack API credentials
- live Backpack execution tools require both `BACKPACK_EXECUTION_ENABLED=true` and `backpack_execution.enabled=true`
- intent routing now exposes Backpack portfolio tools through portfolio-oriented intents and Backpack execution tools through broker/execution-oriented intents

## Drift Read-Only Tools

Added a Drift-specific read-only tool layer that is intentionally focused on account visibility first, not live order execution.

Current Drift tools:
- `drift_get_account_context`
- `drift_get_account_snapshot`
- `drift_get_balances`
- `drift_get_collateral`
- `drift_get_open_orders`
- `drift_get_order_history`
- `drift_get_fill_history`
- `drift_get_positions`
- `drift_get_open_positions`
- `drift_get_position_history`

Behavior:
- Drift read-only tools require wallet-authenticated identity shaped like `wallet:<solana_wallet_address>`
- Drift does not use Backpack-style API key storage for read-only access
- account snapshot, balances, collateral, open orders, and open positions use the optional Drift SDK path directly
- history tools scan recent user-account transactions and parse Drift events from logs
- history tools are more sensitive to Solana RPC quality than snapshot reads, so public RPC endpoints may rate-limit them
- intent routing now exposes Drift portfolio tools through portfolio-oriented intents

Important note:
- Drift live execution is still not implemented
- the remaining major Drift gap is execution architecture rather than read-only account visibility

## Drift Execution Wallet Resolution

Added the first explicit backend contract for Drift auth-wallet versus execution-wallet handling.

Current implementation:
- Drift `v1` uses `same_wallet` only
- the authenticated wallet from JWT is treated as both:
  - auth wallet
  - Drift execution wallet
- `GET /api/drift/execution-wallet` now returns the resolved execution-wallet state for the authenticated user
- Drift account-context tooling now also exposes the resolved execution-wallet state

Important note:
- different execution wallets are still a future advanced flow
- wallet linking and delegated execution are not implemented yet

## Drift Same-Wallet Execution Bridge

Added the first same-wallet Drift execution API bridge for mobile-first signing flow.

Current endpoints:
- `POST /api/drift/execution/prepare`
- `GET /api/drift/execution/{execution_id}`
- `POST /api/drift/execution/submit`

Behavior:
- these endpoints require wallet-authenticated identity
- `same_wallet` is enforced, so auth wallet and execution wallet must currently match
- `prepare` creates a stored execution intent record owned by the authenticated user
- `prepare` now also builds an unsigned same-wallet Drift perp-order transaction payload for mobile signing
- `submit` accepts an already signed transaction and sends it to Solana RPC
- execution request records are stored in JSON-backed persistence at `DRIFT_EXECUTION_REQUESTS_DB_PATH`
- prepared records now include unsigned transaction bytes, unsigned message bytes, recent blockhash metadata, and derived Drift account public keys

Important note:
- this is still a same-wallet client-signing bridge, not backend-held signing
- the backend constructs an unsigned transaction payload, but it still does not sign it
- linked-wallet execution and delegated signer flows are still future work

## Exchange Connection Storage

Added encrypted multi-user exchange connection storage for Backpack credentials.

Current implementation:
- encrypted JSON-backed store at `EXCHANGE_CONNECTIONS_DB_PATH`
- application-level secret encryption using `EXCHANGE_CREDENTIALS_MASTER_KEY`
- service layer for create, list, update, delete, and active-connection credential lookup
- Backpack tools now prefer the active Backpack connection for the current `user_id` instead of only using global env credentials
- CRUD API endpoints:
  - `POST /api/exchange-connections/backpack`
  - `GET /api/exchange-connections`
  - `PATCH /api/exchange-connections/{connection_id}`
  - `DELETE /api/exchange-connections/{connection_id}`

Important current limitation:
- ownership still depends on the provided `user_id` request field because a full auth/session layer is not yet implemented
- before production use, this should be upgraded so user identity comes from authenticated backend session or JWT claims instead of client-provided `user_id`

## Mobile Wallet Auth

Added a mobile-friendly Solana wallet auth flow:
- `POST /api/auth/wallet/nonce` creates a one-time sign-in challenge
- `POST /api/auth/wallet/verify` verifies the signed challenge and issues a JWT bearer token
- `GET /api/auth/me` returns the authenticated wallet identity from the bearer token

Behavior:
- wallet auth uses signed off-chain message verification against the provided Solana public key
- successful verification issues a JWT whose `user_id` is derived as `wallet:<wallet_address>`
- agent chat and exchange connection endpoints can now derive `user_id` from bearer auth and reject mismatches between authenticated identity and client-provided `user_id`

Current note:
- some routes still accept explicit `user_id` for backward compatibility during development
- production should move fully to auth-derived identity and stop relying on client-provided `user_id`

## Intent Routing

Added a model-based intent router before the main agent response step.

Current routing output includes:
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

Current intent families:
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

Routing behavior:
- tool schema can be filtered by allowed tool groups
- intent guidance is injected into the final system prompt
- user goal guidance is injected into the final system prompt so the agent knows the shape of the expected answer
- intent metadata is returned in normal chat responses
- intent metadata is also returned in SSE `done` events

About `user_goal_type`:
- this field describes the outcome the user wants, not just the topic area
- it helps reduce drift for cases where the same intent can require different response shapes
- examples include `analyze`, `compare`, `plan`, `decision_support`, `execution_prep`, and `risk_review`

About taxonomy v2:
- `position_management` covers active-position handling such as stop-loss, take-profit, scale-out, and exit logic
- `education` covers concept explanations where teaching is more important than trade action
- `journal_debrief` covers reflective review of trades, mistakes, and weekly performance
- `alert_setup` covers explicit alert-oriented requests that should bias toward monitoring tools

About taxonomy design expansion:
- `portfolio_review` covers account- or portfolio-level health instead of one isolated trade
- `market_scan` covers opportunity hunting across multiple assets
- `news_impact` covers event-driven market reaction for a specific macro or news catalyst
- `position_sizing` covers capital allocation and risk-budget questions
- `broker_execution` covers operational order and fill issues
- `trade_review` covers post-trade review of one recent trade
- `macro_context` covers top-down market environment and regime
- `regulatory_check` covers legal, tax, and rules-related questions
- `preference_update` covers explicit user requests to change the agent's style or remembered behavior
- `context_reset` covers resetting stale context or changing working focus
- `emotional_check` covers trading psychology and decision-discipline questions

Additional goal and scope design:
- `user_goal_type` now has room for intents like `confirmation`, `second_opinion`, `scenario_planning`, `timing_decision`, `sizing`, and `reflect`
- `analysis_mode` now has room for `sentiment`, `macro`, `regulatory`, `operational`, `portfolio`, and `psychological`
- `analysis_scope` now has room for `scenario_planning`, `correlation`, `liquidity`, `debrief`, `portfolio_review`, and `market_scan`

Combination patterns intentionally kept out of top-level intent:
- `comparison` is currently represented as `market_analysis` plus `user_goal_type=compare` and usually `analysis_scope=comparison`
- `scenario_planning` is currently represented as `plan_or_strategy` or `portfolio_review` plus `user_goal_type=scenario_planning`
- `second_opinion` is currently represented as `market_analysis` plus `user_goal_type=second_opinion`
- `opportunity_timing` is currently represented as `trade_setup` or `position_management` plus `user_goal_type=timing_decision`
- `liquidity_check` is currently represented as `market_analysis` plus `analysis_scope=liquidity`
- `correlation_check` is currently represented as `market_analysis` plus `analysis_scope=correlation`
- `knowledge_gap` is currently represented as `education` plus `user_goal_type=learn_path`

Design reason:
- these flows already behave like variants of broader intents instead of truly separate domains
- keeping them as combinations avoids exploding the number of top-level intents too early
- router prompt guidance and tests now explicitly document these mappings so the taxonomy stays understandable and stable

About the new analysis hints:
- `analysis_mode` gives the agent a higher-level lens such as `technical`, `news`, or `mixed`
- `analysis_scope` narrows the expected depth such as `bias_only`, `full_setup`, or `risk_review`
- `indicator_preference` lets the router bias the agent toward price action, light indicators, or heavier indicator use
- `inferred_indicator_hint` gives a soft hint instead of rigidly locking a specific indicator set
- `need_indicator_confirmation` is reserved for cases where the agent really should confirm indicator choice before proceeding

## Ambiguity, Typo, and Language Policy

The agent behavior was refined so the UX stays practical:

- default response language is English
- if the user clearly speaks another language consistently, the agent may follow the user language
- minor typos, slang, shorthand, and light mixed-language input should be inferred without clarification
- `show_hint` should be used only when ambiguity is strong enough to block a reliable answer
- the agent should prefer answering first, and only ask when the request is genuinely unclear

This keeps HITL available without overusing it.

## Error Handling Improvements

Tool errors were already informative, and the streaming layer now preserves that style:
- tool validation failures include parameter-level detail
- stream `error` events distinguish between request errors, tool errors, and agent errors
- agent failure still ends with a final `done` event carrying failure status

## Prompt and Runtime Alignment

The `TradingAgent` now uses the system prompt from `agents/system_prompts/trading_agent.txt` as the source of truth.

Prompt behavior was updated to explicitly cover:
- risk-aware trading assistance
- `show_plan` and `show_hint` usage
- typo tolerance
- ambiguity handling
- English-by-default communication
- frontend-selected conversation style behavior
- frontend-selected trading style behavior
- frontend-selected market-context behavior

## Testing Added or Updated

Tests were added or updated for:
- multimodal payload construction
- Mem0 client and API behavior
- memory tools
- tool gates
- SSE streaming routes
- UI stream tools
- prompt loading
- intent router parsing and filtering
- chat and SSE intent metadata

Focused validation completed during the session with passing pytest runs for the affected suites.

## Current State After This Session

The backend now has:
- one adaptive `TradingAgent` entry point
- tool-based streaming UI support
- Mem0 long-term memory support
- backend memory CRUD endpoints
- model-based intent routing
- intent-aware tool filtering
- controlled HITL via `show_hint`
- English-first but user-aware language behavior
- Backpack read-only plus live execution support
- Drift read-only account, portfolio, and recent-history support
- wallet-authenticated identity that can drive exchange-linked tools

## Tools Folder Refactor

The `agents/tools` directory was reorganized to reduce mixing between unrelated tool modules.

Current structure:
- `agents/tools/core/` for registry, definitions, and runtime context
- `agents/tools/market/` for market, news, search, monitoring, and TradingView tool registration
- `agents/tools/memory/` for Mem0-backed tool functions
- `agents/tools/ui/` for streaming UI event tools
- `agents/tools/tradingview/` for the lower-level TradingView implementation package

Purpose:
- make editing and navigation easier
- separate infra from domain tools
- reduce confusion between UI, memory, and market-specific modules

## Recommended Next Steps

Good next steps after this session:
- decide Drift execution architecture explicitly:
  client-side wallet signing, delegated signer, or backend-held signer
- add Drift execution preparation docs and API contract around the chosen signer model
- add Backpack execution guardrails such as per-user approval flow, risk caps, and audit logging
- refine how the frontend sends the selected `hint` option back into chat context
