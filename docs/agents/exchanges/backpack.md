# Backpack Agent Behavior

Backpack is the most complete exchange integration in the current agent runtime.

## Identity Model

Backpack inside the agent uses two layers:

- wallet-auth JWT for app-level ownership
- encrypted Backpack API credentials for Backpack account access

The agent does not treat Backpack API credentials as the primary user identity. It treats them as exchange access owned by the authenticated user.

## Visual Model

```text
wallet auth
  -> JWT user identity
  -> exchange connection lookup
  -> decrypt stored Backpack credentials
  -> read-only account tools or gated execution tools
```

## Current Agent Surface

Backpack currently supports:

- read-only account access
- balances and collateral
- open orders
- order, fill, and position history
- live order placement and cancellation

## Current Gates

Backpack execution is still intentionally gated:

- global gate from backend settings
- per-request gate from frontend/runtime state

This lets the agent discuss or plan execution without always being allowed to place live orders.

## What The Agent Needs To Know

From the agent point of view:

- Backpack is account-aware
- Backpack has stored per-user credentials
- Backpack can support both read-only and live execution behavior
- Backpack execution should respect auth-derived ownership and execution gates

## When To Read Integration Docs

Use the Backpack integration docs when you need:

- API key storage behavior
- encryption at rest
- exchange connection CRUD endpoints
- smoke tests or environment variables

Related docs:

- [Backpack Integration Index](../../integrations/backpack/index.md)
- [Backpack API Key Flow and Storage](../../integrations/backpack/api-key-flow-and-storage.md)
