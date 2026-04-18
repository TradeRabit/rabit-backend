# Exchange Connections API

This group manages stored user exchange connections.

At the moment, the implemented connection family is Backpack.

## Endpoints

### `GET /api/execution-access`

Returns one frontend-friendly execution-access payload for both Backpack and Drift.

Purpose:

- let the frontend render one `execution access` surface
- hide the implementation difference between Backpack API credentials and Drift wallet/session authority
- expose whether each exchange is connected and whether live execution is currently ready

Behavior:

- requires either wallet-auth bearer token or an explicit `user_id`
- `backpack` is derived from the active stored Backpack connection
- `drift` is derived from the authenticated wallet execution status

Response model:

- `ExecutionAccessResponse`

### `POST /api/exchange-connections/backpack`

Creates a stored Backpack connection.

Request model:

- `ExchangeConnectionCreateRequest`

Main body fields:

- `user_id`
- `label`
- `api_key`
- `api_secret`
- `trading_enabled`
- `read_only`
- `is_active`

Response model:

- `ExchangeConnectionResponse`

### `GET /api/exchange-connections`

Lists exchange connections for one user.

Query params:

- `user_id`
- `exchange`

Response model:

- `ExchangeConnectionListResponse`

### `PATCH /api/exchange-connections/{connection_id}`

Updates non-secret metadata for a stored connection.

Request model:

- `ExchangeConnectionUpdateRequest`

Main body fields:

- `user_id`
- `label`
- `trading_enabled`
- `read_only`
- `is_active`

Response model:

- `ExchangeConnectionResponse`

### `DELETE /api/exchange-connections/{connection_id}`

Deletes one stored exchange connection.

Query params:

- `user_id`

Response model:

- `ExchangeConnectionDeleteResponse`

## Security Notes

- Stored secrets are encrypted at rest.
- Response payloads only return safe metadata, not raw secrets.
- Bearer auth should be used so ownership can be derived from verified identity.

## Related Documentation

- [Backpack API Key Flow and Storage](../../integrations/backpack/api-key-flow-and-storage.md)
- [Backpack Agent Behavior](../../agents/exchanges/backpack.md)
