from fastapi import FastAPI
from fastapi.testclient import TestClient
from nacl.signing import SigningKey
import jwt

from api.routes import router
from agents.user_profiles import get_user_profile_service


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


def test_authenticated_username_can_be_created_and_updated(monkeypatch, tmp_path):
    monkeypatch.setattr("api.routes.settings.AUTH_JWT_SECRET", "test-jwt-secret")

    service = get_user_profile_service(db_path=str(tmp_path / "user_profiles.json"))
    monkeypatch.setattr("api.routes.get_user_profile_service", lambda: service)

    signing_key = SigningKey.generate()
    wallet_address = b58encode(bytes(signing_key.verify_key))
    token = jwt.encode(
        {
            "sub": wallet_address,
            "user_id": f"wallet:{wallet_address}",
            "wallet_address": wallet_address,
            "iss": "rabit-backend",
            "aud": "rabit-mobile",
            "iat": 1,
            "exp": 4102444800,
        },
        "test-jwt-secret",
        algorithm="HS256",
    )

    client = create_test_client()

    me_response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_response.status_code == 200
    assert me_response.json()["username"] is None

    update_response = client.patch(
        "/api/auth/me/username",
        headers={"Authorization": f"Bearer {token}"},
        json={"username": "TraderOne"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["username"] == "TraderOne"

    me_after_update = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_after_update.status_code == 200
    assert me_after_update.json()["username"] == "TraderOne"
