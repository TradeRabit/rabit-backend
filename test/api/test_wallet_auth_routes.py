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


def create_test_client():
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def test_wallet_auth_endpoints_issue_token_and_me(monkeypatch, tmp_path):
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
    assert nonce_response.status_code == 200
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
    assert verify_response.status_code == 200
    token_payload = verify_response.json()
    assert token_payload["user_id"] == f"wallet:{wallet_address}"

    me_response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token_payload['access_token']}"},
    )
    assert me_response.status_code == 200
    assert me_response.json()["wallet_address"] == wallet_address
    assert me_response.json()["user_id"] == f"wallet:{wallet_address}"

    drift_wallet_response = client.get(
        "/api/drift/execution-wallet",
        headers={"Authorization": f"Bearer {token_payload['access_token']}"},
    )
    assert drift_wallet_response.status_code == 200
    drift_wallet = drift_wallet_response.json()
    assert drift_wallet["mode"] == "same_wallet"
    assert drift_wallet["auth_wallet_address"] == wallet_address
    assert drift_wallet["execution_wallet_address"] == wallet_address
    assert drift_wallet["verified"] is True
    assert drift_wallet["same_wallet_required"] is True
    assert drift_wallet["linked_wallet_supported"] is False


def test_drift_execution_wallet_requires_bearer_token():
    client = create_test_client()

    response = client.get("/api/drift/execution-wallet")

    assert response.status_code == 401
    assert response.json()["detail"] == "Missing bearer token."
