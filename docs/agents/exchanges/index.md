# Agent Exchange Behavior

This section explains how each exchange changes the agent runtime.

It is intentionally short and agent-facing:

- what identity the agent relies on
- what tools exist
- what execution model is active
- what is still intentionally unsupported

## Documents

- [Backpack](./backpack.md)
- [Drift](./drift.md)
- [Market-Data-Only Sources](./market-data-sources.md)

## Quick Comparison

| Area | Backpack | Drift | Market-Data-Only Sources |
|---|---|---|---|
| App identity | Wallet-auth JWT | Wallet-auth JWT | Usually none at the account layer |
| Exchange authority | Encrypted API key + secret | Same-wallet signer flow for execution prep | No per-user exchange authority |
| Read-only account tools | Yes | Yes | No |
| Execution support | Yes, gated | Prepare/submit bridge, same-wallet only | No |
| Primary detail docs | `integrations/backpack/` | `integrations/drift/` | `websocket/` and market-data docs |

## How To Use This Section

Use these pages first if you want a quick answer to:

- what the agent can do on this exchange
- what auth model it expects
- why one exchange has a different tool surface than another

If you need SDK, storage, or provider setup detail, continue into [Integrations](../../integrations/index.md).
