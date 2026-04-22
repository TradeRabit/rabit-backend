"""Instruction data builders and solders Instruction helpers for the Rabit contract."""
from __future__ import annotations

from typing import Optional, Sequence

from .models import InstructionAccountMetaDef
from .registry import get_program_id
from .seeds import instruction_discriminator


def _load_instruction_sdk():
    try:
        from solders.instruction import AccountMeta, Instruction
        from solders.pubkey import Pubkey
    except ImportError as exc:
        raise ValueError(
            "Rabit contract instruction builders require optional Solana dependencies. "
            "Install them before using the on-chain contract SDK."
        ) from exc
    return {"AccountMeta": AccountMeta, "Instruction": Instruction, "Pubkey": Pubkey}


def encode_u8(value: int) -> bytes:
    return int(value).to_bytes(1, "little", signed=False)


def encode_bool(value: bool) -> bytes:
    return encode_u8(1 if value else 0)


def encode_u16(value: int) -> bytes:
    return int(value).to_bytes(2, "little", signed=False)


def encode_u32(value: int) -> bytes:
    return int(value).to_bytes(4, "little", signed=False)


def encode_u64(value: int) -> bytes:
    return int(value).to_bytes(8, "little", signed=False)


def encode_i64(value: int) -> bytes:
    return int(value).to_bytes(8, "little", signed=True)


def encode_string(value: str) -> bytes:
    encoded = str(value).encode("utf-8")
    return encode_u32(len(encoded)) + encoded


def encode_option(value: Optional[object], encoder) -> bytes:
    if value is None:
        return encode_u8(0)
    return encode_u8(1) + encoder(value)


def encode_pubkey(value: str) -> bytes:
    sdk = _load_instruction_sdk()
    return bytes(sdk["Pubkey"].from_string(value))


def build_instruction_data(instruction_name: str, *encoded_args: bytes) -> bytes:
    return instruction_discriminator(instruction_name) + b"".join(encoded_args)


def build_initialize_config_data(platform_fee_bps: int, default_markup_bps: int, backend_authority: str) -> bytes:
    return build_instruction_data(
        "initialize_config",
        encode_u16(platform_fee_bps),
        encode_u16(default_markup_bps),
        encode_pubkey(backend_authority),
    )


def build_register_model_data(model_id: str, provider: str, base_cost_per_token: int, features: str) -> bytes:
    return build_instruction_data(
        "register_model",
        encode_string(model_id),
        encode_string(provider),
        encode_u64(base_cost_per_token),
        encode_string(features),
    )


def build_update_platform_fee_data(new_platform_fee_bps: int) -> bytes:
    return build_instruction_data("update_platform_fee", encode_u16(new_platform_fee_bps))


def build_update_default_markup_data(new_default_markup_bps: int) -> bytes:
    return build_instruction_data("update_default_markup", encode_u16(new_default_markup_bps))


def build_update_authority_data(new_authority: str) -> bytes:
    return build_instruction_data("update_authority", encode_pubkey(new_authority))


def build_update_backend_authority_data(new_backend_authority: str) -> bytes:
    return build_instruction_data("update_backend_authority", encode_pubkey(new_backend_authority))


def build_toggle_pause_data() -> bytes:
    return build_instruction_data("toggle_pause")


def build_claim_fees_data(amount: int) -> bytes:
    return build_instruction_data("claim_fees", encode_u64(amount))


def build_update_model_data(
    base_cost_per_token: Optional[int],
    is_active: Optional[bool],
    features: Optional[str],
    custom_contract: Optional[str],
) -> bytes:
    return build_instruction_data(
        "update_model",
        encode_option(base_cost_per_token, encode_u64),
        encode_option(is_active, encode_bool),
        encode_option(features, encode_string),
        encode_option(custom_contract, encode_pubkey),
    )


def build_deactivate_model_data() -> bytes:
    return build_instruction_data("deactivate_model")


def build_initialize_spending_profile_data() -> bytes:
    return build_instruction_data("initialize_spending_profile")


def build_create_delegated_signer_data(expiry_duration: int, spending_limit: int) -> bytes:
    return build_instruction_data(
        "create_delegated_signer",
        encode_i64(expiry_duration),
        encode_u64(spending_limit),
    )


def build_approve_spending_delegate_data() -> bytes:
    return build_instruction_data("approve_spending_delegate")


def build_revoke_spending_delegate_data() -> bytes:
    return build_instruction_data("revoke_spending_delegate")


def build_close_spending_profile_data() -> bytes:
    return build_instruction_data("close_spending_profile")


def build_revoke_delegated_signer_data() -> bytes:
    return build_instruction_data("revoke_delegated_signer")


def build_close_delegated_signer_data() -> bytes:
    return build_instruction_data("close_delegated_signer")


def build_record_ai_usage_data(
    model_id: str,
    base_cost: int,
    service_cost: int,
    usage_type: str,
    tokens_used: int,
    markup_bps: Optional[int],
) -> bytes:
    return build_instruction_data(
        "record_ai_usage",
        encode_string(model_id),
        encode_u64(base_cost),
        encode_u64(service_cost),
        encode_string(usage_type),
        encode_u64(tokens_used),
        encode_option(markup_bps, encode_u16),
    )


def build_record_ai_usage_with_delegation_data(
    model_id: str,
    base_cost: int,
    service_cost: int,
    usage_type: str,
    tokens_used: int,
    markup_bps: Optional[int],
) -> bytes:
    return build_instruction_data(
        "record_ai_usage_with_delegation",
        encode_string(model_id),
        encode_u64(base_cost),
        encode_u64(service_cost),
        encode_string(usage_type),
        encode_u64(tokens_used),
        encode_option(markup_bps, encode_u16),
    )


def build_instruction(
    *,
    instruction_name: str,
    accounts: Sequence[InstructionAccountMetaDef],
    data: bytes,
    program_id: Optional[str] = None,
    cluster: str = "devnet",
):
    """Build a solders Instruction from normalized account metadata."""
    sdk = _load_instruction_sdk()
    resolved_program_id = sdk["Pubkey"].from_string(program_id or get_program_id(cluster))
    metas = [
        sdk["AccountMeta"](
            pubkey=sdk["Pubkey"].from_string(account.pubkey),
            is_signer=account.is_signer,
            is_writable=account.is_writable,
        )
        for account in accounts
    ]
    return sdk["Instruction"](resolved_program_id, data, metas)
