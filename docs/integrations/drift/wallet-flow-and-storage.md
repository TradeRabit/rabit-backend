# Drift Wallet Flow And Storage

## Overview

This document explains how Rabit currently models Drift access for mobile and multi-user usage.

Unlike Backpack:
- Drift does not naturally fit an API key plus secret storage model
- Drift is wallet-centric
- user identity should come from wallet auth
- future execution should use a wallet signer, delegated signer, or another explicit signing model

Focus areas:
- how mobile auth relates to Drift identity
- what the backend stores today
- what is not stored today
- how Drift execution should be thought about in development versus production

## Core Difference From Backpack

Backpack flow:
- app identity from wallet auth
- exchange access through Backpack API key plus secret
- credentials encrypted at rest

Drift flow:
- app identity from wallet auth
- exchange identity is the wallet itself, or a delegated signer model tied to that wallet
- there is no Drift API key storage path in the current backend

So the backend currently has:
- Drift execution gate
- wallet auth
- Drift read-only account tools
- no encrypted Drift signer storage yet
- no live Drift execution tool yet

## Current Architecture

Current Drift-related layers:

1. Mobile wallet auth
2. Drift execution policy gate
3. Drift read-only account and history tools
4. Drift market-data access through existing WebSocket infrastructure
5. future Drift signer or delegate storage layer

High-level flow today:

```text
mobile app
  -> wallet sign-in
  -> JWT bearer token
  -> agent request may include drift_execution.enabled
  -> backend derives authenticated wallet user
  -> backend can call Drift read-only account tools for balances, collateral, orders, positions, and recent history
  -> backend allows or blocks Drift execution path at policy level
  -> no live Drift order is placed because execution tools are not implemented yet
```

## Wallet Auth Flow

Current mobile-friendly auth flow:

1. `POST /api/auth/wallet/nonce`
2. mobile wallet signs the returned `message`
3. `POST /api/auth/wallet/verify`
4. backend verifies the signature against the Solana public key
5. backend issues a JWT bearer token
6. later requests may use `Authorization: Bearer <token>`

JWT identity shape:

```json
{
  "sub": "<wallet_address>",
  "wallet_address": "<wallet_address>",
  "user_id": "wallet:<wallet_address>"
}
```

For Drift, this wallet-linked identity is the natural starting point.

## What Is Stored Today

Current backend storage related to Drift:
- wallet auth nonce records
- JWT-derived wallet identity
- Drift execution gate state per request

Current backend does not store:
- Drift private key
- delegated Drift signer secret
- Drift subaccount signer secret
- encrypted Drift execution credential records

This is intentional for now.

## What Read-Only Drift Already Supports

The current backend read-only Drift surface already includes:
- `drift_get_account_context`
- `drift_get_account_snapshot`
- `drift_get_balances`
- `drift_get_collateral`
- `drift_get_open_orders`
- `drift_get_order_history`
- `drift_get_fill_history`
- `drift_get_positions`
- `drift_get_open_positions`
- `drift_get_position_history`

This means the current missing Drift capability is mostly `execution`, not `basic account visibility`.

Important note:
- the history tools depend more heavily on Solana RPC quality than snapshot tools
- public RPC endpoints may rate-limit history reads
- for reliable usage, prefer a dedicated `DRIFT_RPC_URL`

## Why There Is No Drift Credential Store Yet

Backpack needed encrypted key storage because it uses an API key plus secret model.

Drift is different:
- the natural authority is a Solana wallet
- if backend starts executing on behalf of a user, it needs a signer model
- signer custody is a much higher-stakes design choice than storing an exchange API key

That means a Drift storage design should only be added when one of these is chosen explicitly:

1. non-custodial mobile signing
2. delegated signer model
3. encrypted backend-held signer
4. another explicit authority/delegate pattern

Until that decision is made, adding a fake "Drift credential storage" layer would be misleading.

## Drift Execution Gate

Current Drift execution control is policy-only.

Global backend gate:
- `DRIFT_EXECUTION_ENABLED`

Request-level gate:
- `drift_execution.enabled`

Behavior:
- if either gate is off, live Drift execution is not allowed
- even if both gates are on, no real order can be placed yet because live Drift execution tools are not implemented

This is useful for:
- frontend state wiring
- prompt/runtime behavior
- future execution readiness

## Future Drift Storage Options

There are three realistic future directions.

### Option 1: Wallet signs on the client

Flow:
- user stays non-custodial
- mobile wallet signs execution payloads or transaction instructions
- backend coordinates but does not hold the signer secret

Pros:
- safest from custody perspective
- simplest secret story on the backend

Cons:
- harder UX for agent-driven execution
- more round-trips to the mobile wallet

### Option 2: Delegated signer model

Flow:
- user authorizes a delegate or execution authority
- backend holds or references a delegate signer
- execution scope can be limited

Pros:
- cleaner automation story
- safer than full primary-wallet custody if designed well

Cons:
- more protocol-specific complexity
- needs explicit product/security decision

### Option 3: Encrypted backend-held signer

Flow:
- user provides a signer secret
- backend encrypts and stores it
- backend decrypts in memory for execution

Pros:
- easiest automation path

Cons:
- highest custody and security burden
- should not be added casually

## Recommended Direction

For this codebase today:
- use wallet auth as the ownership/authentication layer
- keep Drift execution gate in place
- do not add Drift signer storage until execution architecture is chosen
- if automation is a real product requirement, prefer a delegate-oriented design over raw primary-wallet secret storage

## Drift Smoke Test

For development, a simple Drift smoke test script is available at:

`scripts/drift_smoke_test.py`

Modes:

- `public-only`
  - no private credentials required
  - checks Solana RPC health and Drift WebSocket handshake reachability
- `execution-disabled`
  - does not place orders
  - confirms whether the global Drift execution gate is disabled

Examples:

```bash
python scripts/drift_smoke_test.py --mode public-only
python scripts/drift_smoke_test.py --mode execution-disabled
```

## Environment Variables

Relevant Drift and auth variables:

```env
DRIFT_RPC_URL=https://api.mainnet-beta.solana.com
DRIFT_WS_URL=wss://data.api.drift.trade/ws
DRIFT_DLOB_WS_URL=wss://dlob.drift.trade/ws
DRIFT_EXECUTION_ENABLED=false

AUTH_JWT_SECRET=<jwt secret>
AUTH_JWT_ISSUER=rabit-backend
AUTH_JWT_AUDIENCE=rabit-mobile
WALLET_AUTH_NONCE_DB_PATH=data/wallet_auth_nonces.json
```

## Current Security Notes

Safe today:
- wallet identity can be derived from bearer auth
- Drift execution intent can be gated globally and per request
- Drift read-only account tools can use wallet-authenticated identity without storing exchange secrets
- no Drift signer secret is being stored yet

Still missing:
- real Drift execution tools
- explicit Drift signer model
- audit logs for future execution path
- production-grade authorization fully derived from auth on all protected routes

## Practical Next Step

The most practical next step is:

1. choose the Drift execution model explicitly
2. write the execution API contract for that model
3. only then implement `drift_place_order` and `drift_cancel_order`

Recommended order:
- first choose between client-side wallet signing, delegated signer, or backend-held signer
- then define request/response shapes for execution preparation and confirmation
- then add guardrails, audit logs, and approval behavior before enabling live trading

## Recommended Production Upgrade Path

1. Keep wallet auth as the identity base.
2. Choose the Drift signing model explicitly before adding signer storage.
3. If signer storage is ever added, encrypt it at rest and log access.
4. Prefer delegated or scoped authority over broad primary-wallet custody when possible.
5. Add full auth-derived ownership checks to every Drift execution path before enabling live orders.
