# Mobile Data Requirements

This document summarizes the kinds of backend data the mobile app expects.

## Main Data Categories

### Market Data

- current asset prices
- chart or OHLC data
- exchange-specific market context

### Agent Data

- chat responses
- SSE event stream updates
- plan and hint payloads

### User and Execution Data

- wallet-authenticated identity
- memory-related user data
- Backpack connection metadata
- Drift execution-wallet state

## Related Documentation

- [REST API](../../api/rest-api.md)
- [Memory and Context](../../features/memory/index.md)
- [Exchange Execution](../../features/execution/index.md)
