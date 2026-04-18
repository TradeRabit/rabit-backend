"""JWT helpers for mobile wallet authentication."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict

import jwt

from config.settings import settings


class JWTAuthError(RuntimeError):
    """Raised when JWT creation or verification fails."""


def _require_secret() -> str:
    """Return configured JWT secret or raise."""
    secret = settings.AUTH_JWT_SECRET
    if not secret:
        raise JWTAuthError("AUTH_JWT_SECRET is not configured.")
    return secret


def issue_access_token(*, wallet_address: str) -> Dict[str, Any]:
    """Issue one bearer token for a verified wallet."""
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(seconds=settings.AUTH_JWT_TTL_SECONDS)
    user_id = f"wallet:{wallet_address}"
    payload = {
        "sub": wallet_address,
        "user_id": user_id,
        "wallet_address": wallet_address,
        "iss": settings.AUTH_JWT_ISSUER,
        "aud": settings.AUTH_JWT_AUDIENCE,
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
    }
    token = jwt.encode(payload, _require_secret(), algorithm="HS256")
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_at": expires_at.isoformat(),
        "user_id": user_id,
        "wallet_address": wallet_address,
    }


def verify_access_token(token: str) -> Dict[str, Any]:
    """Verify one bearer token and return claims."""
    try:
        payload = jwt.decode(
            token,
            _require_secret(),
            algorithms=["HS256"],
            audience=settings.AUTH_JWT_AUDIENCE,
            issuer=settings.AUTH_JWT_ISSUER,
        )
    except Exception as exc:  # pragma: no cover - library specific failure paths
        raise JWTAuthError("Invalid or expired access token.") from exc
    return payload
