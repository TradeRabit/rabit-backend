# Drift WebSocket

This section documents Drift as a real-time market-data source in the backend.

## Current Role

In the WebSocket layer, Drift is used for:

- public market data
- perp-oriented price awareness
- exchange stream ingestion
- market context enrichment for analysis and monitoring

## Visual Flow

```text
Drift stream
  -> ws/drift/
  -> shared handlers and services
  -> normalized market data
  -> agent context, monitoring, or frontend consumers
```

## What It Is Not

This page is about public or stream-oriented Drift market data.

It is not the place for:

- Drift account read-only tools
- Drift execution preparation
- wallet auth and execution-wallet decisions

For those topics, use:

- [Drift Integration Index](../../integrations/drift/index.md)
- [Drift Agent Behavior](../../agents/exchanges/drift.md)

## Related Code Areas

- `ws/drift/`
- `ws/services/`
- `ws/handlers/`

## Related Documentation

- [WebSocket Overview](../overview.md)
- [Data Sources](../data-sources.md)
- [Drift Integration Index](../../integrations/drift/index.md)
