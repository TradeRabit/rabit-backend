"""Seed and discriminator helpers for the Rabit Solana program."""
from __future__ import annotations

import hashlib
import re
from typing import Optional

from .registry import get_program_id


CONFIG_SEED = b"config"
FEE_RECIPIENT_SEED = b"fee_recipient"
SPENDING_PROFILE_SEED = b"spending_profile"
DELEGATED_SIGNER_SEED = b"delegated_signer"
AI_USAGE_SEED = b"ai_usage"
MODEL_REGISTRY_SEED = b"model_registry"
MAX_PDA_SEED_BYTES = 32
TOKEN_PROGRAM_ID = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
ASSOCIATED_TOKEN_PROGRAM_ID = "ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL"
SYSTEM_PROGRAM_ID = "11111111111111111111111111111111"


def _load_pubkey_sdk():
    try:
        from solders.pubkey import Pubkey
    except ImportError as exc:
        raise ValueError(
            "Rabit contract helpers require optional Solana dependencies. "
            "Install them before using the on-chain contract SDK."
        ) from exc
    return Pubkey


def _normalize_alias_segment(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9-]+", "-", str(value or "").lower())
    normalized = re.sub(r"-+", "-", normalized).strip("-")
    return normalized


def to_on_chain_model_id(model_id: str) -> str:
    """Shorten long model IDs into a PDA-safe alias, matching the contract tooling."""
    normalized = str(model_id or "").strip()
    if len(normalized.encode("utf-8")) <= MAX_PDA_SEED_BYTES:
        return normalized

    provider_raw, _, remainder_raw = normalized.partition("/")
    provider = _normalize_alias_segment(provider_raw or "model") or "model"
    remainder = _normalize_alias_segment(remainder_raw.replace("/", "-")) or "model"
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:6]
    reserved = len(provider) + 1 + 1 + len(digest)
    available = max(1, MAX_PDA_SEED_BYTES - reserved)
    shortened = remainder[:available].rstrip("-") or "m"
    alias = f"{provider}/{shortened}-{digest}"

    if len(alias.encode("utf-8")) > MAX_PDA_SEED_BYTES:
        raise ValueError(f"Could not build safe on-chain alias for model id: {model_id}")
    return alias


def instruction_discriminator(name: str) -> bytes:
    return hashlib.sha256(f"global:{name}".encode("utf-8")).digest()[:8]


def account_discriminator(name: str) -> bytes:
    return hashlib.sha256(f"account:{name}".encode("utf-8")).digest()[:8]


def find_program_address(*seeds: bytes, program_id: Optional[str] = None, cluster: str = "devnet") -> tuple[str, int]:
    """Derive one PDA and return a base58 string plus bump."""
    pubkey_cls = _load_pubkey_sdk()
    resolved_program_id = pubkey_cls.from_string(program_id or get_program_id(cluster))
    derived_pubkey, bump = pubkey_cls.find_program_address(list(seeds), resolved_program_id)
    return str(derived_pubkey), int(bump)


def derive_config_pda(*, cluster: str = "devnet", program_id: Optional[str] = None) -> tuple[str, int]:
    return find_program_address(CONFIG_SEED, program_id=program_id, cluster=cluster)


def derive_fee_recipient_pda(*, cluster: str = "devnet", program_id: Optional[str] = None) -> tuple[str, int]:
    return find_program_address(FEE_RECIPIENT_SEED, program_id=program_id, cluster=cluster)


def derive_spending_profile_pda(owner: str, *, cluster: str = "devnet", program_id: Optional[str] = None) -> tuple[str, int]:
    pubkey_cls = _load_pubkey_sdk()
    return find_program_address(
        SPENDING_PROFILE_SEED,
        bytes(pubkey_cls.from_string(owner)),
        program_id=program_id,
        cluster=cluster,
    )


def derive_delegated_signer_pda(
    owner: str,
    delegate: str,
    *,
    cluster: str = "devnet",
    program_id: Optional[str] = None,
) -> tuple[str, int]:
    pubkey_cls = _load_pubkey_sdk()
    return find_program_address(
        DELEGATED_SIGNER_SEED,
        bytes(pubkey_cls.from_string(owner)),
        bytes(pubkey_cls.from_string(delegate)),
        program_id=program_id,
        cluster=cluster,
    )


def derive_ai_usage_pda(
    spending_profile: str,
    usage_sequence: int,
    *,
    cluster: str = "devnet",
    program_id: Optional[str] = None,
) -> tuple[str, int]:
    pubkey_cls = _load_pubkey_sdk()
    return find_program_address(
        AI_USAGE_SEED,
        bytes(pubkey_cls.from_string(spending_profile)),
        int(usage_sequence).to_bytes(8, "little", signed=False),
        program_id=program_id,
        cluster=cluster,
    )


def derive_model_registry_pda(
    model_id: str,
    *,
    cluster: str = "devnet",
    program_id: Optional[str] = None,
) -> tuple[str, int]:
    on_chain_model_id = to_on_chain_model_id(model_id)
    return find_program_address(
        MODEL_REGISTRY_SEED,
        on_chain_model_id.encode("utf-8"),
        program_id=program_id,
        cluster=cluster,
    )


def derive_associated_token_account(owner: str, mint: str) -> str:
    """Derive the SPL associated token account for one owner and mint."""
    pubkey_cls = _load_pubkey_sdk()
    ata, _ = pubkey_cls.find_program_address(
        [
            bytes(pubkey_cls.from_string(owner)),
            bytes(pubkey_cls.from_string(TOKEN_PROGRAM_ID)),
            bytes(pubkey_cls.from_string(mint)),
        ],
        pubkey_cls.from_string(ASSOCIATED_TOKEN_PROGRAM_ID),
    )
    return str(ata)
