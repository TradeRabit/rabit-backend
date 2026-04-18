# Models API

This group exposes the OpenRouter model catalog and local model-database operations.

## Endpoints

### `GET /api/openrouter/session-costs/{scope_id}`

Returns the accumulated OpenRouter usage summary for one chat/session scope.

Query params:

- `user_id` when bearer auth is not present

Response model:

- `OpenRouterSessionCostResponse`

Main response fields:

- `scope_id`
- `user_id`
- `total_calls`
- `total_input_tokens`
- `total_output_tokens`
- `total_tokens`
- `estimated_cost_usd`
- `model_ids`
- `phases`

### `GET /api/models`

Lists models with optional filtering.

Query params:

- `require_tools`
- `require_reasoning`
- `min_context`
- `max_input_price`
- `max_output_price`
- `provider`
- `enabled_only`
- `refresh`

Response model:

- `ModelsListResponse`

### `GET /api/models/stats`

Returns aggregate model statistics.

Response model:

- `ModelStatsResponse`

### `GET /api/models/{model_id}`

Returns one model by full path-like ID.

Response model:

- `ModelInfoResponse`

### `POST /api/models/toggle`

Enables or disables one model.

Request model:

- `ModelToggleRequest`

### `GET /api/models/providers`

Lists known providers.

### `GET /api/models/grouped`

Returns models grouped by provider.

Query params:

- `enabled_only`
- `require_tools`
- `require_reasoning`

### `GET /api/models/database/stats`

Returns local models database statistics.

### `POST /api/models/database/refresh`

Forces a refresh from OpenRouter.

### `DELETE /api/models/database/clear`

Clears the local models database.

## Related Documentation

- [OpenRouter Integration](../../integrations/openrouter/integration.md)
- [OpenRouter Models](../../integrations/openrouter/models.md)
- [OpenRouter Caching](../../integrations/openrouter/caching.md)
