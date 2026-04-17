import asyncio

from ws.drift.client import DriftWSClient


def test_drift_handles_candle_payload():
    client = DriftWSClient()
    updates = []
    candles = []

    async def on_price_update(price_update):
        updates.append(price_update)

    async def on_ohlc_update(ohlc_data, interval):
        candles.append((ohlc_data, interval))

    asyncio.run(client.subscribe("SOL", on_price_update))
    client.subscribe_ohlc("SOL", on_ohlc_update)

    asyncio.run(
        client._handle_message(
            {
                "symbol": "SOL-PERP",
                "resolution": "1",
                "open": 100.0,
                "high": 105.0,
                "low": 99.0,
                "close": 103.5,
                "volume": 1234.0,
                "startTime": 1710000000000,
            }
        )
    )

    assert len(updates) == 1
    assert updates[0].symbol == "SOL"
    assert updates[0].price == 103.5
    assert len(candles) == 1
    assert candles[0][1] == "1"
    assert candles[0][0].close == 103.5


def test_drift_handles_dlob_trade_payload():
    client = DriftWSClient()
    updates = []

    async def on_price_update(price_update):
        updates.append(price_update)

    asyncio.run(client.subscribe("SOL", on_price_update, subscribe_ohlc=False))

    asyncio.run(
        client._handle_dlob_message(
            {
                "channel": "trades",
                "market": "SOL-PERP",
                "data": [
                    {"price": 131.25, "size": 2.0},
                ],
            }
        )
    )

    assert len(updates) == 1
    assert updates[0].symbol == "SOL"
    assert updates[0].price == 131.25


def test_drift_handles_dlob_orderbook_payload():
    client = DriftWSClient()
    updates = []

    async def on_price_update(price_update):
        updates.append(price_update)

    asyncio.run(client.subscribe("SOL", on_price_update, subscribe_ohlc=False))

    asyncio.run(
        client._handle_dlob_message(
            {
                "channel": "orderbook",
                "market": "SOL-PERP",
                "data": {
                    "bids": [{"price": 130.0, "size": 5}],
                    "asks": [{"price": 132.0, "size": 7}],
                },
            }
        )
    )

    assert len(updates) == 1
    assert updates[0].symbol == "SOL"
    assert updates[0].price == 131.0
