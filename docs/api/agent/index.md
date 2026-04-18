# Agent API

This group covers multimodal uploads, normal chat, and SSE streaming chat.

## Endpoints

### `POST /api/agent/uploads`

Uploads a temporary image or PDF attachment for later agent use.

Input:

- multipart form upload field: `file`

Response model:

- `AgentUploadResponse`

Main response fields:

- `file_id`
- `filename`
- `content_type`
- `kind`
- `size_bytes`
- `expires_at`

### `DELETE /api/agent/uploads/{file_id}`

Deletes a temporary uploaded attachment.

Response model:

- `AgentUploadDeleteResponse`

### `POST /api/agent/chat`

Runs a normal agent response with optional attachments and runtime context.

Request model:

- `AgentChatRequest`

Main request fields:

- `message`
- `scope_id`
- `user_id`
- `conversation_style`
- `trading_style`
- `market_context`
- `backpack_execution`
- `drift_execution`
- `attachment_ids`

Response model:

- `AgentChatResponse`

Main response fields:

- `response`
- `scope_id`
- `user_id`
- `conversation_style`
- `trading_style`
- `market_context`
- `backpack_execution`
- `drift_execution`
- `attachment_ids`
- `intent`
- `session_cost`

Notes:

- `session_cost` is only populated when OpenRouter is enabled and the request includes a stable `scope_id`.
- The value is an accumulated summary for the whole chat/session scope, not only the latest assistant turn.

### `POST /api/agent/chat/stream`

Streams agent output over SSE.

Request model:

- `AgentChatRequest`

Response type:

- `text/event-stream`

Main event names:

- `thinking_summary`
- `assistant_delta`
- `plan`
- `hint`
- `error`
- `done`

Notes:

- The final `done` event may include `session_cost` using the same accumulated scope summary returned by normal chat.

## Auth Notes

- Bearer auth is optional at the transport level but strongly recommended.
- When auth is present, the backend can derive user identity and ownership more safely than relying only on request `user_id`.

## Related Documentation

- [Agent Platform](../../features/agent/index.md)
- [Intent Routing](../../agents/routing/intent-routing.md)
- [Wallet Auth](../../agents/auth/wallet-auth.md)
