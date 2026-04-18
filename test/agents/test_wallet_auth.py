import base64

from nacl.signing import SigningKey

from agents.auth import create_wallet_auth_nonce, verify_access_token, verify_wallet_auth


ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def b58encode(raw: bytes) -> str:
    num = int.from_bytes(raw, "big")
    if num == 0:
        encoded = ""
    else:
        encoded = ""
        while num > 0:
            num, remainder = divmod(num, 58)
            encoded = ALPHABET[remainder] + encoded
    leading_zeros = len(raw) - len(raw.lstrip(b"\x00"))
    return "1" * leading_zeros + (encoded or "1" if raw else "")


def test_wallet_auth_nonce_verify_and_jwt(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "agents.auth.jwt_auth.settings.AUTH_JWT_SECRET",
        "test-jwt-secret",
    )
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

    challenge = create_wallet_auth_nonce(wallet_address=wallet_address)
    signature = signing_key.sign(challenge["message"].encode("utf-8")).signature
    encoded_signature = base64.b64encode(signature).decode("utf-8")

    verified = verify_wallet_auth(
        wallet_address=wallet_address,
        nonce=challenge["nonce"],
        signature=encoded_signature,
        signature_encoding="base64",
        message=challenge["message"],
    )

    claims = verify_access_token(verified["access_token"])
    assert verified["wallet_address"] == wallet_address
    assert verified["user_id"] == f"wallet:{wallet_address}"
    assert claims["wallet_address"] == wallet_address
    assert claims["user_id"] == f"wallet:{wallet_address}"
