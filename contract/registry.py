"""Source-of-truth loaders for Rabit contract artifacts in the backend repo."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from .models import ContractDeployment


CONTRACT_DIR = Path(__file__).resolve().parent
IDL_PATH = CONTRACT_DIR / "idl" / "rabit_contract.json"
DEPLOYMENTS_DIR = CONTRACT_DIR / "deployments"


def get_contract_root() -> Path:
    """Return the backend-local contract artifact root."""
    return CONTRACT_DIR


@lru_cache(maxsize=1)
def load_idl() -> dict[str, Any]:
    """Load the bundled Rabit contract IDL."""
    with IDL_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


@lru_cache(maxsize=8)
def load_deployment(cluster: str = "devnet") -> ContractDeployment:
    """Load one deployment descriptor by cluster name."""
    normalized_cluster = str(cluster or "devnet").strip().lower()
    file_path = DEPLOYMENTS_DIR / f"{normalized_cluster}.json"
    if not file_path.exists():
        raise FileNotFoundError(
            f"Contract deployment metadata for cluster '{normalized_cluster}' was not found at {file_path}."
        )

    with file_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    known_keys = {
        "cluster",
        "program_id",
        "config_pda",
        "fee_recipient_pda",
        "authority_wallet",
        "backend_authority_wallet",
        "init_config_signature",
        "sample_seeded_model_id",
        "sample_seeded_model_pda",
        "sample_model_seed_signature",
        "enabled_models",
        "seeded_models",
        "model_registry_coverage_pct",
        "verified_at",
        "verification_source",
    }
    extra = {key: value for key, value in payload.items() if key not in known_keys}
    return ContractDeployment(
        cluster=payload["cluster"],
        program_id=payload["program_id"],
        config_pda=payload["config_pda"],
        fee_recipient_pda=payload["fee_recipient_pda"],
        authority_wallet=payload.get("authority_wallet"),
        backend_authority_wallet=payload.get("backend_authority_wallet"),
        init_config_signature=payload.get("init_config_signature"),
        sample_seeded_model_id=payload.get("sample_seeded_model_id"),
        sample_seeded_model_pda=payload.get("sample_seeded_model_pda"),
        sample_model_seed_signature=payload.get("sample_model_seed_signature"),
        enabled_models=int(payload.get("enabled_models", 0)),
        seeded_models=int(payload.get("seeded_models", 0)),
        model_registry_coverage_pct=float(payload.get("model_registry_coverage_pct", 0.0)),
        verified_at=payload.get("verified_at"),
        verification_source=payload.get("verification_source"),
        extra=extra,
    )


def get_program_id(cluster: str = "devnet") -> str:
    """Return the Rabit program ID for one cluster."""
    return load_deployment(cluster).program_id
