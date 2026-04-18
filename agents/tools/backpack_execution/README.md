# Backpack Execution

This package now contains Backpack-specific tools for:

- balances and collateral reads
- open orders and order history
- fill and position history
- live order placement and cancellation

Important behavior:

- read-only Backpack account/history tools require Backpack API credentials
- live execution tools require Backpack API credentials
- live execution tools also require both:
  - backend global gate `BACKPACK_EXECUTION_ENABLED=true`
  - frontend request gate `backpack_execution.enabled=true`

This keeps read-only portfolio access available without forcing live execution on.
