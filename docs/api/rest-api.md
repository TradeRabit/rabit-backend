# REST API Overview

The backend mounts its primary HTTP API under the `/api` prefix.

## Base URLs

- application root metadata: `/`
- OpenAPI Swagger UI: `/docs`
- ReDoc: `/redoc`
- main REST API: `/api/*`

## Endpoint Groups

| Group | Purpose | Docs |
|---|---|---|
| System | service health and platform metadata | [System](./system/index.md) |
| Auth | wallet-based sign-in and current identity | [Authentication](./auth/index.md) |
| Agent | uploads, chat, and SSE chat | [Agent](./agent/index.md) |
| Memory | Mem0-backed memory health and CRUD | [Memory](./memory/index.md) |
| Exchange Connections | Backpack credential storage and management | [Exchange Connections](./exchange-connections/index.md) |
| Drift | same-wallet execution wallet and prepare/submit flow | [Drift Execution](./drift/index.md) |
| Assets | asset lookup and OHLC data | [Assets and Chart Data](./assets/index.md) |
| Models | OpenRouter model catalog and local model-database operations | [Models](./models/index.md) |
| Streaming | WebSocket price stream | [Streaming](./streaming/index.md) |

## Auth Pattern

Protected routes use bearer auth when available:

- `Authorization: Bearer <jwt>`

The current wallet-auth flow is documented in:

- [Authentication](./auth/index.md)

## Notes

- Some routes still accept `user_id` in request input or query params for compatibility.
- The long-term direction is to derive ownership from verified auth rather than trust client-provided identity.
- Drift and Backpack do not use the same exchange authority model, so their endpoint families are documented separately.

## Source of Truth

For exact implementation behavior and Pydantic model names, inspect:

- `api/routes.py`
- `api/models.py`

## Related Documentation

- [Python Reference](./python-reference.md)
- [Features Index](../features/index.md)
- [Integrations Index](../integrations/index.md)
