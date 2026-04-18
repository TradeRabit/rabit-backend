# Rabit Documentation

This directory contains the maintained documentation for the Rabit backend.

The documentation is now split into two clear layers:

- Public documentation: setup, architecture, API behavior, features, integrations, and tools
- Internal documentation: plans, session logs, migration notes, and roadmap-style working documents

## How The Public Docs Are Split

- `features/`: product and capability overviews
- `agents/`: agent-facing runtime, auth, routing, and exchange behavior
- `integrations/`: provider-specific setup, storage, SDK, and auth detail
- `websocket/`: streaming and market-data ingestion behavior
- `api/`: route and request/response documentation
- `tools/`: tool-level operational behavior

## Start Here

- [Getting Started](./getting-started/index.md)
- [API](./api/index.md)
- [Architecture](./architecture/index.md)
- [Features](./features/index.md)
- [Integrations](./integrations/index.md)
- [WebSocket and Market Data](./websocket/index.md)
- [Agents](./agents/index.md)
- [Development](./development/index.md)
- [Tools](./tools/index.md)
- [Internal Notes](./internal/index.md)

## Recommended Reading Order

If you are new to the project:

1. [Getting Started](./getting-started/index.md)
2. [Features](./features/index.md)
3. [API](./api/index.md)
4. [Architecture](./architecture/index.md)

If you are integrating with the backend:

1. [API](./api/index.md)
2. [Integrations](./integrations/index.md)
3. [WebSocket and Market Data](./websocket/index.md)

If you are working on the backend codebase:

1. [Architecture](./architecture/index.md)
2. [Agents](./agents/index.md)
3. [Development](./development/index.md)
4. [Internal Notes](./internal/index.md)

## Documentation Conventions

- Public-facing docs use consistent English titles and kebab-case file names.
- Folder-level `index.md` files act as the entry point for each section.
- Historical implementation logs, plans, and roadmap material live under [`docs/internal`](./internal/index.md).
- `README.md` is the main portal. [`DOCS_INDEX.md`](./DOCS_INDEX.md) is the detailed inventory.

## Quick Links

- [REST API](./api/rest-api.md)
- [Authentication API](./api/auth/index.md)
- [Agent API](./api/agent/index.md)
- [Drift Execution API](./api/drift/index.md)
- [Python Reference](./api/python-reference.md)
- [Drift Integration Docs](./integrations/drift/index.md)
- [Backpack Integration Docs](./integrations/backpack/index.md)
- [OpenRouter Integration Docs](./integrations/openrouter/index.md)
- [Intent Routing](./agents/routing/intent-routing.md)
- [Wallet Auth](./agents/auth/wallet-auth.md)
- [Agent Exchange Behavior](./agents/exchanges/index.md)
- [Full Documentation Index](./DOCS_INDEX.md)
