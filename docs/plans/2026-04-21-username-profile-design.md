# Username Profile Design

## Goal

Add editable per-user usernames to Rabit backend.

## Decision

- Store username in backend JSON storage keyed by `user_id`.
- Do not store username on-chain.
- Keep `user_id` as the stable auth identity.
- Allow username changes through authenticated API.

## Data Model

Each profile record stores:

- `user_id`
- `username`
- `created_at`
- `updated_at`

## API

- `GET /api/auth/me` returns `username` in addition to wallet identity.
- `PATCH /api/auth/me/username` updates the caller's username.

## Validation

- Username is required on update.
- Username must be trimmed and length-bounded.
- Username format stays ASCII-safe for frontend usage.

## Behavior

- Profiles are created lazily when a user first sets a username.
- Username can be changed any time by the authenticated owner.
- No JWT changes are required because username is mutable.
