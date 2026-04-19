from agents.market_context import get_market_context_guidance, normalize_market_context


def test_normalize_market_context_supports_locked_asset_and_state():
    normalized = normalize_market_context(
        {
            "scope_mode": "locked_asset",
            "symbol": "BTC",
            "asset_id": "bitcoin",
            "timeframe": "4H",
            "watchlist_symbols": ["BTC", "ETH", ""],
            "market_state": {
                "trend_bias": "bullish",
                "structure_position": "near_resistance",
                "volatility_regime": "high",
                "momentum_state": "weakening",
                "summary": "BTC is testing resistance after a strong move.",
            },
        }
    )

    assert normalized["scope_mode"] == "locked_asset"
    assert normalized["symbol"] == "BTC"
    assert normalized["watchlist_symbols"] == ["BTC", "ETH"]
    assert normalized["market_state"]["trend_bias"] == "bullish"


def test_market_context_guidance_mentions_locked_asset_and_state():
    guidance = get_market_context_guidance(
        {
            "scope_mode": "locked_asset",
            "symbol": "BTC",
            "timeframe": "1H",
            "market_state": {
                "trend_bias": "bearish",
                "structure_position": "near_support",
                "volatility_regime": "medium",
                "momentum_state": "improving",
                "summary": "BTC is stabilizing near support.",
            },
        }
    )

    assert "locked to BTC" in guidance
    assert "1H" in guidance
    assert "trend bias is bearish" in guidance
    assert "BTC is stabilizing near support." in guidance


def test_market_context_supports_news_tail_titles():
    normalized = normalize_market_context(
        {
            "scope_mode": "locked_asset",
            "symbol": "SOL",
            "news_context": {
                "tail_titles": [
                    "SOL breaks above key resistance",
                    "Validator growth supports Solana activity",
                ]
            },
        }
    )

    guidance = get_market_context_guidance(normalized)

    assert normalized["news_context"]["tail_titles"][0] == "SOL breaks above key resistance"
    assert "Recent relevant headlines" in guidance
    assert "Validator growth supports Solana activity" in guidance
