# Drift Read-Only Setup

## Purpose

This document explains how to enable the `Drift` authenticated read-only tools in this backend.

These tools currently cover:
- `drift_get_account_context`
- `drift_get_account_snapshot`
- `drift_get_balances`
- `drift_get_collateral`
- `drift_get_open_orders`
- `drift_get_order_history`
- `drift_get_fill_history`
- `drift_get_positions`
- `drift_get_open_positions`
- `drift_get_position_history`

This setup is for `read-only account visibility`, not live order execution.

## Why This Is Separate

The main backend does not need the full Drift Python SDK stack unless you want private Drift account reads.

To avoid forcing every developer to install the Drift stack:
- the core backend stays lightweight
- Drift account reads use optional dependencies
- Drift execution remains a separate future step

## Install

From the repo root:

```bash
python -m pip install -r requirements-drift-readonly.txt
```

## Verified Environment

The current read-only Drift path was verified in this repo with:

- Python `3.11`
- Windows
- `driftpy==0.8.89`
- `anchorpy==0.21.0`
- `solana==0.36.11`
- `solders==0.26.0`

## Important Note About `zstandard`

`driftpy` declares a dependency on `zstandard==0.18.0`.

In this environment, installing that exact version attempted to build a native extension and failed without:
- Microsoft Visual C++ Build Tools

For the current Rabit `read-only Drift account tools`, the import and live read path worked without forcing `zstandard==0.18.0`, so `requirements-drift-readonly.txt` intentionally does not pin it.

If your environment or a future Drift SDK path requires it, you may need to install:
- Microsoft C++ Build Tools
- then retry the package install

## Pytest Compatibility Note

After installing `anchorpy`, pytest may try to load Anchor's legacy plugin path.

This repo includes a small compatibility shim:

- `pytest_xprocess.py` in the repository root

That shim exists only to keep pytest working normally with the currently installed package set.

## Required App Inputs

To use the private read-only Drift tools at runtime, the backend needs:

1. wallet-authenticated user identity
2. `user_id` shaped like `wallet:<solana_wallet_address>`
3. optional `sub_account_id`

No API key storage is needed for Drift read-only.

## Runtime Requirements

These values still matter:

```env
DRIFT_RPC_URL=https://api.mainnet-beta.solana.com
DRIFT_PROGRAM_ID=dRiftyHA39MWEi3m9aunc5MzRF1JYJjb5ciH7N27eNn
DRIFT_EXECUTION_ENABLED=false
```

For wallet auth:

```env
AUTH_JWT_SECRET=<jwt secret>
AUTH_JWT_ISSUER=rabit-backend
AUTH_JWT_AUDIENCE=rabit-mobile
WALLET_AUTH_NONCE_DB_PATH=data/wallet_auth_nonces.json
```

## What Was Verified

The current implementation was verified in two ways:

1. test suite

```bash
python -m pytest --basetemp .pytest_tmp test\tools\test_drift_readonly_tools.py test\agents\test_intent_router.py test\tools\test_backpack_tools.py test\tools\test_tool_gates.py -q
```

2. live read-only smoke call through the tool layer using a public wallet authority

Example verified result shape:

```json
{
  "classification": "private_account_read_only",
  "spot_balances_count": 4,
  "open_orders_count": 0,
  "open_positions_count": 0,
  "total_collateral": 30121332,
  "free_collateral": 30121332.0,
  "leverage": 0.0
}
```

## Current Limits

This setup still does `not` yet cover:
- `drift_place_order`
- `drift_cancel_order`

And for the new history tools:
- they scan recent transactions for the authenticated Drift user account
- they depend on Solana RPC quality much more than snapshot-style reads
- public RPC endpoints may rate-limit them

For reliable history reads, prefer a dedicated `DRIFT_RPC_URL`.

## Recommended Team Workflow

If a teammate only works on:
- general backend
- Backpack
- prompts
- frontend

they do not need to install the Drift SDK stack.

If a teammate works on:
- Drift private account tools
- Drift read-only testing
- Drift execution preparation

they should install:

```bash
python -m pip install -r requirements-drift-readonly.txt
```

## Next Step

Once this setup is stable for the team, the most natural next addition is:
- Drift live execution design and signer decision

The read-only surface is now much closer to Backpack, so the remaining major gap is execution architecture.
