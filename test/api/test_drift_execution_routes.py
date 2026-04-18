import base64

import jwt
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.routes import router


class DummyDriftExecutionRequestService:
    def __init__(self):
        self.created = []
        self.submitted = []
        self.failed = []
        self.records = {}

    def create_prepared_request(self, **kwargs):
        self.created.append(kwargs)
        record = {
            "execution_id": "exec-1",
            "status": "prepared",
            "mode": "client_wallet_signing",
            "user_id": kwargs["user_id"],
            "auth_wallet_address": kwargs["auth_wallet_address"],
            "execution_wallet_address": kwargs["execution_wallet_status"]["execution_wallet_address"],
            "same_wallet_required": True,
            "sub_account_id": kwargs["sub_account_id"],
            "order_intent": kwargs["order_intent"],
            "requires_client_signature": True,
            "prepared_transaction": kwargs.get("prepared_transaction", {}),
            "prepared_at": "2026-04-18T00:00:00+00:00",
            "expires_at": "2026-04-18T00:15:00+00:00",
            "submitted_at": None,
            "transaction_signature": None,
            "last_error": None,
        }
        self.records["exec-1"] = record
        return record

    def get_request(self, *, user_id, execution_id):
        record = self.records[execution_id]
        assert record["user_id"] == user_id
        return dict(record)

    def mark_submitted(self, **kwargs):
        self.submitted.append(kwargs)
        record = dict(self.records[kwargs["execution_id"]])
        record["status"] = "submitted"
        record["submitted_at"] = "2026-04-18T00:05:00+00:00"
        record["transaction_signature"] = kwargs["transaction_signature"]
        self.records[kwargs["execution_id"]] = record
        return record

    def mark_failed(self, **kwargs):
        self.failed.append(kwargs)
        record = dict(self.records[kwargs["execution_id"]])
        record["status"] = "submit_failed"
        record["last_error"] = kwargs["error"]
        self.records[kwargs["execution_id"]] = record
        return record


class DummySendResponse:
    def __init__(self, value):
        self.value = value


class DummyAsyncClient:
    def __init__(self, rpc_url):
        self.rpc_url = rpc_url
        self.calls = []

    async def send_raw_transaction(self, raw_tx, opts=None):
        self.calls.append({"raw_tx": raw_tx, "opts": opts})
        return DummySendResponse("sig-123")

    async def close(self):
        return None


class DummyDriftExecutionTxBuilder:
    def __init__(self):
        self.calls = []

    async def build_place_perp_order_payload(self, **kwargs):
        self.calls.append(kwargs)
        return {
            "classification": "same_wallet_mobile_signing_payload",
            "market_type": "perp",
            "sub_account_id": kwargs["sub_account_id"],
            "wallet_address": kwargs["wallet_address"],
            "authority": kwargs["wallet_address"],
            "user_account_public_key": "user-pubkey",
            "user_stats_public_key": "user-stats-pubkey",
            "state_public_key": "state-pubkey",
            "recent_blockhash": "blockhash-1",
            "last_valid_block_height": 123,
            "message_version": "v0",
            "transaction_encoding": "base64",
            "unsigned_transaction": "dW5zaWduZWQtdHg=",
            "unsigned_message": "dW5zaWduZWQtbWVzc2FnZQ==",
            "signing_instructions": [
                "Deserialize",
                "Sign",
                "Submit",
            ],
        }


def create_test_client():
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def build_auth_header(monkeypatch, wallet_address="WalletAddress11111111111111111111111111111"):
    monkeypatch.setattr("api.routes.settings.AUTH_JWT_SECRET", "test-jwt-secret")
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
    return {"Authorization": f"Bearer {token}"}


def test_drift_execution_prepare_status_and_submit(monkeypatch):
    service = DummyDriftExecutionRequestService()
    builder = DummyDriftExecutionTxBuilder()
    client = create_test_client()
    headers = build_auth_header(monkeypatch)

    monkeypatch.setattr("api.routes.settings.DRIFT_EXECUTION_ENABLED", True)
    monkeypatch.setattr("api.routes.get_drift_execution_request_service", lambda: service)
    monkeypatch.setattr("api.routes.get_drift_execution_tx_builder", lambda: builder)
    monkeypatch.setattr("solana.rpc.async_api.AsyncClient", DummyAsyncClient)

    prepare_response = client.post(
        "/api/drift/execution/prepare",
        headers=headers,
        json={
            "sub_account_id": 0,
            "market_type": "perp",
            "market_index": 5,
            "symbol": "SOL-PERP",
            "side": "long",
            "order_type": "limit",
            "base_asset_amount": "1000000",
            "price": "150000000",
            "post_only": True,
        },
    )
    assert prepare_response.status_code == 200
    prepared = prepare_response.json()
    assert prepared["execution_id"] == "exec-1"
    assert prepared["status"] == "prepared"
    assert prepared["mode"] == "client_wallet_signing"
    assert prepared["same_wallet_required"] is True
    assert prepared["order_intent"]["symbol"] == "SOL-PERP"
    assert prepared["prepared_transaction"]["classification"] == "same_wallet_mobile_signing_payload"
    assert prepared["prepared_transaction"]["unsigned_transaction"] == "dW5zaWduZWQtdHg="
    assert service.created[0]["execution_wallet_status"]["mode"] == "same_wallet"
    assert builder.calls[0]["order_intent"]["market_index"] == 5

    status_response = client.get("/api/drift/execution/exec-1", headers=headers)
    assert status_response.status_code == 200
    assert status_response.json()["execution_id"] == "exec-1"
    assert status_response.json()["status"] == "prepared"

    signed_tx = base64.b64encode(b"signed-transaction").decode("utf-8")
    submit_response = client.post(
        "/api/drift/execution/submit",
        headers=headers,
        json={
            "execution_id": "exec-1",
            "signed_transaction": signed_tx,
            "transaction_encoding": "base64",
            "skip_preflight": True,
        },
    )
    assert submit_response.status_code == 200
    submitted = submit_response.json()
    assert submitted["success"] is True
    assert submitted["execution_id"] == "exec-1"
    assert submitted["status"] == "submitted"
    assert submitted["transaction_signature"] == "sig-123"
    assert submitted["rpc_url"] == "https://api.mainnet-beta.solana.com"
    assert service.submitted[0]["execution_id"] == "exec-1"


def test_drift_execution_prepare_requires_auth(monkeypatch):
    monkeypatch.setattr("api.routes.settings.DRIFT_EXECUTION_ENABLED", True)
    client = create_test_client()

    response = client.post(
        "/api/drift/execution/prepare",
        json={
            "side": "long",
            "order_type": "market",
            "base_asset_amount": "1",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Missing bearer token."
