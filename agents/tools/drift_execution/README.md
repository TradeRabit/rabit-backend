# Drift Execution

Classification:
- account-linked read-only context tools live here now
- private wallet-linked read-only account tools live here now
- private wallet-linked history reads live here now
- live execution is still a separate future path

This package is the dedicated home for Drift-specific tools such as:

- authenticated wallet-linked request context reads
- account snapshot and margin reads
- open positions and open orders
- recent order, fill, and position-affecting history access
- live order execution and cancellation

The request-level execution gate is already implemented in the agent runtime, so
frontend can enable or disable Drift trade execution before live tools are added.

Current private read-only account tools depend on optional Python SDK packages:
- `driftpy`
- `anchorpy`
- `solders`
- `solana`

If those dependencies are not installed yet, the tools will fail with a clear setup error instead of silently pretending they worked.

Current Backpack-shape-compatible Drift read-only surface:
- `drift_get_balances`
- `drift_get_collateral`
- `drift_get_open_orders`
- `drift_get_order_history`
- `drift_get_fill_history`
- `drift_get_positions`
- `drift_get_position_history`

Additional Drift-specific read-only tools:
- `drift_get_account_context`
- `drift_get_account_snapshot`
- `drift_get_open_positions`
