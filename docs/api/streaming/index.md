# Streaming API

This group covers transport-level streaming APIs exposed directly from the backend.

## Endpoints

### `GET /api/agent/chat/stream`

This is documented in the [Agent API](../agent/index.md) because it is an SSE chat route rather than a WebSocket market-data route.

### `WS /api/ws/prices`

Opens a WebSocket connection for real-time price updates.

Transport:

- WebSocket

Client behavior:

- connect to `/api/ws/prices`
- receive JSON price updates
- optionally send `ping` and receive `pong`

Typical pushed message fields:

- `symbol`
- `price`
- `change_24h`
- `volume_24h`
- `timestamp`

## Notes

- This is a broadcast-style stream backed by the backend market handler.
- Exchange-specific stream behavior still lives under [WebSocket and Market Data](../../websocket/index.md).

## Related Documentation

- [WebSocket Overview](../../websocket/overview.md)
- [WebSocket and Market Data](../../websocket/index.md)
