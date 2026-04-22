from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.routes import router


class DummyMarketService:
    def __init__(self):
        self.data = {
            "BTC": SimpleNamespace(
                name="Bitcoin",
                categories=["Layer 1", "Store of Value"],
                description="Bitcoin",
                contract_address=None,
                links=SimpleNamespace(
                    website="https://bitcoin.org",
                    twitter=None,
                    telegram=None,
                    github=None,
                    explorer=None,
                ),
            ),
            "ETH": SimpleNamespace(
                name="Ethereum",
                categories=["Layer 1", "DeFi"],
                description="Ethereum",
                contract_address={"ethereum": "0xeth"},
                links=SimpleNamespace(
                    website="https://ethereum.org",
                    twitter=None,
                    telegram=None,
                    github="https://github.com/ethereum",
                    explorer=None,
                ),
            ),
            "UNI": SimpleNamespace(
                name="Uniswap",
                categories=["DeFi"],
                description="Uniswap",
                contract_address={"ethereum": "0xuni"},
                links=SimpleNamespace(
                    website="https://uniswap.org",
                    twitter=None,
                    telegram=None,
                    github=None,
                    explorer=None,
                ),
            ),
        }

    async def get_coin_info(self, symbol: str):
        return self.data.get(symbol.upper())


class DummyMarketHandler:
    def __init__(self):
        def make_price(**kwargs):
            defaults = {
                "notional_volume_24h": None,
                "base_volume_24h": None,
                "open_interest": None,
                "funding_rate": None,
                "oracle_price": None,
                "premium": None,
                "circulating_supply": None,
                "total_supply": None,
                "max_leverage": None,
                "only_isolated": None,
                "market_pair": None,
                "full_name": None,
                "token_index": None,
                "is_canonical": None,
                "source_exchange": "phantom_futures",
            }
            defaults.update(kwargs)
            return SimpleNamespace(**defaults)

        self.prices = {
            "BTC": make_price(
                price=65000.0,
                change_24h=2.5,
                volume_24h=1000000.0,
                high_24h=65500.0,
                low_24h=64000.0,
                market_cap=1_000_000_000.0,
                fdv=1_100_000_000.0,
                timestamp=SimpleNamespace(isoformat=lambda: "2026-04-18T00:00:00+00:00"),
            ),
            "ETH": make_price(
                price=3200.0,
                change_24h=1.5,
                volume_24h=500000.0,
                high_24h=3300.0,
                low_24h=3100.0,
                market_cap=500_000_000.0,
                fdv=550_000_000.0,
                timestamp=SimpleNamespace(isoformat=lambda: "2026-04-18T00:00:00+00:00"),
            ),
            "UNI": make_price(
                price=12.0,
                change_24h=-0.5,
                volume_24h=100000.0,
                high_24h=12.5,
                low_24h=11.5,
                market_cap=100_000_000.0,
                fdv=110_000_000.0,
                timestamp=SimpleNamespace(isoformat=lambda: "2026-04-18T00:00:00+00:00"),
            ),
        }
        self.exchange_prices = {
            "phantom_spot": {
                "BTC": self.prices["BTC"],
                "ETH": self.prices["ETH"],
            },
            "phantom_futures": {
                "BTC": make_price(
                    price=64900.0,
                    change_24h=2.1,
                    volume_24h=900000.0,
                    high_24h=65200.0,
                    low_24h=64100.0,
                    market_cap=1_000_000_000.0,
                    fdv=1_100_000_000.0,
                    open_interest=2500000.0,
                    funding_rate=0.0001,
                    timestamp=SimpleNamespace(isoformat=lambda: "2026-04-18T00:00:00+00:00"),
                ),
                "UNI": self.prices["UNI"],
            },
        }

    def get_price(self, symbol: str, exchange: str | None = None):
        if exchange:
            return self.exchange_prices.get(exchange, {}).get(symbol.upper())
        return self.prices.get(symbol.upper())


def create_test_client():
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def test_asset_search_categories_and_supported_routes(monkeypatch):
    import main

    monkeypatch.setattr("api.routes.get_market_service", lambda: DummyMarketService())
    monkeypatch.setattr(main, "market_handler", DummyMarketHandler())
    monkeypatch.setattr("api.routes.settings.TRADING_ASSETS", ["BTC", "ETH", "UNI"])

    client = create_test_client()

    search_response = client.get("/api/assets/search", params={"q": "bit"})
    assert search_response.status_code == 200
    search_payload = search_response.json()
    assert search_payload["query"] == "bit"
    assert search_payload["total"] == 1
    assert search_payload["assets"][0]["symbol"] == "BTC"

    category_response = client.get("/api/assets/categories")
    assert category_response.status_code == 200
    category_payload = category_response.json()
    assert category_payload["total"] >= 2
    category_names = [item["name"] for item in category_payload["categories"]]
    assert "DeFi" in category_names
    assert "Layer 1" in category_names

    category_assets_response = client.get("/api/assets/categories/defi")
    assert category_assets_response.status_code == 200
    category_assets_payload = category_assets_response.json()
    assert category_assets_payload["category"] == "DeFi"
    assert category_assets_payload["total"] == 2
    assert [item["symbol"] for item in category_assets_payload["assets"]] == ["ETH", "UNI"]

    supported_response = client.get("/api/assets/supported")
    assert supported_response.status_code == 200
    supported_payload = supported_response.json()
    assert supported_payload["assets"] == ["BTC", "ETH", "UNI"]
    assert supported_payload["total"] == 3

    trending_response = client.get("/api/assets/trending", params={"limit": 2})
    assert trending_response.status_code == 200
    trending_payload = trending_response.json()
    assert trending_payload["total"] == 2
    assert "ranking_method" in trending_payload
    assert trending_payload["assets"][0]["rank"] == 1
    assert trending_payload["assets"][0]["symbol"] == "BTC"
    assert "active 24h volume" in trending_payload["assets"][0]["reasons"]

    summary_response = client.get("/api/assets/ETH/summary", params={"related_limit": 2})
    assert summary_response.status_code == 200
    summary_payload = summary_response.json()
    assert summary_payload["symbol"] == "ETH"
    assert summary_payload["primary_category"] == "Layer 1"
    assert summary_payload["links"]["contract_address"] == "0xeth"
    assert len(summary_payload["related_assets"]) == 2
    assert [item["symbol"] for item in summary_payload["related_assets"]] == ["BTC", "UNI"]

    related_response = client.get("/api/assets/ETH/related", params={"limit": 5})
    assert related_response.status_code == 200
    related_payload = related_response.json()
    assert related_payload["symbol"] == "ETH"
    assert related_payload["primary_category"] == "Layer 1"
    assert related_payload["total"] == 2
    assert [item["symbol"] for item in related_payload["assets"]] == ["BTC", "UNI"]

    futures_assets_response = client.get("/api/assets", params={"exchange": "futures"})
    assert futures_assets_response.status_code == 200
    futures_assets_payload = futures_assets_response.json()
    assert futures_assets_payload["total"] == 2
    assert [item["symbol"] for item in futures_assets_payload["assets"]] == ["BTC", "UNI"]

    spot_search_response = client.get("/api/assets/search", params={"q": "eth", "exchange": "spot"})
    assert spot_search_response.status_code == 200
    spot_search_payload = spot_search_response.json()
    assert spot_search_payload["total"] == 1
    assert spot_search_payload["assets"][0]["symbol"] == "ETH"

    futures_trending_response = client.get("/api/assets/trending", params={"limit": 5, "exchange": "futures"})
    assert futures_trending_response.status_code == 200
    futures_trending_payload = futures_trending_response.json()
    assert [item["symbol"] for item in futures_trending_payload["assets"]] == ["BTC", "UNI"]

    invalid_exchange_response = client.get("/api/assets", params={"exchange": "kraken"})
    assert invalid_exchange_response.status_code == 400
