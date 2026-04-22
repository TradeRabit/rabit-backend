"""Tests for backend-first model registry routes with on-chain enrichment."""
import asyncio
from types import SimpleNamespace

from agents.openrouter.models import ModelInfo
from api.routes import get_model_info, get_models_grouped, get_models_stats, list_models


class DummyModelsManager:
    def __init__(self, models):
        self._models = list(models)

    async def fetch_models(self, force_refresh: bool = False):
        return self._models

    def filter_models(self, **kwargs):
        enabled_only = kwargs.get("enabled_only", True)
        models = self._models
        if enabled_only:
            models = [model for model in models if model.enabled]
        return models

    def get_stats(self):
        return {
            "total_models": len(self._models),
            "enabled_models": len([model for model in self._models if model.enabled]),
            "disabled_models": len([model for model in self._models if not model.enabled]),
            "models_with_tools": len([model for model in self._models if model.supports_tools]),
            "models_with_reasoning": len([model for model in self._models if model.supports_reasoning]),
            "providers": {"anthropic": {"total": len(self._models), "enabled": len(self._models), "with_tools": len(self._models), "with_reasoning": len(self._models)}},
            "last_updated": "2026-04-22T00:00:00",
        }

    def get_model(self, model_id: str):
        for model in self._models:
            if model.id == model_id:
                return model
        return None

    def get_models_by_provider(self, enabled_only: bool = True):
        models = self._models if not enabled_only else [model for model in self._models if model.enabled]
        grouped = {}
        for model in models:
            grouped.setdefault(model.provider, []).append(model)
        return grouped

    def get_providers(self):
        return sorted({model.provider for model in self._models})


class DummyContractRegistryService:
    def enrich_model(self, model_id: str, snapshot):
        return {
            "onchain_registered": model_id == "anthropic/claude-opus-4.7",
            "onchain_model_id": model_id,
            "onchain_model_registry_pda": "dummy-pda",
            "onchain_is_active": True if model_id == "anthropic/claude-opus-4.7" else None,
            "onchain_is_verified": True if model_id == "anthropic/claude-opus-4.7" else None,
            "onchain_base_cost_per_token": 0 if model_id == "anthropic/claude-opus-4.7" else None,
            "onchain_custom_contract": None,
            "onchain_sync_error": None,
        }


async def _return_snapshot(snapshot, force_refresh: bool = False):
    return snapshot


def _make_model():
    return ModelInfo(
        id="anthropic/claude-opus-4.7",
        name="Anthropic: Claude Opus 4.7",
        provider="anthropic",
        description="test",
        context_length=200000,
        input_price=1.0,
        output_price=2.0,
        supports_tools=True,
        supports_reasoning=True,
        enabled=True,
    )


def _make_unregistered_model():
    return ModelInfo(
        id="openai/gpt-4.1-mini",
        name="OpenAI: GPT-4.1 Mini",
        provider="openai",
        description="test",
        context_length=128000,
        input_price=0.2,
        output_price=0.8,
        supports_tools=True,
        supports_reasoning=False,
        enabled=True,
    )


def test_list_models_includes_onchain_fields(monkeypatch):
    manager = DummyModelsManager([_make_model(), _make_unregistered_model()])
    snapshot = SimpleNamespace(
        available=True,
        total_registered=314,
        total_active=314,
        total_verified=314,
        last_updated="2026-04-22T00:00:00",
        error=None,
    )

    monkeypatch.setattr("agents.openrouter.get_openrouter_models", lambda: manager)
    monkeypatch.setattr("agents.openrouter.get_contract_model_registry_service", lambda: DummyContractRegistryService())
    monkeypatch.setattr(
        "api.routes._get_onchain_model_registry_snapshot",
        lambda force_refresh=False: _return_snapshot(snapshot, force_refresh),
    )

    response = asyncio.run(list_models())

    assert response.total == 2
    assert response.onchain_registered_models == 314
    assert response.models[0].onchain_registered is True
    assert response.models[0].onchain_model_registry_pda == "dummy-pda"
    assert response.models[1].provider == "openai"
    assert response.models[1].onchain_registered is False


def test_get_model_info_includes_onchain_fields(monkeypatch):
    manager = DummyModelsManager([_make_model()])
    snapshot = SimpleNamespace(
        available=True,
        total_registered=314,
        total_active=314,
        total_verified=314,
        last_updated="2026-04-22T00:00:00",
        error=None,
    )

    monkeypatch.setattr("agents.openrouter.get_openrouter_models", lambda: manager)
    monkeypatch.setattr("agents.openrouter.get_contract_model_registry_service", lambda: DummyContractRegistryService())
    monkeypatch.setattr(
        "api.routes._get_onchain_model_registry_snapshot",
        lambda force_refresh=False: _return_snapshot(snapshot, force_refresh),
    )

    response = asyncio.run(get_model_info("anthropic/claude-opus-4.7"))

    assert response.onchain_registered is True
    assert response.onchain_is_verified is True


def test_get_models_stats_includes_onchain_fields(monkeypatch):
    manager = DummyModelsManager([_make_model()])
    snapshot = SimpleNamespace(
        available=True,
        total_registered=314,
        total_active=300,
        total_verified=280,
        last_updated="2026-04-22T00:00:00",
        error=None,
    )

    monkeypatch.setattr("agents.openrouter.get_openrouter_models", lambda: manager)
    monkeypatch.setattr(
        "api.routes._get_onchain_model_registry_snapshot",
        lambda force_refresh=False: _return_snapshot(snapshot, force_refresh),
    )

    response = asyncio.run(get_models_stats())

    assert response.onchain_available is True
    assert response.onchain_registered_models == 314
    assert response.onchain_active_models == 300
    assert response.onchain_verified_models == 280


def test_get_models_grouped_preserves_backend_grouping_and_onchain_fields(monkeypatch):
    manager = DummyModelsManager([_make_model(), _make_unregistered_model()])
    snapshot = SimpleNamespace(
        available=True,
        total_registered=314,
        total_active=300,
        total_verified=280,
        last_updated="2026-04-22T00:00:00",
        error=None,
    )

    monkeypatch.setattr("agents.openrouter.get_openrouter_models", lambda: manager)
    monkeypatch.setattr("agents.openrouter.get_contract_model_registry_service", lambda: DummyContractRegistryService())
    monkeypatch.setattr(
        "api.routes._get_onchain_model_registry_snapshot",
        lambda force_refresh=False: _return_snapshot(snapshot, force_refresh),
    )

    response = asyncio.run(get_models_grouped(enabled_only=True))

    assert response["total_providers"] == 2
    assert "anthropic" in response["grouped"]
    assert "openai" in response["grouped"]
    assert response["grouped"]["anthropic"][0].onchain_registered is True
    assert response["grouped"]["openai"][0].onchain_registered is False
    assert response["onchain_active_models"] == 300
