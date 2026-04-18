# Drift Signer Architecture

## Overview

This document defines the missing design layer for Drift live execution:
- who signs Drift transactions
- where signer authority lives
- what the backend stores
- what the mobile app signs
- which approach is recommended for Rabit

This exists because Drift is not a Backpack-style API key system.
Before implementing Drift live execution or signer storage, the project needs a clear signer model.

## Problem

For Backpack, the backend can store:
- `api_key`
- `api_secret`

For Drift, there is no equivalent API key pair in the current architecture.
Execution depends on Solana signing authority.

That means the core question is:

`who signs the Drift transaction?`

There are three realistic answers:
- the mobile wallet signs
- a delegated signer signs
- the backend stores and uses a signer directly

## Goals

The signer model should:
- work well for mobile
- preserve clear user ownership
- avoid unnecessary custody risk
- support future agent-driven execution
- allow safe step-by-step rollout

## Option 1: Client-Side Wallet Signing

### Flow

1. user authenticates with wallet
2. agent/backend prepares Drift execution intent
3. backend returns transaction payload or signing request
4. mobile wallet signs on-device
5. mobile app submits signed transaction

### Pros

- most non-custodial
- backend does not store a Drift signer secret
- easiest security story
- easiest to justify for early production

### Cons

- more round-trips for every execution
- weaker UX for fast automation
- harder to support autonomous agent actions
- backend cannot execute while user is offline

### Best fit

- safest MVP
- ideal when the product wants execution confirmation on every trade

## Option 2: Delegated Signer

### Flow

1. user authenticates with wallet
2. user authorizes a delegate or limited execution authority
3. backend stores delegate reference or encrypted delegate secret
4. agent/backend executes within delegated permissions

### Pros

- better automation than client-side signing
- cleaner separation between user identity and execution authority
- can support scoped permissions
- better long-term design than storing the primary signer directly

### Cons

- more protocol/product complexity
- requires careful permission design
- exact implementation depends on Drift and surrounding wallet/account model

### Best fit

- best long-term automation path
- strongest candidate if Rabit wants agent-driven execution with guardrails

## Option 3: Backend-Held Signer

### Flow

1. user authenticates with wallet
2. user provides signer secret to backend
3. backend encrypts and stores signer secret
4. backend decrypts in memory when executing Drift transactions

### Pros

- easiest automation
- easiest backend execution path
- simplest implementation from a pure engineering perspective

### Cons

- highest custody risk
- hardest security burden
- worst blast radius if backend is compromised
- difficult to justify unless the product explicitly chooses custodial behavior

### Best fit

- only if full custodial automation is a deliberate business decision

## Recommended Direction For Rabit

Current recommendation:

### Phase 1

Use `client-side wallet signing`.

Reason:
- matches mobile-first development
- keeps user custody on-device
- avoids premature signer storage
- lets the team ship Drift execution intent flow before committing to custody

### Phase 2

Evaluate `delegated signer` support if automation becomes a core feature.

Reason:
- better than storing the main signer directly
- enables automation with clearer boundaries
- aligns better with agent-driven execution than client-only signing

### Avoid For Now

Do not implement backend-held primary signer storage yet.

Reason:
- too much security burden too early
- not necessary for current stage
- easy to add later, hard to safely remove once relied upon

## What Should Be Implemented Next

Before real Drift execution tools, the backend should implement:

1. `execution intent generation`
2. `transaction payload preparation`
3. `mobile signing handoff format`
4. `signed transaction submit/confirm flow`
5. `execution audit log`

This means the next practical Drift feature is not secret storage.
It is a wallet-sign execution bridge.

## Storage Implications

### If using client-side wallet signing

Backend stores:
- wallet-derived `user_id`
- execution preferences
- audit logs
- optional Drift subaccount metadata

Backend does not store:
- private signer secret

### If using delegated signer

Backend may store:
- delegate metadata
- delegate status
- possibly encrypted delegate signer secret if the delegate is backend-controlled

### If using backend-held signer

Backend must store:
- encrypted signer secret
- rotation metadata
- access logs
- revocation metadata

## Security Model

### Minimum safe baseline

No matter which option is chosen:
- user identity should come from wallet-auth JWT
- ownership should be auth-derived, not client-provided
- execution should respect `DRIFT_EXECUTION_ENABLED`
- every live execution path should be logged

### Additional requirements for signer storage

If Drift signer secrets are ever stored:
- encrypt at rest
- decrypt only in memory
- separate key management from stored ciphertext
- add audit logs for every access
- add rotation and revocation flow

## Suggested API Evolution

### Phase 1: wallet-sign execution

Possible future endpoints:
- `POST /api/drift/execution/prepare`
- `POST /api/drift/execution/submit`
- `GET /api/drift/execution/{id}`

### Phase 2: delegated execution

Possible future endpoints:
- `POST /api/drift/delegates`
- `GET /api/drift/delegates`
- `DELETE /api/drift/delegates/{id}`

## Decision Summary

For Rabit today:
- identity: wallet auth
- signer strategy: client-side wallet signing first
- future automation: delegated signer if needed
- avoid: backend-held primary signer storage for now

## Relation To Existing Docs

This document extends:
- `docs/integrations/drift/wallet-flow-and-storage.md`

Use that document for:
- current implemented state
- auth flow
- smoke test

Use this document for:
- signer strategy decision
- execution architecture direction
- future implementation phases
