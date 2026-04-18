# Features Overview

This document gives a high-level view of what the Rabit backend currently supports.

## Core Capabilities

### Agent Runtime

- single adaptive `TradingAgent`
- model-based intent routing
- tool-aware response generation
- SSE streaming for UI events

### Market Data

- real-time exchange-backed market feeds
- OHLC and charting support
- exchange-specific WebSocket integrations

### Execution

- Backpack authenticated reads and execution tools
- Drift read-only account tools
- Drift same-wallet execution preparation for mobile signing

### User State

- Mem0 long-term memory
- wallet-authenticated identity
- per-request market context
- per-request exchange execution gates

## Where to Read More

- [Features Index](../../features/index.md)
- [Exchange Execution](../../features/execution/index.md)
- [Memory and Context](../../features/memory/index.md)
- [Real-Time Market Data](../../features/market-data/index.md)
