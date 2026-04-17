# Agent Multimodal Upload Design

**Goal:** Add a full temporary upload pipeline so Rabit agents can accept images and PDF documents through the API, then pass them to Claude/OpenRouter as multimodal message content.

**Scope**
- Temporary file upload storage with TTL-based cleanup
- API endpoints for upload, chat, and delete
- Agent support for text + image + PDF attachments
- Claude SDK compatible content block formatting
- OpenRouter-compatible file/image input formatting through the same agent flow

**Architecture**
- Client uploads files to the backend first and receives a short-lived `file_id`.
- Chat requests send `message`, `scope_id`, and `attachments[file_id]`.
- The backend resolves each file reference into an internal attachment object and converts it into provider-compatible message content blocks.
- Conversation memory stores only text plus compact attachment summaries, not raw file bytes.

**Storage**
- Files are stored under `data/uploads/tmp/`.
- Metadata is persisted in a small JSON registry so API processes can resolve uploaded files across requests.
- Files expire automatically based on TTL and can also be deleted manually.

**Supported Inputs**
- Images: `image/jpeg`, `image/png`, `image/webp`
- Documents: `application/pdf`

**Message Formatting**
- Anthropic direct:
  - Images use `type: "image"` blocks with base64 source.
  - PDFs use `type: "document"` blocks with base64 source.
- OpenRouter:
  - Images use `type: "image_url"` with data URLs.
  - PDFs use `type: "file"` with `file.filename` + `file.fileData` data URL.

**Safety / Limits**
- Temporary storage only
- Default TTL: 1 hour
- Max file size: 10 MB
- File type validation by MIME + extension
- Cleanup on upload/chat/delete paths to avoid stale files

**Testing**
- Upload lifecycle tests
- Expiration / cleanup tests
- Multimodal message block conversion tests
- Chat endpoint tests with text-only and attachment-backed requests
