# Memory API

This group exposes Mem0 health and user-memory CRUD/search behavior.

## Endpoints

### `GET /api/memory/health`

Checks whether Mem0 is enabled and reachable.

Response model:

- `MemoryHealthResponse`

### `GET /api/memory/search`

Searches one user's memories semantically.

Query params:

- `user_id`
- `query`
- `limit`

Response model:

- `MemoryListResponse`

### `GET /api/memory`

Lists all memories for one user.

Query params:

- `user_id`

Response model:

- `MemoryListResponse`

### `POST /api/memory`

Creates one user memory.

Request model:

- `MemoryCreateRequest`

Response model:

- `MemoryCreateResponse`

### `DELETE /api/memory/{memory_id}`

Deletes one memory by ID.

Query params:

- `user_id`

Response model:

- `MemoryDeleteResponse`

### `DELETE /api/memory`

Deletes all memories for one user.

Query params:

- `user_id`

Response model:

- `MemoryDeleteResponse`

## Notes

- These routes are user-scoped.
- Today they still take `user_id` explicitly.
- The safer long-term direction is auth-derived ownership for protected memory access as well.

## Related Documentation

- [Memory and Context](../../features/memory/index.md)
- [Mem0 Integration](../../integrations/mem0/integration.md)
