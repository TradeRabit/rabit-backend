# Backpack WebSocket Integration

This document explains how Backpack market data is used in the backend WebSocket layer.

## Scope

This integration is for public market-data streams and TradingView-related data flows.

It is not the same as:

- authenticated Backpack account credentials
- Backpack order execution
- per-user Backpack API key storage

For those topics, use:
- [Backpack Integration Index](../../integrations/backpack/index.md)

## Current Role in the Backend

Backpack is used as one of the market-data sources for:

- real-time prices
- symbol-level ticker updates
- frontend-facing market streams
- charting and TradingView support

## Main Characteristics

- transport: WebSocket
- exchange format: `BASE_QUOTE`, for example `SOL_USDC`
- supported use cases: price subscriptions, ticker updates, TradingView support

## Related Code Areas

- `ws/backpack/`
- `ws/services/`
- `ws/handlers/`

## Related Documentation

- [WebSocket Index](../index.md)
- [Backpack WebSocket Quickstart](./quickstart.md)
- [Backpack TradingView Quickstart](./tradingview-quickstart.md)
- [Tools Index](../../tools/index.md)
