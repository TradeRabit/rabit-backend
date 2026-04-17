import asyncio

from ws.models.coin_info import CoinInfo, CoinLinks
from ws.services.market_service import MarketDataService


class FakeDatabase:
    def get_coin_info(self, symbol):
        return None

    def is_stale(self, symbol, max_age_days=30):
        return True


def test_initialize_coins_retries_until_success():
    service = MarketDataService()
    service.db = FakeDatabase()

    attempts = {"BTC": 0}

    async def fake_get_coin_info(symbol):
        attempts[symbol] += 1
        if attempts[symbol] < 2:
            return None

        return CoinInfo(
            id="bitcoin",
            symbol="BTC",
            name="Bitcoin",
            description="Test",
            links=CoinLinks(),
            categories=[],
        )

    original_sleep = asyncio.sleep

    async def fast_sleep(_seconds):
        return None

    service.get_coin_info = fake_get_coin_info
    asyncio.sleep = fast_sleep
    try:
        asyncio.run(service.initialize_coins(["BTC"]))
    finally:
        asyncio.sleep = original_sleep

    assert attempts["BTC"] == 2
