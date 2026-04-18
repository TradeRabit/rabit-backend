import base64

from fastapi import FastAPI
from fastapi.testclient import TestClient
from nacl.signing import SigningKey

from api.routes import router


ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def b58encode(raw: bytes) -> str:
    num = int.from_bytes(raw, "big")
    encoded = ""
    while num > 0:
        num, remainder = divmod(num, 58)
        encoded = ALPHABET[remainder] + encoded
    leading_zeros = len(raw) - len(raw.lstrip(b"\x00"))
    if not encoded and raw:
        encoded = "1"
    return "1" * leading_zeros + encoded


class DummyExchangeConnectionService:
    def list_connections(self, *, user_id, exchange=None):
        if exchange == "backpack":
            return [
                {
                    "id": "conn-1",
                    "user_id": user_id,
                    "exchange": "backpack",
                    "label": "Primary Backpack",
                    "last4": "1234",
                    "fingerprint": "abc123",
                    "trading_enabled": True,
                    "read_only": False,
                    "is_active": True,
                    "created_at": "2026-04-18T00:00:00+00:00",
                    "updated_at": "2026-04-18T00:00:00+00:00",
                    "last_used_at": None,
                    "revoked_at": None,
                }
            ]
        return []


def create_test_client():
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def build_wallet_auth_header(monkeypatch, tmp_path):
    monkeypatch.setattr("agents.auth.jwt_auth.settings.AUTH_JWT_SECRET", "test-jwt-secret")
    monkeypatch.setattr(
        "agents.auth.nonce_store.settings.WALLET_AUTH_NONCE_DB_PATH",
        str(tmp_path / "wallet_nonces.json"),
    )
    monkeypatch.setattr(
        "agents.auth.nonce_store.settings.WALLET_AUTH_NONCE_TTL_SECONDS",
        300,
    )

    signing_key = SigningKey.generate()
    wallet_address = b58encode(bytes(signing_key.verify_key))
    client = create_test_client()

    nonce_response = client.post(
        "/api/auth/wallet/nonce",
        json={"wallet_address": wallet_address},
    )
    challenge = nonce_response.json()
    signature = signing_key.sign(challenge["message"].encode("utf-8")).signature
    encoded_signature = base64.b64encode(signature).decode("utf-8")

    verify_response = client.post(
        "/api/auth/wallet/verify",
        json={
            "wallet_address": wallet_address,
            "nonce": challenge["nonce"],
            "signature": encoded_signature,
            "signature_encoding": "base64",
            "message": challenge["message"],
        },
    )
    token_payload = verify_response.json()
    return client, wallet_address, {"Authorization": f"Bearer {token_payload['access_token']}"}


def test_execution_access_status_combines_backpack_and_drift(monkeypatch, tmp_path):
    monkeypatch.setattr("api.routes.settings.BACKPACK_EXECUTION_ENABLED", True)
    monkeypatch.setattr("api.routes.settings.DRIFT_EXECUTION_ENABLED", True)
    monkeypatch.setattr("api.routes.get_exchange_connection_service", lambda: DummyExchangeConnectionService())

    client, wallet_address, headers = build_wallet_auth_header(monkeypatch, tmp_path)

    response = client.get("/api/execution-access", headers=headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["authenticated"] is True
    assert payload["user_id"] == f"wallet:{wallet_address}"

    backpack = payload["backpack"]
    assert backpack["exchange"] == "backpack"
    assert backpack["authority_type"] == "api_credential"
    assert backpack["connected"] is True
    assert backpack["execution_ready"] is True
    assert backpack["active_connection_id"] == "conn-1"

    drift = payload["drift"]
    assert drift["exchange"] == "drift"
    assert drift["authority_type"] == "wallet_session"
    assert drift["connected"] is True
    assert drift["execution_ready"] is True
    assert drift["mode"] == "same_wallet"
    assert drift["auth_wallet_address"] == wallet_address
    assert drift["execution_wallet_address"] == wallet_address


def test_execution_access_status_requires_identity():
    client = create_test_client()

    response = client.get("/api/execution-access")

    assert response.status_code == 401
    assert "required" in response.json()["detail"]
