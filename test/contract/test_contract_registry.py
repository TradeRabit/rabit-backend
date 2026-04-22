"""Tests for the backend-local Rabit contract artifact registry."""
from contract.registry import get_program_id, load_deployment, load_idl
from contract.seeds import MAX_PDA_SEED_BYTES, to_on_chain_model_id


def test_load_devnet_deployment():
    deployment = load_deployment("devnet")

    assert deployment.cluster == "devnet"
    assert deployment.program_id == "Eq7vUXz6hdoYDXgmjNT4HbTtZb43QjenDhMLWdqVcpHT"
    assert deployment.config_pda == "DipGVm96xHJeqJZ6BhJHZEuRkWBptxnecWWHMcRrGAL2"
    assert deployment.seeded_models == deployment.enabled_models == 314
    assert deployment.model_registry_coverage_pct == 100.0


def test_load_idl_matches_deployment_program():
    idl = load_idl()

    assert idl["address"] == get_program_id("devnet")
    assert idl["metadata"]["name"] == "rabit_contract"


def test_to_on_chain_model_id_keeps_short_ids():
    model_id = "anthropic/claude-opus-4.7"
    assert to_on_chain_model_id(model_id) == model_id


def test_to_on_chain_model_id_shortens_long_ids():
    model_id = "provider/" + ("very-long-model-name-" * 8)
    alias = to_on_chain_model_id(model_id)

    assert alias != model_id
    assert len(alias.encode("utf-8")) <= MAX_PDA_SEED_BYTES
    assert alias.startswith("provider/")
