# Market-Data-Only Sources

Not every market source in the backend behaves like an account-aware exchange inside the agent.

## Current Role

Some sources mainly support:

- prices
- OHLC
- charting
- metadata
- enrichment

They do not currently act like per-user exchange authorities for the agent.

## Examples

### Binance

Binance currently appears in the backend mainly as an OHLC and chart-oriented source.

The agent may benefit from Binance-backed chart data, but it does not treat Binance like a per-user execution surface.

### CoinGecko

CoinGecko is used for metadata and enrichment rather than account access or execution.

### Public Drift and Backpack market feeds

Even Drift and Backpack can appear in public market-data form through the WebSocket layer, separate from account-aware exchange behavior.

## Why This Matters

This distinction keeps the agent mental model cleaner:

- account-aware exchange behavior belongs in exchange-specific docs
- public market-data behavior belongs in WebSocket and market-data docs

## Related Documentation

- [WebSocket Index](../../websocket/index.md)
- [Real-Time Market Data](../../features/market-data/index.md)
