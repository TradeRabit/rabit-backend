"""Encryption helpers for storing exchange credentials at rest."""
from __future__ import annotations

import base64
import binascii
from typing import Optional

from nacl.secret import SecretBox

from config.settings import settings


class ExchangeCredentialCryptoError(RuntimeError):
    """Raised when exchange credential encryption is unavailable or invalid."""


def _decode_secretbox_key(raw: str) -> bytes:
    """Decode a 32-byte SecretBox key from base64, hex, or raw text."""
    value = raw.strip()
    if not value:
        raise ExchangeCredentialCryptoError(
            "EXCHANGE_CREDENTIALS_MASTER_KEY is not configured."
        )

    candidates = []
    try:
        candidates.append(bytes.fromhex(value))
    except ValueError:
        pass

    for decode_fn in (base64.b64decode, base64.urlsafe_b64decode):
        try:
            padded = value + "=" * ((4 - len(value) % 4) % 4)
            candidates.append(decode_fn(padded))
        except (binascii.Error, ValueError):
            continue

    candidates.append(value.encode("utf-8"))

    for candidate in candidates:
        if len(candidate) == SecretBox.KEY_SIZE:
            return candidate

    raise ExchangeCredentialCryptoError(
        "EXCHANGE_CREDENTIALS_MASTER_KEY must decode to exactly 32 bytes."
    )


def get_secret_box(master_key: Optional[str] = None) -> SecretBox:
    """Return a SecretBox from configured exchange master key."""
    return SecretBox(_decode_secretbox_key(master_key or settings.EXCHANGE_CREDENTIALS_MASTER_KEY))


def encrypt_secret(value: str, master_key: Optional[str] = None) -> str:
    """Encrypt a secret string for at-rest storage."""
    if not value:
        raise ExchangeCredentialCryptoError("Cannot encrypt an empty credential value.")
    box = get_secret_box(master_key)
    encrypted = box.encrypt(value.encode("utf-8"))
    return base64.b64encode(encrypted).decode("utf-8")


def decrypt_secret(ciphertext: str, master_key: Optional[str] = None) -> str:
    """Decrypt a stored secret string."""
    if not ciphertext:
        raise ExchangeCredentialCryptoError("Cannot decrypt an empty credential value.")
    box = get_secret_box(master_key)
    try:
        payload = base64.b64decode(ciphertext)
        plaintext = box.decrypt(payload)
    except Exception as exc:  # pragma: no cover - library-specific failure path
        raise ExchangeCredentialCryptoError(
            "Failed to decrypt exchange credential. Check master key configuration."
        ) from exc
    return plaintext.decode("utf-8")
