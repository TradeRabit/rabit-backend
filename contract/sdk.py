"""High-level async SDK for reading and preparing Rabit on-chain contract interactions."""
from __future__ import annotations

from contextlib import suppress
from typing import Any, Optional

from config.settings import settings

from .codecs import (
    decode_ai_usage_record,
    decode_delegated_signer,
    decode_model_registry,
    decode_platform_config,
    decode_spending_profile,
)
from .instructions import (
    build_approve_spending_delegate_data,
    build_claim_fees_data,
    build_close_delegated_signer_data,
    build_close_spending_profile_data,
    build_create_delegated_signer_data,
    build_deactivate_model_data,
    build_initialize_config_data,
    build_initialize_spending_profile_data,
    build_instruction,
    build_record_ai_usage_data,
    build_record_ai_usage_with_delegation_data,
    build_register_model_data,
    build_revoke_delegated_signer_data,
    build_revoke_spending_delegate_data,
    build_toggle_pause_data,
    build_update_authority_data,
    build_update_backend_authority_data,
    build_update_default_markup_data,
    build_update_model_data,
    build_update_platform_fee_data,
)
from .models import (
    ContractDeploymentStatus,
    InstructionAccountMetaDef,
    ProgramAccountSnapshot,
)
from .registry import load_deployment, load_idl
from .seeds import (
    SYSTEM_PROGRAM_ID,
    TOKEN_PROGRAM_ID,
    derive_ai_usage_pda,
    derive_config_pda,
    derive_delegated_signer_pda,
    derive_fee_recipient_pda,
    derive_model_registry_pda,
    derive_spending_profile_pda,
)


class RabitContractSDK:
    """Backend-facing Rabit contract helper for account reads and instruction assembly."""

    def __init__(
        self,
        *,
        cluster: Optional[str] = None,
        rpc_url: Optional[str] = None,
        program_id: Optional[str] = None,
    ) -> None:
        self.cluster = str(cluster or settings.RABIT_CONTRACT_CLUSTER or "devnet").strip().lower()
        self.deployment = load_deployment(self.cluster)
        self.rpc_url = rpc_url or settings.RABIT_CONTRACT_RPC_URL or settings.DRIFT_RPC_URL
        self.program_id = program_id or settings.RABIT_CONTRACT_PROGRAM_ID or self.deployment.program_id
        self.idl = load_idl()
        self._client = None

    @staticmethod
    def _load_sdk():
        try:
            from solders.pubkey import Pubkey
            from solana.rpc.async_api import AsyncClient
        except ImportError as exc:
            raise ValueError(
                "Rabit contract SDK requires optional Solana dependencies. "
                "Install them before using backend on-chain contract helpers."
            ) from exc
        return {"Pubkey": Pubkey, "AsyncClient": AsyncClient}

    async def _get_client(self):
        if self._client is None:
            sdk = self._load_sdk()
            self._client = sdk["AsyncClient"](self.rpc_url)
        return self._client

    async def close(self) -> None:
        if self._client is not None:
            with suppress(Exception):
                await self._client.close()
            self._client = None

    async def __aenter__(self) -> "RabitContractSDK":
        await self._get_client()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()

    def _pubkey(self, value: str):
        return self._load_sdk()["Pubkey"].from_string(value)

    @staticmethod
    def _snapshot_from_account(pubkey: str, account_info: Any) -> Optional[ProgramAccountSnapshot]:
        if account_info is None:
            return None
        return ProgramAccountSnapshot(
            pubkey=pubkey,
            owner=str(getattr(account_info, "owner", "")) or None,
            lamports=int(getattr(account_info, "lamports", 0) or 0),
            executable=bool(getattr(account_info, "executable", False)),
            data_len=len(getattr(account_info, "data", b"") or b""),
            rent_epoch=getattr(account_info, "rent_epoch", None),
        )

    async def get_account_info(self, pubkey: str):
        client = await self._get_client()
        response = await client.get_account_info(self._pubkey(pubkey))
        return getattr(response, "value", None)

    async def get_program_accounts(self):
        """Return all raw accounts owned by the Rabit program."""
        client = await self._get_client()
        response = await client.get_program_accounts(self._pubkey(self.program_id))
        return list(getattr(response, "value", []) or [])

    async def get_program_account_info(self) -> Optional[ProgramAccountSnapshot]:
        info = await self.get_account_info(self.program_id)
        return self._snapshot_from_account(self.program_id, info)

    async def get_config_account_info(self) -> Optional[ProgramAccountSnapshot]:
        config_pda, _ = derive_config_pda(cluster=self.cluster, program_id=self.program_id)
        info = await self.get_account_info(config_pda)
        return self._snapshot_from_account(config_pda, info)

    async def get_fee_recipient_account_info(self) -> Optional[ProgramAccountSnapshot]:
        fee_recipient_pda, _ = derive_fee_recipient_pda(cluster=self.cluster, program_id=self.program_id)
        info = await self.get_account_info(fee_recipient_pda)
        return self._snapshot_from_account(fee_recipient_pda, info)

    async def get_config(self):
        config_pda, _ = derive_config_pda(cluster=self.cluster, program_id=self.program_id)
        account_info = await self.get_account_info(config_pda)
        if account_info is None:
            return None
        return decode_platform_config(bytes(account_info.data))

    async def get_spending_profile(self, owner: str):
        spending_profile_pda, _ = derive_spending_profile_pda(owner, cluster=self.cluster, program_id=self.program_id)
        account_info = await self.get_account_info(spending_profile_pda)
        if account_info is None:
            return None
        return decode_spending_profile(bytes(account_info.data))

    async def get_delegated_signer(self, owner: str, delegate: str):
        delegated_signer_pda, _ = derive_delegated_signer_pda(
            owner,
            delegate,
            cluster=self.cluster,
            program_id=self.program_id,
        )
        account_info = await self.get_account_info(delegated_signer_pda)
        if account_info is None:
            return None
        return decode_delegated_signer(bytes(account_info.data))

    async def get_model_registry(self, model_id: str):
        model_registry_pda, _ = derive_model_registry_pda(
            model_id,
            cluster=self.cluster,
            program_id=self.program_id,
        )
        account_info = await self.get_account_info(model_registry_pda)
        if account_info is None:
            return None
        return decode_model_registry(bytes(account_info.data))

    async def list_model_registry_accounts(self) -> list[tuple[str, Any]]:
        """Return every decodable on-chain ModelRegistry account with its PDA."""
        accounts = await self.get_program_accounts()
        registry_accounts: list[tuple[str, Any]] = []
        for item in accounts:
            pubkey = getattr(item, "pubkey", None)
            account = getattr(item, "account", None)
            if pubkey is None or account is None:
                continue
            try:
                decoded = decode_model_registry(bytes(account.data))
            except Exception:
                continue
            registry_accounts.append((str(pubkey), decoded))
        return registry_accounts

    async def get_ai_usage_record(self, spending_profile: str, usage_sequence: int):
        usage_record_pda, _ = derive_ai_usage_pda(
            spending_profile,
            usage_sequence,
            cluster=self.cluster,
            program_id=self.program_id,
        )
        account_info = await self.get_account_info(usage_record_pda)
        if account_info is None:
            return None
        return decode_ai_usage_record(bytes(account_info.data))

    async def list_ai_usage_records(
        self,
        *,
        spending_profile: Optional[str] = None,
        user: Optional[str] = None,
        delegated_signer: Optional[str] = None,
    ) -> list[tuple[str, Any]]:
        """Return decodable on-chain AI usage records, optionally filtered by account fields."""
        accounts = await self.get_program_accounts()
        usage_records: list[tuple[str, Any]] = []
        for item in accounts:
            pubkey = getattr(item, "pubkey", None)
            account = getattr(item, "account", None)
            if pubkey is None or account is None:
                continue
            try:
                decoded = decode_ai_usage_record(bytes(account.data))
            except Exception:
                continue
            if spending_profile and str(decoded.spending_profile) != str(spending_profile):
                continue
            if user and str(decoded.user) != str(user):
                continue
            if delegated_signer and str(decoded.delegated_signer or "") != str(delegated_signer):
                continue
            usage_records.append((str(pubkey), decoded))
        usage_records.sort(key=lambda item: int(getattr(item[1], "timestamp", 0)), reverse=True)
        return usage_records

    async def get_deployment_status(self) -> ContractDeploymentStatus:
        program, config, fee_recipient = await self._fetch_status_accounts()
        return ContractDeploymentStatus(
            cluster=self.cluster,
            rpc_url=self.rpc_url,
            program=program,
            config=config,
            fee_recipient=fee_recipient,
            deployment=self.deployment,
            enabled_models=self.deployment.enabled_models,
            seeded_models=self.deployment.seeded_models,
            model_registry_coverage_pct=self.deployment.model_registry_coverage_pct,
        )

    async def _fetch_status_accounts(self):
        program = await self.get_program_account_info()
        config = await self.get_config_account_info()
        fee_recipient = await self.get_fee_recipient_account_info()
        return program, config, fee_recipient

    def build_initialize_config_instruction(
        self,
        *,
        authority: str,
        backend_authority: str,
        platform_fee_bps: int,
        default_markup_bps: int,
    ):
        config_pda, _ = derive_config_pda(cluster=self.cluster, program_id=self.program_id)
        fee_recipient_pda, _ = derive_fee_recipient_pda(cluster=self.cluster, program_id=self.program_id)
        return build_instruction(
            instruction_name="initialize_config",
            data=build_initialize_config_data(platform_fee_bps, default_markup_bps, backend_authority),
            accounts=[
                InstructionAccountMetaDef(config_pda, is_writable=True),
                InstructionAccountMetaDef(fee_recipient_pda, is_writable=True),
                InstructionAccountMetaDef(authority, is_signer=True, is_writable=True),
                InstructionAccountMetaDef(SYSTEM_PROGRAM_ID),
            ],
            program_id=self.program_id,
            cluster=self.cluster,
        )

    def build_register_model_instruction(
        self,
        *,
        authority: str,
        model_id: str,
        provider: str,
        base_cost_per_token: int,
        features: str,
    ):
        config_pda, _ = derive_config_pda(cluster=self.cluster, program_id=self.program_id)
        model_registry_pda, _ = derive_model_registry_pda(model_id, cluster=self.cluster, program_id=self.program_id)
        return build_instruction(
            instruction_name="register_model",
            data=build_register_model_data(model_id, provider, base_cost_per_token, features),
            accounts=[
                InstructionAccountMetaDef(model_registry_pda, is_writable=True),
                InstructionAccountMetaDef(config_pda),
                InstructionAccountMetaDef(authority, is_signer=True, is_writable=True),
                InstructionAccountMetaDef(SYSTEM_PROGRAM_ID),
            ],
            program_id=self.program_id,
            cluster=self.cluster,
        )

    def build_update_platform_fee_instruction(self, *, authority: str, new_platform_fee_bps: int):
        config_pda, _ = derive_config_pda(cluster=self.cluster, program_id=self.program_id)
        return build_instruction(
            instruction_name="update_platform_fee",
            data=build_update_platform_fee_data(new_platform_fee_bps),
            accounts=[
                InstructionAccountMetaDef(config_pda, is_writable=True),
                InstructionAccountMetaDef(authority, is_signer=True),
            ],
            program_id=self.program_id,
            cluster=self.cluster,
        )

    def build_update_default_markup_instruction(self, *, authority: str, new_default_markup_bps: int):
        config_pda, _ = derive_config_pda(cluster=self.cluster, program_id=self.program_id)
        return build_instruction(
            instruction_name="update_default_markup",
            data=build_update_default_markup_data(new_default_markup_bps),
            accounts=[
                InstructionAccountMetaDef(config_pda, is_writable=True),
                InstructionAccountMetaDef(authority, is_signer=True),
            ],
            program_id=self.program_id,
            cluster=self.cluster,
        )

    def build_update_authority_instruction(self, *, authority: str, new_authority: str):
        config_pda, _ = derive_config_pda(cluster=self.cluster, program_id=self.program_id)
        return build_instruction(
            instruction_name="update_authority",
            data=build_update_authority_data(new_authority),
            accounts=[
                InstructionAccountMetaDef(config_pda, is_writable=True),
                InstructionAccountMetaDef(authority, is_signer=True),
            ],
            program_id=self.program_id,
            cluster=self.cluster,
        )

    def build_update_backend_authority_instruction(self, *, authority: str, new_backend_authority: str):
        config_pda, _ = derive_config_pda(cluster=self.cluster, program_id=self.program_id)
        return build_instruction(
            instruction_name="update_backend_authority",
            data=build_update_backend_authority_data(new_backend_authority),
            accounts=[
                InstructionAccountMetaDef(config_pda, is_writable=True),
                InstructionAccountMetaDef(authority, is_signer=True),
            ],
            program_id=self.program_id,
            cluster=self.cluster,
        )

    def build_toggle_pause_instruction(self, *, authority: str):
        config_pda, _ = derive_config_pda(cluster=self.cluster, program_id=self.program_id)
        return build_instruction(
            instruction_name="toggle_pause",
            data=build_toggle_pause_data(),
            accounts=[
                InstructionAccountMetaDef(config_pda, is_writable=True),
                InstructionAccountMetaDef(authority, is_signer=True),
            ],
            program_id=self.program_id,
            cluster=self.cluster,
        )

    def build_claim_fees_instruction(self, *, authority: str, amount: int):
        config_pda, _ = derive_config_pda(cluster=self.cluster, program_id=self.program_id)
        fee_recipient_pda, _ = derive_fee_recipient_pda(cluster=self.cluster, program_id=self.program_id)
        return build_instruction(
            instruction_name="claim_fees",
            data=build_claim_fees_data(amount),
            accounts=[
                InstructionAccountMetaDef(config_pda),
                InstructionAccountMetaDef(fee_recipient_pda, is_writable=True),
                InstructionAccountMetaDef(authority, is_signer=True, is_writable=True),
                InstructionAccountMetaDef(SYSTEM_PROGRAM_ID),
            ],
            program_id=self.program_id,
            cluster=self.cluster,
        )

    def build_update_model_instruction(
        self,
        *,
        authority: str,
        model_id: str,
        base_cost_per_token: Optional[int] = None,
        is_active: Optional[bool] = None,
        features: Optional[str] = None,
        custom_contract: Optional[str] = None,
    ):
        config_pda, _ = derive_config_pda(cluster=self.cluster, program_id=self.program_id)
        model_registry_pda, _ = derive_model_registry_pda(model_id, cluster=self.cluster, program_id=self.program_id)
        return build_instruction(
            instruction_name="update_model",
            data=build_update_model_data(base_cost_per_token, is_active, features, custom_contract),
            accounts=[
                InstructionAccountMetaDef(model_registry_pda, is_writable=True),
                InstructionAccountMetaDef(config_pda),
                InstructionAccountMetaDef(authority, is_signer=True),
            ],
            program_id=self.program_id,
            cluster=self.cluster,
        )

    def build_deactivate_model_instruction(self, *, authority: str, model_id: str):
        config_pda, _ = derive_config_pda(cluster=self.cluster, program_id=self.program_id)
        model_registry_pda, _ = derive_model_registry_pda(model_id, cluster=self.cluster, program_id=self.program_id)
        return build_instruction(
            instruction_name="deactivate_model",
            data=build_deactivate_model_data(),
            accounts=[
                InstructionAccountMetaDef(model_registry_pda, is_writable=True),
                InstructionAccountMetaDef(config_pda),
                InstructionAccountMetaDef(authority, is_signer=True),
            ],
            program_id=self.program_id,
            cluster=self.cluster,
        )

    def build_initialize_spending_profile_instruction(self, *, owner: str, payment_mint: str):
        spending_profile_pda, _ = derive_spending_profile_pda(owner, cluster=self.cluster, program_id=self.program_id)
        return build_instruction(
            instruction_name="initialize_spending_profile",
            data=build_initialize_spending_profile_data(),
            accounts=[
                InstructionAccountMetaDef(spending_profile_pda, is_writable=True),
                InstructionAccountMetaDef(payment_mint),
                InstructionAccountMetaDef(owner, is_signer=True, is_writable=True),
                InstructionAccountMetaDef(SYSTEM_PROGRAM_ID),
            ],
            program_id=self.program_id,
            cluster=self.cluster,
        )

    def build_create_delegated_signer_instruction(
        self,
        *,
        owner: str,
        delegate: str,
        expiry_duration: int,
        spending_limit: int,
    ):
        delegated_signer_pda, _ = derive_delegated_signer_pda(
            owner,
            delegate,
            cluster=self.cluster,
            program_id=self.program_id,
        )
        return build_instruction(
            instruction_name="create_delegated_signer",
            data=build_create_delegated_signer_data(expiry_duration, spending_limit),
            accounts=[
                InstructionAccountMetaDef(delegated_signer_pda, is_writable=True),
                InstructionAccountMetaDef(owner, is_signer=True, is_writable=True),
                InstructionAccountMetaDef(delegate),
                InstructionAccountMetaDef(SYSTEM_PROGRAM_ID),
            ],
            program_id=self.program_id,
            cluster=self.cluster,
        )

    def build_approve_spending_delegate_instruction(
        self,
        *,
        owner: str,
        delegate: str,
        user_token_account: str,
    ):
        spending_profile_pda, _ = derive_spending_profile_pda(owner, cluster=self.cluster, program_id=self.program_id)
        delegated_signer_pda, _ = derive_delegated_signer_pda(
            owner,
            delegate,
            cluster=self.cluster,
            program_id=self.program_id,
        )
        return build_instruction(
            instruction_name="approve_spending_delegate",
            data=build_approve_spending_delegate_data(),
            accounts=[
                InstructionAccountMetaDef(spending_profile_pda, is_writable=True),
                InstructionAccountMetaDef(delegated_signer_pda),
                InstructionAccountMetaDef(user_token_account, is_writable=True),
                InstructionAccountMetaDef(owner, is_signer=True, is_writable=True),
                InstructionAccountMetaDef(TOKEN_PROGRAM_ID),
            ],
            program_id=self.program_id,
            cluster=self.cluster,
        )

    def build_revoke_spending_delegate_instruction(
        self,
        *,
        owner: str,
        user_token_account: str,
    ):
        spending_profile_pda, _ = derive_spending_profile_pda(owner, cluster=self.cluster, program_id=self.program_id)
        return build_instruction(
            instruction_name="revoke_spending_delegate",
            data=build_revoke_spending_delegate_data(),
            accounts=[
                InstructionAccountMetaDef(spending_profile_pda, is_writable=True),
                InstructionAccountMetaDef(user_token_account, is_writable=True),
                InstructionAccountMetaDef(owner, is_signer=True, is_writable=True),
                InstructionAccountMetaDef(TOKEN_PROGRAM_ID),
            ],
            program_id=self.program_id,
            cluster=self.cluster,
        )

    def build_close_spending_profile_instruction(
        self,
        *,
        owner: str,
        user_token_account: str,
    ):
        spending_profile_pda, _ = derive_spending_profile_pda(owner, cluster=self.cluster, program_id=self.program_id)
        return build_instruction(
            instruction_name="close_spending_profile",
            data=build_close_spending_profile_data(),
            accounts=[
                InstructionAccountMetaDef(spending_profile_pda, is_writable=True),
                InstructionAccountMetaDef(user_token_account, is_writable=True),
                InstructionAccountMetaDef(owner, is_signer=True, is_writable=True),
            ],
            program_id=self.program_id,
            cluster=self.cluster,
        )

    def build_revoke_delegated_signer_instruction(
        self,
        *,
        owner: str,
        delegate: str,
    ):
        delegated_signer_pda, _ = derive_delegated_signer_pda(
            owner,
            delegate,
            cluster=self.cluster,
            program_id=self.program_id,
        )
        return build_instruction(
            instruction_name="revoke_delegated_signer",
            data=build_revoke_delegated_signer_data(),
            accounts=[
                InstructionAccountMetaDef(delegated_signer_pda, is_writable=True),
                InstructionAccountMetaDef(owner, is_signer=True),
            ],
            program_id=self.program_id,
            cluster=self.cluster,
        )

    def build_close_delegated_signer_instruction(
        self,
        *,
        owner: str,
        delegate: str,
    ):
        delegated_signer_pda, _ = derive_delegated_signer_pda(
            owner,
            delegate,
            cluster=self.cluster,
            program_id=self.program_id,
        )
        return build_instruction(
            instruction_name="close_delegated_signer",
            data=build_close_delegated_signer_data(),
            accounts=[
                InstructionAccountMetaDef(delegated_signer_pda, is_writable=True),
                InstructionAccountMetaDef(owner, is_signer=True, is_writable=True),
            ],
            program_id=self.program_id,
            cluster=self.cluster,
        )

    def build_record_ai_usage_instruction(
        self,
        *,
        user: str,
        owner: Optional[str],
        user_token_account: str,
        fee_recipient_token_account: str,
        payment_mint: str,
        model_id: str,
        base_cost: int,
        service_cost: int,
        usage_type: str,
        tokens_used: int,
        usage_sequence: int,
        markup_bps: Optional[int] = None,
    ):
        resolved_owner = owner or user
        config_pda, _ = derive_config_pda(cluster=self.cluster, program_id=self.program_id)
        spending_profile_pda, _ = derive_spending_profile_pda(user, cluster=self.cluster, program_id=self.program_id)
        usage_record_pda, _ = derive_ai_usage_pda(
            spending_profile_pda,
            usage_sequence,
            cluster=self.cluster,
            program_id=self.program_id,
        )
        model_registry_pda, _ = derive_model_registry_pda(model_id, cluster=self.cluster, program_id=self.program_id)
        return build_instruction(
            instruction_name="record_ai_usage",
            data=build_record_ai_usage_data(
                model_id,
                base_cost,
                service_cost,
                usage_type,
                tokens_used,
                markup_bps,
            ),
            accounts=[
                InstructionAccountMetaDef(usage_record_pda, is_writable=True),
                InstructionAccountMetaDef(spending_profile_pda, is_writable=True),
                InstructionAccountMetaDef(config_pda, is_writable=True),
                InstructionAccountMetaDef(user_token_account, is_writable=True),
                InstructionAccountMetaDef(fee_recipient_token_account, is_writable=True),
                InstructionAccountMetaDef(payment_mint),
                InstructionAccountMetaDef(resolved_owner),
                InstructionAccountMetaDef(user, is_signer=True, is_writable=True),
                InstructionAccountMetaDef(model_registry_pda, is_writable=True),
                InstructionAccountMetaDef(TOKEN_PROGRAM_ID),
                InstructionAccountMetaDef(SYSTEM_PROGRAM_ID),
            ],
            program_id=self.program_id,
            cluster=self.cluster,
        )

    def build_record_ai_usage_with_delegation_instruction(
        self,
        *,
        owner: str,
        delegate: str,
        user_token_account: str,
        fee_recipient_token_account: str,
        payment_mint: str,
        model_id: str,
        base_cost: int,
        service_cost: int,
        usage_type: str,
        tokens_used: int,
        usage_sequence: int,
        markup_bps: Optional[int] = None,
    ):
        config_pda, _ = derive_config_pda(cluster=self.cluster, program_id=self.program_id)
        spending_profile_pda, _ = derive_spending_profile_pda(owner, cluster=self.cluster, program_id=self.program_id)
        delegated_signer_pda, _ = derive_delegated_signer_pda(
            owner,
            delegate,
            cluster=self.cluster,
            program_id=self.program_id,
        )
        usage_record_pda, _ = derive_ai_usage_pda(
            spending_profile_pda,
            usage_sequence,
            cluster=self.cluster,
            program_id=self.program_id,
        )
        model_registry_pda, _ = derive_model_registry_pda(model_id, cluster=self.cluster, program_id=self.program_id)
        return build_instruction(
            instruction_name="record_ai_usage_with_delegation",
            data=build_record_ai_usage_with_delegation_data(
                model_id,
                base_cost,
                service_cost,
                usage_type,
                tokens_used,
                markup_bps,
            ),
            accounts=[
                InstructionAccountMetaDef(usage_record_pda, is_writable=True),
                InstructionAccountMetaDef(spending_profile_pda, is_writable=True),
                InstructionAccountMetaDef(delegated_signer_pda, is_writable=True),
                InstructionAccountMetaDef(config_pda, is_writable=True),
                InstructionAccountMetaDef(user_token_account, is_writable=True),
                InstructionAccountMetaDef(fee_recipient_token_account, is_writable=True),
                InstructionAccountMetaDef(payment_mint),
                InstructionAccountMetaDef(model_registry_pda, is_writable=True),
                InstructionAccountMetaDef(delegate, is_signer=True, is_writable=True),
                InstructionAccountMetaDef(TOKEN_PROGRAM_ID),
                InstructionAccountMetaDef(SYSTEM_PROGRAM_ID),
            ],
            program_id=self.program_id,
            cluster=self.cluster,
        )


_rabit_contract_sdk: RabitContractSDK | None = None


def get_rabit_contract_sdk() -> RabitContractSDK:
    """Return a singleton Rabit contract SDK."""
    global _rabit_contract_sdk
    if _rabit_contract_sdk is None:
        _rabit_contract_sdk = RabitContractSDK()
    return _rabit_contract_sdk
