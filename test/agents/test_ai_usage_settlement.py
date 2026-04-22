from agents.ai_usage_settlement import build_onchain_ai_usage_preview


def test_build_onchain_ai_usage_preview_converts_usd_into_contract_units(monkeypatch):
    monkeypatch.setattr("config.settings.settings.RABIT_AI_USAGE_PAYMENT_MINT", "So11111111111111111111111111111111111111112")
    monkeypatch.setattr("config.settings.settings.RABIT_AI_USAGE_PAYMENT_TOKEN_SYMBOL", "USDC")
    monkeypatch.setattr("config.settings.settings.RABIT_AI_USAGE_PAYMENT_MINT_DECIMALS", 6)
    monkeypatch.setattr("config.settings.settings.RABIT_AI_USAGE_PAYMENT_TOKEN_USD_PRICE", 1.0)
    monkeypatch.setattr("config.settings.settings.RABIT_AI_USAGE_PLATFORM_FEE_BPS", 500)
    monkeypatch.setattr("config.settings.settings.RABIT_AI_USAGE_DEFAULT_MARKUP_BPS", 500)
    monkeypatch.setattr("config.settings.settings.RABIT_AI_USAGE_DEFAULT_USAGE_TYPE", "text")

    preview = build_onchain_ai_usage_preview(
        scope_id="scope-1",
        user_id="wallet:HfMHdkJuHztBm1y2JpPfZwauqesZQdmenQaHVL3J9wMP",
        session_cost={
            "scope_id": "scope-1",
            "user_id": "wallet:HfMHdkJuHztBm1y2JpPfZwauqesZQdmenQaHVL3J9wMP",
            "estimated_cost_usd": 0.0123,
            "total_tokens": 3900,
            "model_ids": ["anthropic/claude-3.5-sonnet"],
        },
        monitoring_cost={
            "scope_id": "scope-1",
            "user_id": "wallet:HfMHdkJuHztBm1y2JpPfZwauqesZQdmenQaHVL3J9wMP",
            "total_cost_usd": 0.0115,
        },
    )

    assert preview is not None
    assert preview["owner_wallet_address"] == "HfMHdkJuHztBm1y2JpPfZwauqesZQdmenQaHVL3J9wMP"
    assert preview["model_id"] == "anthropic/claude-3.5-sonnet"
    assert preview["base_cost_units"] == 12300
    assert preview["service_cost_units"] == 11500
    assert preview["chargeable_cost_units"] == 23800
    assert preview["markup_amount_units"] == 1190
    assert preview["platform_fee_amount_units"] == 1249
    assert preview["total_charged_units"] == 26239
    assert preview["instruction_buildable"] is True
    assert preview["instruction_name"] == "record_ai_usage_with_delegation"
    assert preview["spending_profile_pda"] is not None
    assert preview["delegated_signer_pda"] is not None
