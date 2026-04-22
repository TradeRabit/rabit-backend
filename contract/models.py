"""Dataclasses used by the Rabit on-chain contract layer."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass(frozen=True)
class ContractDeployment:
    """Resolved deployment metadata for one Rabit contract cluster."""

    cluster: str
    program_id: str
    config_pda: str
    fee_recipient_pda: str
    authority_wallet: Optional[str] = None
    backend_authority_wallet: Optional[str] = None
    init_config_signature: Optional[str] = None
    sample_seeded_model_id: Optional[str] = None
    sample_seeded_model_pda: Optional[str] = None
    sample_model_seed_signature: Optional[str] = None
    enabled_models: int = 0
    seeded_models: int = 0
    model_registry_coverage_pct: float = 0.0
    verified_at: Optional[str] = None
    verification_source: Optional[str] = None
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class InstructionAccountMetaDef:
    """Serializable account metadata before converting into SDK-specific types."""

    pubkey: str
    is_signer: bool = False
    is_writable: bool = False


@dataclass(frozen=True)
class ProgramAccountSnapshot:
    """Raw account snapshot returned by the on-chain SDK layer."""

    pubkey: str
    owner: Optional[str]
    lamports: int
    executable: bool
    data_len: int
    rent_epoch: Optional[int] = None


@dataclass(frozen=True)
class PlatformConfigAccount:
    authority: str
    backend_authority: str
    platform_fee_bps: int
    default_markup_bps: int
    fee_recipient: str
    total_fees_collected: int
    total_markup_collected: int
    is_paused: bool
    bump: int
    fee_recipient_bump: int


@dataclass(frozen=True)
class SpendingProfileAccount:
    owner: str
    payment_mint: str
    total_charged: int
    total_model_cost: int
    total_service_cost: int
    total_platform_fee: int
    total_delegated_usage: int
    created_at: int
    usage_sequence: int
    bump: int


@dataclass(frozen=True)
class DelegatedSignerAccount:
    owner: str
    delegated_pubkey: str
    created_at: int
    expires_at: int
    spending_limit: int
    spent_amount: int
    is_active: bool
    bump: int


@dataclass(frozen=True)
class AiUsageRecordAccount:
    user: str
    spending_profile: str
    delegated_signer: Optional[str]
    model_id: str
    usage_type: str
    tokens_used: int
    base_cost: int
    service_cost: int
    markup_bps: int
    markup_amount: int
    platform_fee_bps: int
    platform_fee_amount: int
    total_charged: int
    timestamp: int
    is_verified_model: bool
    pricing_verified: bool
    bump: int


@dataclass(frozen=True)
class ModelRegistryAccount:
    model_id: str
    provider: str
    custom_contract: Optional[str]
    base_cost_per_token: int
    is_active: bool
    is_verified: bool
    features: str
    total_usage_count: int
    total_tokens_processed: int
    created_at: int
    updated_at: int
    bump: int


@dataclass(frozen=True)
class ContractDeploymentStatus:
    """Backend-friendly on-chain deployment status snapshot."""

    cluster: str
    rpc_url: str
    program: Optional[ProgramAccountSnapshot]
    config: Optional[ProgramAccountSnapshot]
    fee_recipient: Optional[ProgramAccountSnapshot]
    deployment: ContractDeployment
    enabled_models: int
    seeded_models: int
    model_registry_coverage_pct: float
