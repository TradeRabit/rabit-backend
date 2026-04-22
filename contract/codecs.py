"""Manual account decoders for the Rabit Solana program."""
from __future__ import annotations

from typing import Optional, TypeVar

from .models import (
    AiUsageRecordAccount,
    DelegatedSignerAccount,
    ModelRegistryAccount,
    PlatformConfigAccount,
    SpendingProfileAccount,
)
from .seeds import account_discriminator

T = TypeVar("T")


def _load_pubkey_sdk():
    try:
        from solders.pubkey import Pubkey
    except ImportError as exc:
        raise ValueError(
            "Rabit contract account decoding requires optional Solana dependencies. "
            "Install them before using the on-chain contract SDK."
        ) from exc
    return Pubkey


def _ensure_discriminator(data: bytes, account_name: str) -> int:
    expected = account_discriminator(account_name)
    if len(data) < 8 or data[:8] != expected:
        raise ValueError(f"Account discriminator mismatch for {account_name}.")
    return 8


def _read_u8(data: bytes, offset: int) -> tuple[int, int]:
    return data[offset], offset + 1


def _read_bool(data: bytes, offset: int) -> tuple[bool, int]:
    value, offset = _read_u8(data, offset)
    return bool(value), offset


def _read_u16(data: bytes, offset: int) -> tuple[int, int]:
    return int.from_bytes(data[offset : offset + 2], "little", signed=False), offset + 2


def _read_u64(data: bytes, offset: int) -> tuple[int, int]:
    return int.from_bytes(data[offset : offset + 8], "little", signed=False), offset + 8


def _read_i64(data: bytes, offset: int) -> tuple[int, int]:
    return int.from_bytes(data[offset : offset + 8], "little", signed=True), offset + 8


def _read_pubkey(data: bytes, offset: int) -> tuple[str, int]:
    pubkey_cls = _load_pubkey_sdk()
    end = offset + 32
    return str(pubkey_cls.from_bytes(data[offset:end])), end


def _read_string(data: bytes, offset: int) -> tuple[str, int]:
    length = int.from_bytes(data[offset : offset + 4], "little", signed=False)
    start = offset + 4
    end = start + length
    return data[start:end].decode("utf-8"), end


def _read_option_pubkey(data: bytes, offset: int) -> tuple[Optional[str], int]:
    tag, offset = _read_u8(data, offset)
    if tag == 0:
        return None, offset
    value, offset = _read_pubkey(data, offset)
    return value, offset


def decode_platform_config(data: bytes) -> PlatformConfigAccount:
    offset = _ensure_discriminator(data, "PlatformConfig")
    authority, offset = _read_pubkey(data, offset)
    backend_authority, offset = _read_pubkey(data, offset)
    platform_fee_bps, offset = _read_u16(data, offset)
    default_markup_bps, offset = _read_u16(data, offset)
    fee_recipient, offset = _read_pubkey(data, offset)
    total_fees_collected, offset = _read_u64(data, offset)
    total_markup_collected, offset = _read_u64(data, offset)
    is_paused, offset = _read_bool(data, offset)
    bump, offset = _read_u8(data, offset)
    fee_recipient_bump, offset = _read_u8(data, offset)
    return PlatformConfigAccount(
        authority=authority,
        backend_authority=backend_authority,
        platform_fee_bps=platform_fee_bps,
        default_markup_bps=default_markup_bps,
        fee_recipient=fee_recipient,
        total_fees_collected=total_fees_collected,
        total_markup_collected=total_markup_collected,
        is_paused=is_paused,
        bump=bump,
        fee_recipient_bump=fee_recipient_bump,
    )


def decode_spending_profile(data: bytes) -> SpendingProfileAccount:
    offset = _ensure_discriminator(data, "SpendingProfile")
    owner, offset = _read_pubkey(data, offset)
    payment_mint, offset = _read_pubkey(data, offset)
    total_charged, offset = _read_u64(data, offset)
    total_model_cost, offset = _read_u64(data, offset)
    total_service_cost, offset = _read_u64(data, offset)
    total_platform_fee, offset = _read_u64(data, offset)
    total_delegated_usage, offset = _read_u64(data, offset)
    created_at, offset = _read_i64(data, offset)
    usage_sequence, offset = _read_u64(data, offset)
    bump, offset = _read_u8(data, offset)
    return SpendingProfileAccount(
        owner=owner,
        payment_mint=payment_mint,
        total_charged=total_charged,
        total_model_cost=total_model_cost,
        total_service_cost=total_service_cost,
        total_platform_fee=total_platform_fee,
        total_delegated_usage=total_delegated_usage,
        created_at=created_at,
        usage_sequence=usage_sequence,
        bump=bump,
    )


def decode_delegated_signer(data: bytes) -> DelegatedSignerAccount:
    offset = _ensure_discriminator(data, "DelegatedSigner")
    owner, offset = _read_pubkey(data, offset)
    delegated_pubkey, offset = _read_pubkey(data, offset)
    created_at, offset = _read_i64(data, offset)
    expires_at, offset = _read_i64(data, offset)
    spending_limit, offset = _read_u64(data, offset)
    spent_amount, offset = _read_u64(data, offset)
    is_active, offset = _read_bool(data, offset)
    bump, offset = _read_u8(data, offset)
    return DelegatedSignerAccount(
        owner=owner,
        delegated_pubkey=delegated_pubkey,
        created_at=created_at,
        expires_at=expires_at,
        spending_limit=spending_limit,
        spent_amount=spent_amount,
        is_active=is_active,
        bump=bump,
    )


def decode_ai_usage_record(data: bytes) -> AiUsageRecordAccount:
    offset = _ensure_discriminator(data, "AiUsageRecord")
    user, offset = _read_pubkey(data, offset)
    spending_profile, offset = _read_pubkey(data, offset)
    delegated_signer, offset = _read_option_pubkey(data, offset)
    model_id, offset = _read_string(data, offset)
    usage_type, offset = _read_string(data, offset)
    tokens_used, offset = _read_u64(data, offset)
    base_cost, offset = _read_u64(data, offset)
    service_cost, offset = _read_u64(data, offset)
    markup_bps, offset = _read_u16(data, offset)
    markup_amount, offset = _read_u64(data, offset)
    platform_fee_bps, offset = _read_u16(data, offset)
    platform_fee_amount, offset = _read_u64(data, offset)
    total_charged, offset = _read_u64(data, offset)
    timestamp, offset = _read_i64(data, offset)
    is_verified_model, offset = _read_bool(data, offset)
    pricing_verified, offset = _read_bool(data, offset)
    bump, offset = _read_u8(data, offset)
    return AiUsageRecordAccount(
        user=user,
        spending_profile=spending_profile,
        delegated_signer=delegated_signer,
        model_id=model_id,
        usage_type=usage_type,
        tokens_used=tokens_used,
        base_cost=base_cost,
        service_cost=service_cost,
        markup_bps=markup_bps,
        markup_amount=markup_amount,
        platform_fee_bps=platform_fee_bps,
        platform_fee_amount=platform_fee_amount,
        total_charged=total_charged,
        timestamp=timestamp,
        is_verified_model=is_verified_model,
        pricing_verified=pricing_verified,
        bump=bump,
    )


def decode_model_registry(data: bytes) -> ModelRegistryAccount:
    offset = _ensure_discriminator(data, "ModelRegistry")
    model_id, offset = _read_string(data, offset)
    provider, offset = _read_string(data, offset)
    custom_contract, offset = _read_option_pubkey(data, offset)
    base_cost_per_token, offset = _read_u64(data, offset)
    is_active, offset = _read_bool(data, offset)
    is_verified, offset = _read_bool(data, offset)
    features, offset = _read_string(data, offset)
    total_usage_count, offset = _read_u64(data, offset)
    total_tokens_processed, offset = _read_u64(data, offset)
    created_at, offset = _read_i64(data, offset)
    updated_at, offset = _read_i64(data, offset)
    bump, offset = _read_u8(data, offset)
    return ModelRegistryAccount(
        model_id=model_id,
        provider=provider,
        custom_contract=custom_contract,
        base_cost_per_token=base_cost_per_token,
        is_active=is_active,
        is_verified=is_verified,
        features=features,
        total_usage_count=total_usage_count,
        total_tokens_processed=total_tokens_processed,
        created_at=created_at,
        updated_at=updated_at,
        bump=bump,
    )
