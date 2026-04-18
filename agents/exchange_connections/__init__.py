"""Encrypted storage and service helpers for user exchange connections."""

from .crypto import (
    ExchangeCredentialCryptoError,
    decrypt_secret,
    encrypt_secret,
)
from .database import (
    ExchangeConnectionsDatabase,
    get_exchange_connections_database,
)
from .service import (
    ExchangeConnectionNotFoundError,
    ExchangeConnectionOwnershipError,
    ExchangeConnectionService,
    get_exchange_connection_service,
)

__all__ = [
    "ExchangeCredentialCryptoError",
    "decrypt_secret",
    "encrypt_secret",
    "ExchangeConnectionsDatabase",
    "get_exchange_connections_database",
    "ExchangeConnectionNotFoundError",
    "ExchangeConnectionOwnershipError",
    "ExchangeConnectionService",
    "get_exchange_connection_service",
]
