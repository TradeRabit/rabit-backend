# Drift Auth Wallet And Execution Wallet

## Purpose

This document defines the recommended product and technical model for handling:
- the wallet used to log into Rabit
- the wallet used to execute Drift actions
- what happens when those wallets are the same
- what happens when those wallets are different

This is written for both:
- frontend mobile implementation
- backend ownership and execution design

## Core Terms

### Auth wallet

The `auth wallet` is the wallet used to sign in to Rabit.

It is used for:
- user authentication
- deriving `user_id`
- proving account ownership inside the app

Current identity shape:

```json
{
  "user_id": "wallet:<auth_wallet_address>"
}
```

### Execution wallet

The `execution wallet` is the wallet or authority intended to execute Drift actions.

It is used for:
- future Drift order execution
- future submission of signed Drift transactions
- future delegate or signer-based automation

## Recommended Product Direction

Recommended rollout for Rabit:

### Phase 1: same wallet only

For the first live Drift execution release:
- require `auth wallet == execution wallet`
- do not support separate execution wallets yet

Reason:
- simplest frontend UX
- clearest ownership model
- least confusing for mobile users
- easiest backend authorization story

### Phase 2: linked execution wallet

After same-wallet execution is stable:
- support `auth wallet != execution wallet`
- require explicit wallet linking
- treat this as an advanced mode

Reason:
- supports power users
- supports dedicated trading wallets
- avoids forcing casual users into a more complex flow

### Phase 3: delegated or automated execution

Only after Phase 2 is stable:
- add delegated signer or another automation model
- keep execution guardrails and audit logging mandatory

## Why This Is Recommended

This recommendation balances:
- mobile UX simplicity
- security clarity
- future automation needs

If separate wallets are supported too early:
- frontend becomes harder to explain
- user ownership becomes less obvious
- backend authorization gets more complex before execution is even stable

## Same Wallet Flow

This is the recommended `v1` flow.

### Frontend flow

1. user connects wallet
2. user signs login challenge
3. backend issues JWT
4. frontend marks wallet as both:
   - auth wallet
   - execution wallet
5. Drift execution can only proceed from this wallet identity

### Backend interpretation

Backend derives:
- `auth_wallet_address`
- `user_id = wallet:<auth_wallet_address>`

Backend also treats:
- `execution_wallet_address = auth_wallet_address`

### UX recommendation

Show a simple status like:

```text
Login wallet: 9abc...1234
Drift execution wallet: same as login wallet
Status: ready
```

## Different Wallet Flow

This is the recommended `v2` advanced flow.

### Rule

If:

```text
auth wallet != execution wallet
```

then backend must not trust the execution wallet address just because the frontend sent it.

The execution wallet must also prove control by signing a backend challenge.

### Required linking flow

1. user logs in with auth wallet
2. user chooses a different Drift execution wallet
3. backend creates a linking challenge
4. execution wallet signs that challenge
5. backend verifies the signature
6. backend stores a verified link:
   - auth wallet A
   - execution wallet B
7. frontend can now show the execution wallet as linked

### Why linking is required

Without linking, a user could claim:
- someone else's execution wallet
- a wallet they do not control

That would break both:
- security
- user ownership guarantees

## Recommended Frontend States

For mobile, the cleanest UI model is:

1. `auth_wallet_connected`
2. `execution_wallet_mode`
   - `same_wallet`
   - `linked_wallet`
3. `execution_wallet_status`
   - `not_set`
   - `pending_verification`
   - `linked`
   - `failed`
4. `drift_execution_enabled`

### Recommended display

For normal users:

```text
Login wallet: 9abc...1234
Execution wallet: same as login wallet
Drift execution: disabled
```

For advanced users:

```text
Login wallet: 9abc...1234
Execution wallet: 7xyz...7890
Execution wallet status: linked and verified
Drift execution: enabled
```

## Recommended Backend Data Model

The backend should treat auth and execution identity separately.

Suggested stored shape:

```json
{
  "user_id": "wallet:<auth_wallet_address>",
  "auth_wallet_address": "<auth_wallet_address>",
  "drift_execution_wallet": {
    "mode": "same_wallet",
    "wallet_address": "<execution_wallet_address>",
    "verified": true,
    "linked_at": "2026-04-18T10:00:00Z"
  }
}
```

For linked wallets:

```json
{
  "user_id": "wallet:<auth_wallet_address>",
  "auth_wallet_address": "<auth_wallet_address>",
  "drift_execution_wallet": {
    "mode": "linked_wallet",
    "wallet_address": "<different_execution_wallet_address>",
    "verified": true,
    "linked_at": "2026-04-18T10:00:00Z"
  }
}
```

## Security Rules

The backend should always enforce:

1. auth wallet identity must come from verified wallet-auth JWT
2. execution wallet must be:
   - the same wallet as auth wallet, or
   - a separately verified linked wallet
3. execution wallet address from client input is never trusted by itself
4. enabling execution is separate from verifying wallet ownership

Important distinction:
- wallet ownership verification
- execution permission

These are related, but not the same thing.

Even a verified execution wallet should still respect:
- `DRIFT_EXECUTION_ENABLED`
- request-level execution gate
- future risk controls
- future approval requirements

## Recommendation For Current Rabit State

Right now, the best practical decision is:

### Recommended now

- `v1`: same wallet only
- document linked wallet as a future advanced mode
- do not implement backend-held signer first

### Why

- Drift execution is not live yet
- read-only Drift already works
- the biggest risk now is overcomplicating execution before the signer path is chosen
- same-wallet mode is the cleanest bridge from today's wallet auth to tomorrow's execution

## Suggested API Evolution

### Phase 1

No linking API is required yet.

Backend can assume:

```text
execution wallet = auth wallet
```

Current backend helper endpoint:
- `GET /api/drift/execution-wallet`

This endpoint returns the resolved Drift execution-wallet status for the authenticated user.

Current same-wallet execution bridge endpoints:
- `POST /api/drift/execution/prepare`
- `GET /api/drift/execution/{execution_id}`
- `POST /api/drift/execution/submit`

Current meaning:
- `prepare` validates ownership, builds one unsigned same-wallet Drift transaction payload, and stores one execution intent record
- `status` returns the current record state for the same authenticated user
- `submit` sends an already signed transaction to Solana RPC

Current `prepare` output now includes:
- unsigned versioned transaction bytes
- unsigned message bytes
- recent blockhash metadata
- derived Drift account public keys

Important note:
- the backend still does not sign the transaction
- mobile or another signing layer still needs to replace the null signer with a real wallet signature before `submit`

### Phase 2

Add explicit linking endpoints such as:
- `POST /api/drift/execution-wallet/link/nonce`
- `POST /api/drift/execution-wallet/link/verify`
- `GET /api/drift/execution-wallet`
- `DELETE /api/drift/execution-wallet`

## Decision Summary

Recommended final stance:

- for `v1`, use the same wallet for auth and Drift execution
- only support different execution wallets after adding explicit wallet-link verification
- treat different-wallet mode as advanced
- keep backend-held signer as a later decision, not the default first step

## Current Implementation Status

Implemented now:
- wallet-auth JWT identity
- same-wallet-only Drift execution-wallet resolution
- `GET /api/drift/execution-wallet`
- `POST /api/drift/execution/prepare`
- `GET /api/drift/execution/{execution_id}`
- `POST /api/drift/execution/submit`
- same-wallet unsigned Drift transaction builder for perp orders
- Drift account context tool also exposes resolved execution-wallet state

Not implemented yet:
- different execution wallet linking
- live Drift order execution
- delegated signer flow
- linked-wallet execution
- advanced risk controls around prepared transactions

## Related Documents

Use this document together with:
- [Drift Wallet Flow and Storage](./wallet-flow-and-storage.md)
- [Drift Signer Architecture](./signer-architecture.md)
- [Drift Read-Only Setup](./read-only-setup.md)
