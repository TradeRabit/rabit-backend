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
        self.prices = {
            "BTC": SimpleNamespace(
                price=65000.0,
                change_24h=2.5,
                volume_24h=1000000.0,
                high_24h=65500.0,
                low_24h=64000.0,
                market_cap=1_000_000_000.0,
                fdv=1_100_000_000.0,
                open_interest=None,
                funding_rate=None,
                timestamp=SimpleNamespace(isoformat=lambda: "2026-04-18T00:00:00+00:00"),
            ),
            "ETH": SimpleNamespace(
                price=3200.0,
                change_24h=1.5,
                volume_24h=500000.0,
                high_24h=3300.0,
                low_24h=3100.0,
                market_cap=500_000_000.0,
                fdv=550_000_000.0,
                open_interest=None,
                funding_rate=None,
                timestamp=SimpleNamespace(isoformat=lambda: "2026-04-18T00:00:00+00:00"),
            ),
            "UNI": SimpleNamespace(
                price=12.0,
                change_24h=-0.5,
                volume_24h=100000.0,
                high_24h=12.5,
                low_24h=11.5,
                market_cap=100_000_000.0,
                fdv=110_000_000.0,
                open_interest=None,
                funding_rate=None,
                timestamp=SimpleNamespace(isoformat=lambda: "2026-04-18T00:00:00+00:00"),
            ),
        }

    def get_price(self, symbol: str):
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

    supported_response = client.get("/api/assets/supported")
    assert supported_response.status_code == 200
    supported_payload = supported_response.json()
    assert supported_payload["assets"] == ["BTC", "ETH", "UNI"]
    assert supported_payload["total"] == 3
