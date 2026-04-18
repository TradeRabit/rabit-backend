# Exchange Execution

The backend currently supports two exchange execution models with different trust and custody assumptions.

## Backpack

Backpack uses exchange API credentials.

Current backend support:

- per-user encrypted credential storage
- read-only account tools
- order placement and cancellation tools
- request-level execution gating
- global backend execution gating

## Drift

Drift is wallet-based rather than API-key based.

Current backend support:

- same-wallet-only execution resolution
- same-wallet execution preparation for mobile signing
- signed transaction submission bridge
- read-only private account tools

Current non-goals:

- backend-held signer by default
- linked-wallet execution
- delegated signer flow

## Related Documentation

- [Backpack Integration](../../integrations/backpack/index.md)
- [Drift Integration](../../integrations/drift/index.md)
