# System Overview

This page is the lightweight system map for the Rabit backend.

## Main Runtime Layers

```text
client apps
  -> API layer
  -> agent runtime
  -> tools and exchange helpers
  -> memory and context services
  -> websocket and market-data services
  -> external integrations
```

## Core Layers

### API Layer

Responsibilities:

- expose REST routes
- expose SSE and WebSocket entry points
- validate request and response models

Main code:

- `main.py`
- `api/`

### Agent Layer

Responsibilities:

- run the trading assistant
- shape requests with routing and context
- call tools and stream UI-safe events

Main code:

- `agents/core/`
- `agents/intent_router.py`
- `agents/tools/`

### Market and Streaming Layer

Responsibilities:

- subscribe to external market feeds
- normalize market updates
- support charting and price consumers

Main code:

- `ws/`

### Integration Layer

Responsibilities:

- connect to provider-specific services
- handle storage, auth, or SDK behavior
- support exchange-specific account and execution workflows

Main code:

- `agents/backpack_execution/`
- `agents/drift_execution/`
- `agents/exchange_connections/`
- provider-specific integration helpers

## How The Pieces Fit Together

The current backend is built around one adaptive agent runtime rather than many separate runtime binaries.

The main interaction pattern is:

1. request enters through REST, SSE, or WebSocket
2. auth and request context are resolved
3. the agent or market service runs
4. tools and integrations are called when needed
5. the backend returns structured responses or stream events

## Related Documentation

- [Project Overview](../project/index.md)
- [Agents Index](../../agents/index.md)
- [WebSocket Index](../../websocket/index.md)
- [API Index](../../api/index.md)
