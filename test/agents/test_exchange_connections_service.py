import base64

from agents.exchange_connections.database import (
    ExchangeConnectionsDatabase,
)
from agents.exchange_connections.service import ExchangeConnectionService


def _master_key() -> str:
    return base64.b64encode(bytes(range(32))).decode("utf-8")


def test_exchange_connection_service_encrypts_and_lists_records(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "agents.exchange_connections.crypto.settings.EXCHANGE_CREDENTIALS_MASTER_KEY",
        _master_key(),
    )

    db = ExchangeConnectionsDatabase(str(tmp_path / "exchange_connections.json"))
    service = ExchangeConnectionService(db=db)

    created = service.create_connection(
        user_id="user-1",
        exchange="backpack",
        label="Main Backpack",
        api_key="public-key-1234",
        api_secret="secret-key-xyz",
        trading_enabled=True,
        read_only=False,
        is_active=True,
    )

    assert created["user_id"] == "user-1"
    assert created["exchange"] == "backpack"
    assert created["last4"] == "1234"
    assert "api_secret" not in created

    stored = db.get_connection(created["id"])
    assert stored is not None
    assert stored["api_key_ciphertext"] != "public-key-1234"
    assert stored["api_secret_ciphertext"] != "secret-key-xyz"

    listed = service.list_connections(user_id="user-1")
    assert len(listed) == 1
    assert listed[0]["id"] == created["id"]
    assert listed[0]["label"] == "Main Backpack"

    credentials = service.get_active_credentials(user_id="user-1", exchange="backpack")
    assert credentials is not None
    assert credentials["api_key"] == "public-key-1234"
    assert credentials["api_secret"] == "secret-key-xyz"


def test_exchange_connection_service_only_keeps_one_active_connection(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "agents.exchange_connections.crypto.settings.EXCHANGE_CREDENTIALS_MASTER_KEY",
        _master_key(),
    )

    db = ExchangeConnectionsDatabase(str(tmp_path / "exchange_connections.json"))
    service = ExchangeConnectionService(db=db)

    first = service.create_connection(
        user_id="user-1",
        exchange="backpack",
        label="First",
        api_key="first-key-1111",
        api_secret="first-secret",
        is_active=True,
    )
    second = service.create_connection(
        user_id="user-1",
        exchange="backpack",
        label="Second",
        api_key="second-key-2222",
        api_secret="second-secret",
        is_active=True,
    )

    records = {item["id"]: item for item in service.list_connections(user_id="user-1")}
    assert records[first["id"]]["is_active"] is False
    assert records[second["id"]]["is_active"] is True
