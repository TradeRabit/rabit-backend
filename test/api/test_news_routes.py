from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.routes import router


def create_test_client():
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


class DummyNewsClient:
    def search_news_by_symbols(self, symbols, max_results=5):
        symbol = symbols[0]
        return {
            symbol: [
                {
                    "title": f"{symbol} headline one",
                    "url": f"https://example.com/{symbol.lower()}-1",
                    "snippet": f"{symbol} snippet one",
                    "date": "2026-04-19T00:00:00Z",
                    "detected_at": "2026-04-19T00:05:00Z",
                    "source": "Example",
                    "symbol": symbol,
                },
                {
                    "title": f"{symbol} headline two",
                    "url": f"https://example.com/{symbol.lower()}-2",
                    "snippet": f"{symbol} snippet two",
                    "date": "2026-04-19T01:00:00Z",
                    "detected_at": "2026-04-19T01:05:00Z",
                    "source": "Example",
                    "symbol": symbol,
                },
            ][:max_results]
        }


class DummyNewsMonitor:
    def __init__(self):
        import asyncio

        self.running = False
        self.poll_interval = 300
        self.requested_symbols = []
        self.queue = asyncio.Queue()
        self.unsubscribed = False

    async def start(self):
        self.running = True

    def ensure_symbols(self, symbols):
        self.requested_symbols = list(symbols)

    def subscribe(self):
        return self.queue

    def unsubscribe(self, queue):
        self.unsubscribed = queue is self.queue

    def get_asset_news_snapshot(self, symbols=None, tail=5):
        symbols = symbols or ["BTC"]
        return {
            symbol: [
                {
                    "title": f"{symbol} snapshot",
                    "url": f"https://example.com/{symbol.lower()}-snapshot",
                    "snippet": f"{symbol} snapshot snippet",
                    "date": "2026-04-19T00:00:00Z",
                    "detected_at": "2026-04-19T00:02:00Z",
                    "source": "Snapshot",
                    "symbols": [symbol],
                }
            ][:tail]
            for symbol in symbols
        }


def test_get_asset_news_snapshot(monkeypatch):
    client = create_test_client()
    monkeypatch.setattr("agents.tools.market.news_tools.get_news_client", lambda: DummyNewsClient())

    response = client.get("/api/news/assets/BTC?limit=2")

    assert response.status_code == 200
    payload = response.json()
    assert payload["timestamp"]
    assert payload["symbol"] == "BTC"
    assert payload["total"] == 2
    assert payload["news"][0]["title"] == "BTC headline one"
    assert payload["news"][0]["date"] == "2026-04-19T00:00:00Z"
    assert payload["news"][0]["detected_at"] == "2026-04-19T00:05:00Z"
    assert isinstance(payload["news"][0]["freshness_seconds"], int)
    assert payload["news"][0]["freshness_seconds"] >= 0
    assert payload["news"][0]["is_new"] is True


def test_websocket_news_returns_snapshot_and_filtered_updates(monkeypatch):
    client = create_test_client()
    monitor = DummyNewsMonitor()
    monitor.queue.put_nowait(
        {
            "type": "news_update",
            "timestamp": "2026-04-19T02:00:00Z",
            "count": 2,
            "news": [
                {
                    "title": "BTC update",
                    "url": "https://example.com/btc-update",
                    "snippet": "BTC moving",
                    "date": "2026-04-19T02:00:00Z",
                    "detected_at": "2026-04-19T02:03:00Z",
                    "source": "Feed",
                    "symbols": ["BTC"],
                },
                {
                    "title": "ETH update",
                    "url": "https://example.com/eth-update",
                    "snippet": "ETH moving",
                    "date": "2026-04-19T02:00:00Z",
                    "source": "Feed",
                    "symbols": ["ETH"],
                },
            ],
            "stats": {},
        }
    )
    monkeypatch.setattr("api.routes.get_news_monitor", lambda: monitor)

    with client.websocket_connect("/api/ws/news?symbols=BTC&tail=5") as websocket:
        snapshot = websocket.receive_json()
        update = websocket.receive_json()

    assert snapshot["type"] == "news_snapshot"
    assert snapshot["timestamp"]
    assert snapshot["symbols"] == ["BTC"]
    assert snapshot["news_by_symbol"]["BTC"][0]["title"] == "BTC snapshot"
    assert snapshot["news_by_symbol"]["BTC"][0]["detected_at"] == "2026-04-19T00:02:00Z"
    assert isinstance(snapshot["news_by_symbol"]["BTC"][0]["freshness_seconds"], int)
    assert snapshot["news_by_symbol"]["BTC"][0]["freshness_seconds"] >= 0
    assert snapshot["news_by_symbol"]["BTC"][0]["is_new"] is True

    assert update["type"] == "news_update"
    assert update["timestamp"] == "2026-04-19T02:00:00Z"
    assert update["symbols"] == ["BTC"]
    assert update["count"] == 1
    assert update["news"][0]["title"] == "BTC update"
    assert update["news"][0]["date"] == "2026-04-19T02:00:00Z"
    assert update["news"][0]["detected_at"] == "2026-04-19T02:03:00Z"
    assert isinstance(update["news"][0]["freshness_seconds"], int)
    assert update["news"][0]["freshness_seconds"] >= 0
    assert update["news"][0]["is_new"] is True
    assert monitor.requested_symbols == ["BTC"]
    assert monitor.unsubscribed is True
