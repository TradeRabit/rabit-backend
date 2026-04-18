# Drift Agent Behavior

Drift is account-aware for read-only access, but its execution model is intentionally more conservative than Backpack.

## Identity Model

Drift currently uses:

- wallet-auth JWT for app-level identity
- the authenticated wallet as the current same-wallet execution identity

Unlike Backpack, Drift does not currently rely on stored API key credentials.

## Visual Model

```text
wallet auth
  -> JWT user identity
  -> same wallet becomes current execution identity
  -> Drift read-only account tools
  -> prepare unsigned execution payload
  -> mobile wallet signs
  -> backend submits signed transaction
```

## Current Agent Surface

Drift currently supports:

- account context lookup
- account snapshot and balances
- collateral
- open orders
- positions and open positions
- order, fill, and position history
- same-wallet execution prepare and submit bridge

## Current Execution Model

The current Drift execution path is:

- same-wallet only
- backend prepares unsigned execution payloads
- mobile or another signer signs the transaction
- backend submits the signed transaction

This is not the same as backend-held Backpack API credentials. Drift execution is still signer-sensitive and intentionally more cautious.

## What The Agent Needs To Know

From the agent point of view:

- Drift can read account state for the authenticated wallet user
- Drift execution is not fully autonomous
- same-wallet mode is the only active execution mode today
- different execution wallets are a future mode, not the default current path

## When To Read Integration Docs

Use the Drift integration docs when you need:

- signer architecture decisions
- same-wallet execution bridge details
- read-only SDK setup
- future linked-wallet or delegate plans

Related docs:

- [Drift Integration Index](../../integrations/drift/index.md)
- [Drift Auth and Execution Wallet](../../integrations/drift/auth-and-execution-wallet.md)
- [Drift Signer Architecture](../../integrations/drift/signer-architecture.md)
