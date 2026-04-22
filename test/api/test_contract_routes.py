import jwt
from fastapi import FastAPI
from fastapi.testclient import TestClient
from types import SimpleNamespace

from api.routes import router


def create_test_client():
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def build_auth_header(monkeypatch, wallet_address="HfMHdkJuHztBm1y2JpPfZwauqesZQdmenQaHVL3J9wMP"):
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


async def _mock_readiness(*, wallet_address, user_id=None):
    return {
        "user_id": user_id,
        "wallet_address": wallet_address,
        "cluster": "devnet",
        "program_id": "program-1",
        "backend_authority_wallet": "HfMHdkJuHztBm1y2JpPfZwauqesZQdmenQaHVL3J9wMP",
        "backend_signer_ready": True,
        "backend_signer_pubkey": "HfMHdkJuHztBm1y2JpPfZwauqesZQdmenQaHVL3J9wMP",
        "payment_mint": "So11111111111111111111111111111111111111112",
        "payment_token_symbol": "USDC",
        "payment_mint_decimals": 6,
        "payment_token_usd_price": 1.0,
        "minimum_balance_usd": 1.0,
        "user_token_account": "user-ata-1",
        "fee_recipient_token_account": "fee-ata-1",
        "user_token_account_exists": True,
        "fee_recipient_token_account_exists": True,
        "payment_balance_amount": 5000000,
        "payment_balance_ui_amount": 5.0,
        "payment_balance_usd": 5.0,
        "balance_ok": True,
        "spending_profile_pda": "DipGVm96xHJeqJZ6BhJHZEuRkWBptxnecWWHMcRrGAL2",
        "spending_profile_exists": True,
        "spending_profile_usage_sequence": 4,
        "spending_profile_payment_mint": "mint-1",
        "delegated_signer_pda": "GAAcR82eZgdugS1737HLgKdKjx9vx7yYCSRm4iVwwGb3",
        "delegated_signer_exists": True,
        "delegated_signer_active": True,
        "delegated_signer_expires_at": 9999999999,
        "delegated_signer_spending_limit": 1000000000,
        "setup_complete": True,
        "can_chat": True,
        "notes": [],
    }


def test_contract_readiness_endpoint(monkeypatch):
    monkeypatch.setattr("api.routes.get_contract_readiness", _mock_readiness)
    client = create_test_client()
    headers = build_auth_header(monkeypatch)

    response = client.get("/api/contract/readiness", headers=headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["setup_complete"] is True
    assert payload["payment_balance_usd"] == 5.0
    assert payload["backend_authority_wallet"] == "HfMHdkJuHztBm1y2JpPfZwauqesZQdmenQaHVL3J9wMP"


def test_prepare_contract_spending_profile_returns_unsigned_payload(monkeypatch):
    async def _uninitialized_readiness(*, wallet_address, user_id=None):
        payload = await _mock_readiness(wallet_address=wallet_address, user_id=user_id)
        payload["spending_profile_exists"] = False
        payload["setup_complete"] = False
        return payload

    class DummySdk:
        rpc_url = "https://rpc.devnet.example"

        def build_initialize_spending_profile_instruction(self, *, owner, payment_mint):
            assert owner.startswith("HfMH")
            assert payment_mint == "mint-1"
            return "instruction-1"

    async def _build_unsigned_instruction_payload(**kwargs):
        assert kwargs["action"] == "initialize_spending_profile"
        assert kwargs["instruction"] == "instruction-1"
        return {
            "classification": "contract_setup_mobile_signing_payload",
            "action": kwargs["action"],
            "cluster": "devnet",
            "program_id": "program-1",
            "authority": kwargs["payer"],
            "transaction_encoding": "base64",
            "recent_blockhash": "blockhash-1",
            "last_valid_block_height": 123,
            "message_version": "v0",
            "unsigned_transaction": "dW5zaWduZWQtdHg=",
            "unsigned_message": "dW5zaWduZWQtbWVzc2FnZQ==",
            "signing_instructions": ["Sign it"],
        }

    monkeypatch.setattr("api.routes.get_contract_readiness", _uninitialized_readiness)
    monkeypatch.setattr("api.routes.get_rabit_contract_sdk", lambda: DummySdk())
    monkeypatch.setattr("api.routes.settings.RABIT_AI_USAGE_PAYMENT_MINT", "mint-1")
    monkeypatch.setattr("api.routes.build_unsigned_instruction_payload", _build_unsigned_instruction_payload)

    client = create_test_client()
    headers = build_auth_header(monkeypatch)
    response = client.post("/api/contract/setup/spending-profile/prepare", headers=headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["action"] == "initialize_spending_profile"
    assert payload["unsigned_transaction"] == "dW5zaWduZWQtdHg="


def test_settle_contract_ai_usage_submits_backend_signed_transaction(monkeypatch):
    class DummySettlementDb:
        def __init__(self):
            self.record = None

        def get(self, scope_id):
            return None

        def upsert(self, scope_id, record):
            self.record = dict(record)
            return self.record

    class DummyProfile:
        usage_sequence = 7

    class DummySdk:
        rpc_url = "https://rpc.devnet.example"

        async def get_spending_profile(self, wallet_address):
            assert wallet_address.startswith("HfMH")
            return DummyProfile()

        def build_record_ai_usage_with_delegation_instruction(self, **kwargs):
            assert kwargs["usage_sequence"] == 7
            assert kwargs["model_id"] == "anthropic/claude-opus-4.7"
            return "settle-ix-1"

    async def _submit_backend_signed_instruction(**kwargs):
        assert kwargs["instruction"] == "settle-ix-1"
        return {
            "transaction_signature": "sig-contract-1",
            "rpc_url": "https://rpc.devnet.example",
        }

    monkeypatch.setattr("api.routes.get_contract_readiness", _mock_readiness)
    monkeypatch.setattr(
        "api.routes._build_service_cost_summary",
        lambda scope_id, user_id=None, session_cost=None, monitoring_cost=None: {
                "scope_id": scope_id,
                "user_id": user_id,
                "onchain_ai_usage": {
                    "scope_id": scope_id,
                    "user_id": user_id,
                    "cluster": "devnet",
                    "program_id": "program-1",
                    "config_pda": "config-pda-1",
                    "fee_recipient_pda": "fee-pda-1",
                    "backend_authority_wallet": "HfMHdkJuHztBm1y2JpPfZwauqesZQdmenQaHVL3J9wMP",
                    "owner_wallet_address": "HfMHdkJuHztBm1y2JpPfZwauqesZQdmenQaHVL3J9wMP",
                    "spending_profile_pda": "DipGVm96xHJeqJZ6BhJHZEuRkWBptxnecWWHMcRrGAL2",
                    "delegated_signer_pda": "GAAcR82eZgdugS1737HLgKdKjx9vx7yYCSRm4iVwwGb3",
                    "payment_mint": "So11111111111111111111111111111111111111112",
                    "payment_token_symbol": "USDC",
                    "payment_mint_decimals": 6,
                    "payment_token_usd_price": 1.0,
                    "usage_type": "text",
                    "tokens_used": 3900,
                    "model_ids": ["anthropic/claude-opus-4.7"],
                    "instruction_buildable": True,
                    "instruction_name": "record_ai_usage_with_delegation",
                    "preview_mode": "aggregate_scope_preview",
                    "notes": [],
                    "model_id": "anthropic/claude-opus-4.7",
                    "model_registry_pda": "model-registry-pda-1",
                    "model_cost_usd": 0.0123,
                    "service_cost_usd": 0.0115,
                    "total_cost_usd": 0.0238,
                    "base_cost_units": 12300,
                    "service_cost_units": 11500,
                    "chargeable_cost_units": 23800,
                    "usage_type": "text",
                    "tokens_used": 3900,
                    "markup_bps": 500,
                    "markup_amount_units": 1190,
                    "platform_fee_bps": 500,
                    "platform_fee_amount_units": 1249,
                    "total_charged_units": 26239,
                },
            },
        )
    monkeypatch.setattr("api.routes.get_rabit_contract_sdk", lambda: DummySdk())
    monkeypatch.setattr("api.routes.get_ai_usage_settlement_database", lambda: DummySettlementDb())
    monkeypatch.setattr("api.routes.submit_backend_signed_instruction", _submit_backend_signed_instruction)
    monkeypatch.setattr("api.routes.settings.RABIT_AI_USAGE_PAYMENT_MINT", "mint-1")

    client = create_test_client()
    headers = build_auth_header(monkeypatch)
    response = client.post(
        "/api/contract/ai-usage/settle",
        headers=headers,
        json={"scope_id": "scope-1"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["transaction_signature"] == "sig-contract-1"
    assert payload["settlement_record"]["usage_sequence"] == 7


def test_agent_chat_rejects_when_contract_balance_is_below_threshold(monkeypatch):
    async def _low_balance_readiness(*, wallet_address, user_id=None):
        payload = await _mock_readiness(wallet_address=wallet_address, user_id=user_id)
        payload["balance_ok"] = False
        payload["payment_balance_usd"] = 0.42
        payload["can_chat"] = False
        payload["notes"] = ["Payment balance is below minimum."]
        return payload

    monkeypatch.setattr("api.routes.get_contract_readiness", _low_balance_readiness)
    monkeypatch.setattr("api.routes.settings.RABIT_AI_USAGE_ENFORCE_CHAT_BALANCE", True)

    client = create_test_client()
    headers = build_auth_header(monkeypatch)
    response = client.post(
        "/api/agent/chat",
        headers=headers,
        json={"message": "hello", "scope_id": "scope-1", "attachment_ids": []},
    )

    assert response.status_code == 402
    payload = response.json()
    assert payload["detail"]["readiness"]["payment_balance_usd"] == 0.42


def test_contract_config_endpoint_returns_decoded_account(monkeypatch):
    class DummySdk:
        async def get_config(self):
            return SimpleNamespace(
                authority="auth-1",
                backend_authority="backend-1",
                platform_fee_bps=500,
                default_markup_bps=400,
                fee_recipient="fee-1",
                total_fees_collected=1000,
                total_markup_collected=500,
                is_paused=False,
                bump=1,
                fee_recipient_bump=2,
            )

    monkeypatch.setattr("api.routes.get_rabit_contract_sdk", lambda: DummySdk())
    monkeypatch.setattr(
        "api.routes.load_deployment",
        lambda cluster: SimpleNamespace(cluster="devnet", program_id="program-1", config_pda="config-pda-1"),
    )

    client = create_test_client()
    response = client.get("/api/contract/config")

    assert response.status_code == 200
    payload = response.json()
    assert payload["account_type"] == "platform_config"
    assert payload["pda"] == "config-pda-1"
    assert payload["data"]["platform_fee_bps"] == 500


def test_prepare_contract_revoke_delegate_returns_unsigned_payload(monkeypatch):
    class DummySdk:
        rpc_url = "https://rpc.devnet.example"

        def build_revoke_spending_delegate_instruction(self, *, owner, user_token_account):
            assert owner.startswith("HfMH")
            assert user_token_account == "user-ata-1"
            return "revoke-delegate-ix"

    async def _build_unsigned_instruction_payload(**kwargs):
        assert kwargs["action"] == "revoke_spending_delegate"
        assert kwargs["instruction"] == "revoke-delegate-ix"
        return {
            "classification": "contract_setup_mobile_signing_payload",
            "action": kwargs["action"],
            "cluster": "devnet",
            "program_id": "program-1",
            "authority": kwargs["payer"],
            "transaction_encoding": "base64",
            "recent_blockhash": "blockhash-1",
            "last_valid_block_height": 123,
            "message_version": "v0",
            "unsigned_transaction": "dHgtMQ==",
            "unsigned_message": "bXNnLTE=",
            "signing_instructions": ["Sign it"],
        }

    monkeypatch.setattr("api.routes.get_contract_readiness", _mock_readiness)
    monkeypatch.setattr("api.routes.get_rabit_contract_sdk", lambda: DummySdk())
    monkeypatch.setattr("api.routes.build_unsigned_instruction_payload", _build_unsigned_instruction_payload)

    client = create_test_client()
    headers = build_auth_header(monkeypatch)
    response = client.post("/api/contract/setup/revoke-delegate/prepare", headers=headers)

    assert response.status_code == 200
    assert response.json()["action"] == "revoke_spending_delegate"


def test_prepare_contract_direct_ai_usage_returns_unsigned_payload(monkeypatch):
    class DummyProfile:
        usage_sequence = 9

    class DummySdk:
        rpc_url = "https://rpc.devnet.example"

        async def get_spending_profile(self, wallet_address):
            assert wallet_address.startswith("HfMH")
            return DummyProfile()

        def build_record_ai_usage_instruction(self, **kwargs):
            assert kwargs["usage_sequence"] == 9
            assert kwargs["model_id"] == "anthropic/claude-opus-4.7"
            return "direct-ai-usage-ix"

    async def _build_unsigned_instruction_payload(**kwargs):
        assert kwargs["action"] == "record_ai_usage"
        assert kwargs["instruction"] == "direct-ai-usage-ix"
        return {
            "classification": "contract_setup_mobile_signing_payload",
            "action": kwargs["action"],
            "cluster": "devnet",
            "program_id": "program-1",
            "authority": kwargs["payer"],
            "transaction_encoding": "base64",
            "recent_blockhash": "blockhash-2",
            "last_valid_block_height": 124,
            "message_version": "v0",
            "unsigned_transaction": "dHgtMg==",
            "unsigned_message": "bXNnLTI=",
            "signing_instructions": ["Sign it"],
        }

    monkeypatch.setattr("api.routes.get_contract_readiness", _mock_readiness)
    monkeypatch.setattr(
        "api.routes._build_service_cost_summary",
        lambda scope_id, user_id=None, session_cost=None, monitoring_cost=None: {
            "scope_id": scope_id,
            "user_id": user_id,
            "onchain_ai_usage": {
                "instruction_buildable": True,
                "model_id": "anthropic/claude-opus-4.7",
                "base_cost_units": 123,
                "service_cost_units": 45,
                "usage_type": "text",
                "tokens_used": 3900,
                "markup_bps": 500,
            },
        },
    )
    monkeypatch.setattr("api.routes.get_rabit_contract_sdk", lambda: DummySdk())
    monkeypatch.setattr("api.routes.build_unsigned_instruction_payload", _build_unsigned_instruction_payload)
    monkeypatch.setattr("api.routes.settings.RABIT_AI_USAGE_PAYMENT_MINT", "mint-1")

    client = create_test_client()
    headers = build_auth_header(monkeypatch)
    response = client.post(
        "/api/contract/ai-usage/direct/prepare",
        headers=headers,
        json={"scope_id": "scope-2"},
    )

    assert response.status_code == 200
    assert response.json()["action"] == "record_ai_usage"


def test_contract_settlement_detail_reconciles_onchain_record(monkeypatch):
    class DummySettlementDb:
        def get(self, scope_id):
            return {
                "scope_id": scope_id,
                "user_id": "wallet:HfMHdkJuHztBm1y2JpPfZwauqesZQdmenQaHVL3J9wMP",
                "wallet_address": "HfMHdkJuHztBm1y2JpPfZwauqesZQdmenQaHVL3J9wMP",
                "transaction_signature": "sig-1",
                "rpc_url": "https://rpc.devnet.example",
                "submitted_at": "2026-04-22T00:00:00+00:00",
                "usage_sequence": 7,
                "model_id": "anthropic/claude-opus-4.7",
            }

    class DummySdk:
        async def get_ai_usage_record(self, spending_profile, usage_sequence):
            assert usage_sequence == 7
            return SimpleNamespace(model_id="anthropic/claude-opus-4.7", total_charged=26239, usage_type="text")

    monkeypatch.setattr("api.routes.get_ai_usage_settlement_database", lambda: DummySettlementDb())
    monkeypatch.setattr("api.routes.get_contract_readiness", _mock_readiness)
    monkeypatch.setattr("api.routes.get_rabit_contract_sdk", lambda: DummySdk())
    monkeypatch.setattr("api.routes.derive_ai_usage_pda", lambda *args, **kwargs: ("usage-pda-1", 255))
    monkeypatch.setattr(
        "api.routes.load_deployment",
        lambda cluster: SimpleNamespace(cluster="devnet", program_id="program-1"),
    )

    client = create_test_client()
    headers = build_auth_header(monkeypatch)
    response = client.get("/api/contract/settlements/scope-1", headers=headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["onchain_record_found"] is True
    assert payload["onchain_record_pda"] == "usage-pda-1"
    assert payload["onchain_record"]["total_charged"] == 26239


def test_register_contract_model_uses_backend_signed_instruction(monkeypatch):
    class DummySdk:
        rpc_url = "https://rpc.devnet.example"

        def build_register_model_instruction(self, **kwargs):
            assert kwargs["authority"] == "auth-wallet-1"
            assert kwargs["model_id"] == "anthropic/claude-opus-4.7"
            return "register-model-ix"

    async def _submit_backend_signed_instruction(**kwargs):
        assert kwargs["instruction"] == "register-model-ix"
        return {
            "transaction_signature": "sig-register-1",
            "rpc_url": "https://rpc.devnet.example",
            "signer": "auth-wallet-1",
        }

    monkeypatch.setattr("api.routes._require_contract_authority_signer", lambda: "auth-wallet-1")
    monkeypatch.setattr("api.routes.get_rabit_contract_sdk", lambda: DummySdk())
    monkeypatch.setattr("api.routes.submit_backend_signed_instruction", _submit_backend_signed_instruction)
    monkeypatch.setattr(
        "api.routes.load_deployment",
        lambda cluster: SimpleNamespace(cluster="devnet", program_id="program-1"),
    )

    client = create_test_client()
    response = client.post(
        "/api/contract/model-registry/register",
        json={
            "model_id": "anthropic/claude-opus-4.7",
            "provider": "anthropic",
            "base_cost_per_token": 123,
            "features": "tools,reasoning",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["instruction_name"] == "register_model"
    assert payload["transaction_signature"] == "sig-register-1"
