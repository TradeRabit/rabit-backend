# Rabit Backend

Rabit Backend is the backend service for the Rabit trading assistant experience.

It combines:

- a FastAPI REST and streaming API surface
- one adaptive trading agent runtime
- exchange-aware execution flows for Backpack and Drift
- a local on-chain contract SDK layer for the deployed Rabit Solana program
- real-time market-data ingestion
- long-term memory and request-scoped context

## What This Backend Does

The current backend supports:

- agent chat with multimodal uploads
- SSE streaming for assistant text and UI events
- wallet-based authentication
- Backpack encrypted credential storage and gated execution
- Drift read-only account access and same-wallet execution preparation
- real-time and chart-oriented market-data flows
- OpenRouter model catalog management
- OpenRouter session-cost accumulation per chat scope
- backend-local contract artifacts, PDA helpers, account decoders, and instruction builders

## Quick Start

### 1. Create and activate a virtual environment

```bash
python -m venv venv
```

Windows:

```bash
venv\Scripts\activate
```

Linux or macOS:

```bash
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

If you want Drift read-only account tools, also install:

```bash
pip install -r requirements-drift-readonly.txt
```

That optional dependency set also enables the bundled Rabit on-chain contract SDK under `contract/`.

### 3. Configure environment variables

```bash
cp .env.example .env
```

Typical local values to review first:

- `ANTHROPIC_API_KEY` or OpenRouter configuration
- `AUTH_JWT_SECRET`
- `DRIFT_RPC_URL`
- `BACKPACK_API_URL`

### 4. Start the backend

```bash
python main.py
```

The default local server is:

- `http://localhost:8000`

## Main Entrypoints

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- API health: `http://localhost:8000/api/health`

## Documentation

The docs tree has been reorganized to make it easier to read quickly, especially for demos and hackathon judging.

Start here:

- [Documentation Portal](./docs/README.md)
- [Getting Started](./docs/getting-started/index.md)
- [Features](./docs/features/index.md)
- [API](./docs/api/index.md)
- [Agents](./docs/agents/index.md)
- [WebSocket and Market Data](./docs/websocket/index.md)
- [Integrations](./docs/integrations/index.md)
- [Architecture](./docs/architecture/index.md)
- [Full Documentation Index](./docs/DOCS_INDEX.md)

## Recommended Reading Paths

### For judges or reviewers

1. [Getting Started](./docs/getting-started/index.md)
2. [Features](./docs/features/index.md)
3. [Agents](./docs/agents/index.md)
4. [API](./docs/api/index.md)
5. [Architecture](./docs/architecture/index.md)

### For frontend or mobile integration

1. [API](./docs/api/index.md)
2. [Authentication API](./docs/api/auth/index.md)
3. [Agent API](./docs/api/agent/index.md)
4. [Drift Execution API](./docs/api/drift/index.md)
5. [Exchange Connections API](./docs/api/exchange-connections/index.md)

### For backend contributors

1. [Architecture](./docs/architecture/index.md)
2. [Agents](./docs/agents/index.md)
3. [Development](./docs/development/index.md)
4. [Integrations](./docs/integrations/index.md)

## Repository Structure

```text
rabit-backend/
  api/                FastAPI routes and request/response models
  agents/             agent runtime, routing, tools, auth, and execution helpers
  config/             application settings
  contract/           deployed Rabit program metadata, IDL, PDA helpers, and SDK layer
  docs/               maintained documentation
  scripts/            smoke tests and helper scripts
  test/               automated tests
  ws/                 websocket and market-data services
  main.py             FastAPI entry point
```

## On-Chain Contract Layer

The backend now ships with a dedicated `contract/` package that mirrors the deployed Rabit Solana program and gives backend code one local source of truth for on-chain interaction.

It includes:

- bundled IDL copied from the contract workspace
- devnet deployment metadata
- PDA derivation helpers
- manual account decoders for `PlatformConfig`, `SpendingProfile`, `DelegatedSigner`, `AiUsageRecord`, and `ModelRegistry`
- async RPC helpers for reading deployed accounts
- solders instruction builders for core Rabit program interactions

Main entrypoints:

- `contract.load_deployment("devnet")`
- `contract.load_idl()`
- `contract.get_rabit_contract_sdk()`

Environment overrides:

- `RABIT_CONTRACT_CLUSTER`
- `RABIT_CONTRACT_RPC_URL`
- `RABIT_CONTRACT_PROGRAM_ID`

## Key API Groups

The main API is mounted under `/api`.

Main endpoint families:

- `/api/auth/*`
- `/api/agent/*`
- `/api/memory/*`
- `/api/exchange-connections/*`
- `/api/drift/*`
- `/api/assets/*`
- `/api/models/*`
- `/api/ws/prices`

For the detailed API docs, use:

- [REST API Overview](./docs/api/rest-api.md)
- [Authentication API](./docs/api/auth/index.md)
- [Agent API](./docs/api/agent/index.md)

## Status Snapshot

### Backpack

- encrypted per-user exchange connection storage
- read-only account tools
- live execution tools with execution gates

### Drift

- wallet-auth-based identity
- read-only account tools
- same-wallet execution prepare and submit bridge
- no backend-held signer by default

## Development Notes

- Public documentation lives under `docs/`
- Historical plans, migration notes, and session logs live under `docs/internal/`
- Root `README.md` is the repo-level entry point, while `docs/README.md` is the documentation portal

## License

MIT
