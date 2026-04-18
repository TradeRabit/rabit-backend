# Agent Visual Guide

This is a simplified mental model of how one request moves through the backend agent stack.

## Request Flow

```text
frontend request
  -> auth and request normalization
  -> TradingAgent entry point
  -> intent routing
  -> tool-group filtering
  -> prompt assembly with runtime context
  -> tool-enabled response generation
  -> REST response or SSE stream
```

## Runtime Inputs

The agent can be influenced by:

- authenticated user identity
- conversation style
- trading style
- market context
- Backpack execution gate
- Drift execution gate
- uploaded attachments

## Runtime Outputs

The runtime can produce:

- normal chat response
- streaming text deltas
- thinking summary events
- plan events
- hint events
- intent metadata

## Why This Matters

The backend no longer needs many separate agent binaries to support different behavior.

Instead, one runtime adapts based on:

- routing
- tool access
- request context
- frontend state

## Related Documentation

- [Agent Runtime Structure](./structure.md)
- [Agent Auth](../auth/index.md)
- [Agent Context](../context/index.md)
- [Agent Routing](../routing/index.md)
- [Agent Exchange Behavior](../exchanges/index.md)
