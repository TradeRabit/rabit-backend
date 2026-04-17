import asyncio

from ws.backpack.client import BackpackWSClient


def test_backpack_handles_flattened_ticker_messages():
    client = BackpackWSClient()
    updates = []

    async def on_price_update(price_update):
        updates.append(price_update)

    asyncio.run(client.subscribe("SOL", on_price_update, subscribe_ohlc=False))

    asyncio.run(
        client._handle_message(
            {
                "e": "ticker",
                "E": 1694687692980000,
                "s": "SOL_USDC",
                "o": "18.75",
                "c": "19.24",
                "h": "19.80",
                "l": "18.50",
                "v": "32123",
                "V": "928190",
                "n": 93828,
            }
        )
    )

    assert len(updates) == 1
    assert updates[0].symbol == "SOL"
    assert updates[0].price == 19.24
    assert updates[0].high_24h == 19.80


def test_backpack_handles_flattened_trade_messages():
    client = BackpackWSClient()
    updates = []

    async def on_price_update(price_update):
        updates.append(price_update)

    asyncio.run(client.subscribe("BTC", on_price_update, subscribe_ohlc=False))

    asyncio.run(
        client._handle_message(
            {
                "e": "trade",
                "E": 1694688638091000,
                "s": "BTC_USDC",
                "p": "65000.50",
                "q": "0.122",
                "m": True,
            }
        )
    )

    assert len(updates) == 1
    assert updates[0].symbol == "BTC"
    assert updates[0].price == 65000.50


def test_backpack_handles_flattened_kline_messages():
    client = BackpackWSClient()
    candles = []

    async def on_ohlc_update(ohlc_data, interval):
        candles.append((ohlc_data, interval))

    client.subscribe_ohlc("SOL", on_ohlc_update)

    asyncio.run(
        client._handle_message(
            {
                "e": "kline",
                "E": 1694687692980000,
                "s": "SOL_USDC",
                "i": "1m",
                "t": "2024-09-11T12:00:00",
                "T": "2024-09-11T12:01:00",
                "o": "18.75",
                "c": "19.25",
                "h": "19.80",
                "l": "18.50",
                "v": "32123",
                "X": False,
            }
        )
    )

    assert len(candles) == 1
    assert candles[0][0].symbol == "SOL"
    assert candles[0][0].close == 19.25
    assert candles[0][1] == "1m"


def test_backpack_ignores_incomplete_kline_messages():
    client = BackpackWSClient()
    candles = []

    async def on_ohlc_update(ohlc_data, interval):
        candles.append((ohlc_data, interval))

    client.subscribe_ohlc("SOL", on_ohlc_update)

    asyncio.run(
        client._handle_message(
            {
                "e": "kline",
                "s": "SOL_USDC",
                "i": "1m",
                "t": "2024-09-11T12:00:00",
                "o": "18.75",
                "c": None,
                "h": "19.80",
                "l": "18.50",
                "v": "32123",
            }
        )
    )

    assert candles == []
