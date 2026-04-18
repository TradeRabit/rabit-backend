# Wallet Auth

The backend currently uses wallet-based authentication as the main identity layer for protected agent and exchange flows.

## Current Flow

The mobile-friendly flow is:

1. `POST /api/auth/wallet/nonce`
2. the wallet signs the returned challenge message
3. `POST /api/auth/wallet/verify`
4. the backend verifies the signature against the wallet public key
5. the backend issues a JWT bearer token
6. later requests send `Authorization: Bearer <token>`

## Visual Flow

```text
mobile app
  -> connect wallet
  -> request nonce
  -> sign challenge
  -> verify signature
  -> receive JWT
  -> call agent and exchange routes with bearer token
```

## What The Agent Receives

After verification, the backend can derive:

- `wallet_address`
- `user_id` shaped like `wallet:<wallet_address>`
- authenticated ownership for protected routes

This matters because the agent runtime should not trust a client-provided `user_id` when identity can instead come from verified auth.

## Why This Matters For Agent Behavior

Wallet auth influences:

- memory ownership
- exchange connection ownership
- Backpack credential lookup
- Drift account-linked read-only tools
- Drift same-wallet execution preparation

In practice, the agent runtime becomes safer because execution and account reads can be tied to verified identity instead of loose request input.

## Exchange Differences

The same wallet-auth layer feeds both exchange families, but the exchange behavior is different:

- Backpack uses wallet auth for app identity, then per-user encrypted Backpack API credentials for exchange access
- Drift uses wallet auth as both the app identity base and the current same-wallet execution identity base

For those differences, see:

- [Backpack Agent Behavior](../exchanges/backpack.md)
- [Drift Agent Behavior](../exchanges/drift.md)

## Related Documentation

- [Agent Runtime Visual Guide](../runtime/visual-guide.md)
- [Backpack API Key Flow and Storage](../../integrations/backpack/api-key-flow-and-storage.md)
- [Drift Auth and Execution Wallet](../../integrations/drift/auth-and-execution-wallet.md)
