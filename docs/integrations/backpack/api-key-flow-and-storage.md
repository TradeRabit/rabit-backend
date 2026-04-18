# Backpack API Key Flow And Storage

## Overview

This document explains how Rabit currently handles Backpack API credentials for multi-user usage.

Focus areas:
- how mobile/frontend sends Backpack credentials
- how backend encrypts and stores them
- how ownership is enforced
- how agent tools retrieve and use the active credentials
- what is safe today and what still needs hardening before production

## Current Architecture

The Backpack credential path has four layers:

1. Wallet/mobile auth layer
2. Exchange connection storage layer
3. Backpack execution client layer
4. Agent tool layer

High-level flow:

```text
mobile app
  -> wallet sign-in
  -> JWT bearer token
  -> submit Backpack api_key + api_secret
  -> backend encrypts and stores credentials
  -> user enables active Backpack connection
  -> agent tool requests Backpack access
  -> backend resolves authenticated user
  -> backend loads active Backpack connection
  -> backend decrypts secret in memory
  -> Backpack client signs private API request
```

## Source Of Truth

### Frontend-provided values

The mobile app provides:
- `api_key`
- `api_secret`
- `label`
- `trading_enabled`
- `read_only`
- `is_active`

The wallet auth flow also starts from frontend-provided:
- `wallet_address`
- signed challenge `signature`

### Backend-generated values

The backend generates and owns:
- `user_id` from wallet JWT as `wallet:<wallet_address>`
- connection `id`
- encrypted credential ciphertext
- `last4`
- `fingerprint`
- `created_at`
- `updated_at`
- `last_used_at`

This means credentials are not stored as raw frontend JSON.

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

This is the identity that should own Backpack connections.

## Storage Flow

### Record creation

When the app creates a Backpack connection:

1. backend resolves `user_id`
2. backend validates `api_key` and `api_secret`
3. backend encrypts both values at the application layer
4. backend writes one JSON-backed record to `EXCHANGE_CONNECTIONS_DB_PATH`

Current storage fields:

```json
{
  "id": "uuid",
  "user_id": "wallet:<wallet_address>",
  "exchange": "backpack",
  "label": "Main Backpack",
  "api_key_ciphertext": "<encrypted>",
  "api_secret_ciphertext": "<encrypted>",
  "last4": "1234",
  "fingerprint": "abcd1234efgh5678",
  "trading_enabled": true,
  "read_only": false,
  "is_active": true,
  "created_at": "...",
  "updated_at": "...",
  "last_used_at": null,
  "revoked_at": null
}
```

### Encryption

At-rest encryption uses:
- `EXCHANGE_CREDENTIALS_MASTER_KEY`
- application-level symmetric encryption

Secrets are encrypted before being saved and only decrypted in memory when needed.

### Public-safe response shape

The API never returns raw Backpack secrets back to the frontend after storage.

Safe response fields:
- `id`
- `user_id`
- `exchange`
- `label`
- `last4`
- `fingerprint`
- `trading_enabled`
- `read_only`
- `is_active`
- timestamps

## Runtime Usage Flow

When an agent tool needs Backpack access:

1. runtime context provides the active `user_id`
2. Backpack tool asks exchange connection service for the active Backpack connection
3. service checks ownership by `user_id`
4. service decrypts `api_key` and `api_secret`
5. Backpack client is created with these credentials
6. request is signed and sent to Backpack private API

Tool priority order:

1. active user-specific Backpack connection
2. fallback to global env credentials only if no user context exists

This makes multi-user operation possible without forcing one shared API key for all users.

## Execution Guardrails

Backpack live execution is controlled by two gates:

1. global backend gate
   - `BACKPACK_EXECUTION_ENABLED`
2. request-level gate
   - `backpack_execution.enabled`

Live execution tools only run when both are enabled.

Read-only tools do not require the execution gate, but they still require valid Backpack credentials.

## API Endpoints

### Wallet auth

- `POST /api/auth/wallet/nonce`
- `POST /api/auth/wallet/verify`
- `GET /api/auth/me`

### Backpack connection CRUD

- `POST /api/exchange-connections/backpack`
- `GET /api/exchange-connections`
- `PATCH /api/exchange-connections/{connection_id}`
- `DELETE /api/exchange-connections/{connection_id}`

## Environment Variables

Required for Backpack connection storage:

```env
EXCHANGE_CONNECTIONS_DB_PATH=data/exchange_connections.json
EXCHANGE_CREDENTIALS_MASTER_KEY=<32-byte key encoded for app encryption>
```

Required for wallet auth:

```env
AUTH_JWT_SECRET=<jwt secret>
AUTH_JWT_ISSUER=rabit-backend
AUTH_JWT_AUDIENCE=rabit-mobile
AUTH_JWT_TTL_SECONDS=604800
WALLET_AUTH_NONCE_DB_PATH=data/wallet_auth_nonces.json
WALLET_AUTH_NONCE_TTL_SECONDS=300
```

Optional Backpack env fallback:

```env
BACKPACK_API_URL=https://api.backpack.exchange
BACKPACK_API_KEY=
BACKPACK_API_SECRET=
BACKPACK_EXECUTION_ENABLED=false
```

## Mobile App Flow

Recommended mobile sequence:

1. connect wallet
2. request nonce
3. sign message in wallet
4. verify signature and receive bearer token
5. store bearer token securely on device
6. call Backpack connection API with bearer token
7. later call agent chat and Backpack-backed tools with the same bearer token

## Smoke Test Script

For development, a simple Backpack smoke test script is available at:

`scripts/backpack_smoke_test.py`

Modes:

- `public-only`
  - no API key required
  - checks docs reachability and public Backpack endpoints like `/api/v1/time` and `/api/v1/ping`
- `private-readonly`
  - requires `BACKPACK_API_KEY` and `BACKPACK_API_SECRET`
  - checks private read-only endpoints such as balances, collateral, and open orders
- `execution-disabled`
  - does not place orders
  - confirms whether the global execution gate is disabled and whether credentials are present

Examples:

```bash
python scripts/backpack_smoke_test.py --mode public-only
python scripts/backpack_smoke_test.py --mode private-readonly
python scripts/backpack_smoke_test.py --mode execution-disabled
```

## Current Security Notes

Safe today:
- Backpack secrets are encrypted at rest
- Backpack secrets are not returned in API responses
- bearer auth can derive `user_id` as `wallet:<wallet_address>`
- exchange routes can reject mismatch between token identity and provided `user_id`

Still transitional:
- some routes still accept explicit `user_id` for backward compatibility
- production should move fully to auth-derived identity
- JSON-backed storage is acceptable for development, but production should eventually move to a stronger database or secret manager with audit support

## Recommended Production Upgrade Path

1. Stop accepting client-provided `user_id` on protected routes.
2. Require bearer auth for exchange connection routes and agent chat.
3. Move from JSON-backed storage to a proper database or secret manager.
4. Add audit logs for create, update, delete, and live execution actions.
5. Add key rotation and connection revocation flows.
