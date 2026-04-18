# Agent Platform

The Rabit backend uses a single adaptive `TradingAgent` entry point.

## Current Capabilities

- multimodal uploads for images and PDFs
- intent routing before final response generation
- optional tool gating to reduce prompt overhead
- SSE streaming for assistant text and UI events
- frontend-selected conversation style
- frontend-selected trading style
- frontend-selected market context
- decision-support tools for market scan, position sizing, and structured trade debriefs

## UI-Oriented Agent Events

The agent can emit:

- `thinking_summary`
- `plan`
- `hint`
- `assistant_delta`
- `done`

These events are exposed through the streaming chat endpoint and are designed for frontend rendering.

## Related Documentation

- [REST API](../../api/rest-api.md)
- [Agents Index](../../agents/index.md)
- [Memory and Context](../memory/index.md)
