# Drift Execution API

This group covers the current same-wallet Drift execution bridge.

## Endpoints

### `GET /api/drift/execution-wallet`

Returns the resolved Drift execution-wallet status for the authenticated user.

Headers:

- `Authorization: Bearer <token>`

Response model:

- `DriftExecutionWalletResponse`

Main fields:

- `mode`
- `auth_wallet_address`
- `execution_wallet_address`
- `verified`
- `same_wallet_required`
- `linked_wallet_supported`
- `backend_held_signer_enabled`

### `POST /api/drift/execution/prepare`

Prepares one same-wallet Drift execution request for client-side signing.

Headers:

- `Authorization: Bearer <token>`

Request model:

- `DriftExecutionPrepareRequest`

Main request fields:

- `sub_account_id`
- `market_type`
- `market_index`
- `symbol`
- `side`
- `order_type`
- `base_asset_amount`
- `price`
- `reduce_only`
- `post_only`
- `immediate_or_cancel`
- `client_order_id`

Response model:

- `DriftExecutionRecordResponse`

Important response fields:

- `execution_id`
- `status`
- `prepared_transaction`
- `requires_client_signature`
- `expires_at`

### `GET /api/drift/execution/{execution_id}`

Returns one owned execution request.

Headers:

- `Authorization: Bearer <token>`

Response model:

- `DriftExecutionRecordResponse`

### `POST /api/drift/execution/submit`

Submits a signed same-wallet Drift transaction.

Headers:

- `Authorization: Bearer <token>`

Request model:

- `DriftExecutionSubmitRequest`

Main request fields:

- `execution_id`
- `signed_transaction`
- `transaction_encoding`
- `skip_preflight`
- `max_retries`

Response model:

- `DriftExecutionSubmitResponse`

## Current Constraints

- same-wallet only
- v1 prepare currently supports `market_type='perp'`
- backend prepares unsigned payloads but does not hold the signer

## Related Documentation

- [Drift Auth and Execution Wallet](../../integrations/drift/auth-and-execution-wallet.md)
- [Drift Signer Architecture](../../integrations/drift/signer-architecture.md)
- [Drift Agent Behavior](../../agents/exchanges/drift.md)
