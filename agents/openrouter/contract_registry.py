"""On-chain enrichment for the backend OpenRouter model catalog."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

from contract import derive_model_registry_pda, get_rabit_contract_sdk, to_on_chain_model_id
from contract.models import ModelRegistryAccount
from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class OnchainModelRegistrySnapshot:
    """Cached view of the Rabit on-chain model registry."""

    accounts_by_pda: dict[str, ModelRegistryAccount]
    total_registered: int
    total_active: int
    total_verified: int
    last_updated: Optional[str]
    available: bool
    error: Optional[str] = None


class ContractModelRegistryService:
    """Resolve and cache contract-backed model registry state for API enrichment."""

    CACHE_TTL_SECONDS = 120

    def __init__(self) -> None:
        self._snapshot: Optional[OnchainModelRegistrySnapshot] = None
        self._snapshot_expires_at: Optional[datetime] = None

    async def get_snapshot(self, *, force_refresh: bool = False) -> OnchainModelRegistrySnapshot:
        """Return a cached on-chain model registry snapshot."""
        now = datetime.utcnow()
        if (
            not force_refresh
            and self._snapshot is not None
            and self._snapshot_expires_at is not None
            and now < self._snapshot_expires_at
        ):
            return self._snapshot

        try:
            sdk = get_rabit_contract_sdk()
            accounts = await sdk.list_model_registry_accounts()
            accounts_by_pda = {pda: account for pda, account in accounts}
            snapshot = OnchainModelRegistrySnapshot(
                accounts_by_pda=accounts_by_pda,
                total_registered=len(accounts_by_pda),
                total_active=sum(1 for account in accounts_by_pda.values() if account.is_active),
                total_verified=sum(1 for account in accounts_by_pda.values() if account.is_verified),
                last_updated=now.isoformat(),
                available=True,
                error=None,
            )
        except Exception as exc:
            logger.warning(f"On-chain model registry snapshot unavailable: {exc}")
            snapshot = OnchainModelRegistrySnapshot(
                accounts_by_pda={},
                total_registered=0,
                total_active=0,
                total_verified=0,
                last_updated=now.isoformat(),
                available=False,
                error=str(exc),
            )

        self._snapshot = snapshot
        self._snapshot_expires_at = now + timedelta(seconds=self.CACHE_TTL_SECONDS)
        return snapshot

    @staticmethod
    def enrich_model(model_id: str, snapshot: OnchainModelRegistrySnapshot) -> dict:
        """Return one model's on-chain fields derived from the cached snapshot."""
        try:
            onchain_model_id = to_on_chain_model_id(model_id)
            model_registry_pda, _ = derive_model_registry_pda(model_id)
        except Exception as exc:
            return {
                "onchain_registered": False,
                "onchain_model_id": None,
                "onchain_model_registry_pda": None,
                "onchain_is_active": None,
                "onchain_is_verified": None,
                "onchain_base_cost_per_token": None,
                "onchain_custom_contract": None,
                "onchain_sync_error": str(exc),
            }

        account = snapshot.accounts_by_pda.get(model_registry_pda)
        return {
            "onchain_registered": account is not None,
            "onchain_model_id": onchain_model_id,
            "onchain_model_registry_pda": model_registry_pda,
            "onchain_is_active": account.is_active if account else None,
            "onchain_is_verified": account.is_verified if account else None,
            "onchain_base_cost_per_token": account.base_cost_per_token if account else None,
            "onchain_custom_contract": account.custom_contract if account else None,
            "onchain_sync_error": None if snapshot.available else snapshot.error,
        }


_contract_model_registry_service: Optional[ContractModelRegistryService] = None


def get_contract_model_registry_service() -> ContractModelRegistryService:
    """Return singleton on-chain registry enrichment service."""
    global _contract_model_registry_service
    if _contract_model_registry_service is None:
        _contract_model_registry_service = ContractModelRegistryService()
    return _contract_model_registry_service


__all__ = [
    "ContractModelRegistryService",
    "OnchainModelRegistrySnapshot",
    "get_contract_model_registry_service",
]
