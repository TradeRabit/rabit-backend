# Authentication API

The backend currently uses wallet-based authentication for protected agent and exchange flows.

## Endpoints

### `POST /api/auth/wallet/nonce`

Creates a one-time wallet sign-in challenge.

Request model:

- `WalletAuthNonceRequest`

Required body fields:

- `wallet_address`

Response model:

- `WalletAuthNonceResponse`

Main response fields:

- `wallet_address`
- `nonce`
- `message`
- `issued_at`
- `expires_at`

### `POST /api/auth/wallet/verify`

Verifies the signed challenge and issues a JWT.

Request model:

- `WalletAuthVerifyRequest`

Required body fields:

- `wallet_address`
- `nonce`
- `signature`

Optional body fields:

- `signature_encoding`
- `message`

Response model:

- `WalletAuthVerifyResponse`

Main response fields:

- `access_token`
- `token_type`
- `expires_at`
- `user_id`
- `wallet_address`

### `GET /api/auth/me`

Returns the current authenticated wallet identity.

Headers:

- `Authorization: Bearer <token>`

Response model:

- `AuthMeResponse`

## Typical Flow

```text
mobile client
  -> POST /api/auth/wallet/nonce
  -> sign challenge
  -> POST /api/auth/wallet/verify
  -> store access_token
  -> call protected routes with bearer token
```

## Related Documentation

- [Wallet Auth](../../agents/auth/wallet-auth.md)
- [Drift Auth and Execution Wallet](../../integrations/drift/auth-and-execution-wallet.md)
- [Backpack API Key Flow and Storage](../../integrations/backpack/api-key-flow-and-storage.md)
