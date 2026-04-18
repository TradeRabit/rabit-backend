# WebSocket and Market Data

This section covers real-time market data, streaming infrastructure, and exchange-specific WebSocket behavior.

## Documents

- [Overview](./overview.md)
- [Data Sources](./data-sources.md)
- [Trading Assets](./trading-assets.md)
- [Backpack WebSocket Docs](./backpack/index.md)
- [Drift WebSocket Docs](./drift/index.md)
- [Binance Market Data Docs](./binance/index.md)

## Why This Section Exists

Use `docs/websocket` for the streaming and market-ingestion side of the backend:

- exchange market feeds
- OHLC delivery
- source-specific stream behavior
- charting and TradingView-oriented data paths

This is intentionally different from:

- [Features](../features/index.md), which describe user-visible capabilities
- [Integrations](../integrations/index.md), which describe provider-specific setup, storage, SDK, and auth details

## Recommended Use

- Start here if you need to understand how prices, OHLC, and exchange streams enter the backend
- See [Integrations](../integrations/index.md) for non-streaming service integrations
