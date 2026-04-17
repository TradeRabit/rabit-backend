import asyncio

from config.settings import settings
from ws.handlers import MarketDataHandler
from ws.models import OHLCData


class TestPriceSourceSettings:
    def test_get_price_sources_backpack(self):
        original = settings.PRICE_SOURCE
        original_backpack_enabled = settings.BACKPACK_ENABLED
        try:
            settings.PRICE_SOURCE = "backpack"
            settings.BACKPACK_ENABLED = True
            assert settings.get_price_sources() == ["backpack"]
        finally:
            settings.PRICE_SOURCE = original
            settings.BACKPACK_ENABLED = original_backpack_enabled

    def test_get_price_sources_both(self):
        original = settings.PRICE_SOURCE
        original_backpack_enabled = settings.BACKPACK_ENABLED
        try:
            settings.PRICE_SOURCE = "both"
            settings.BACKPACK_ENABLED = True
            assert settings.get_price_sources() == ["backpack", "drift"]
        finally:
            settings.PRICE_SOURCE = original
            settings.BACKPACK_ENABLED = original_backpack_enabled

    def test_get_price_sources_filters_disabled_backpack(self):
        original = settings.PRICE_SOURCE
        original_backpack_enabled = settings.BACKPACK_ENABLED
        try:
            settings.PRICE_SOURCE = "both"
            settings.BACKPACK_ENABLED = False
            assert settings.get_price_sources() == ["drift"]
        finally:
            settings.PRICE_SOURCE = original
            settings.BACKPACK_ENABLED = original_backpack_enabled


class TestMarketDataHandlerExchangeAware:
    def test_on_ohlc_update_from_exchange_saves_with_explicit_exchange(self):
        handler = MarketDataHandler(auto_save_ohlc=False)
        ohlc = OHLCData(
            symbol="SOL",
            timestamp=1710000000000,
            open=100.0,
            high=110.0,
            low=95.0,
            close=105.0,
            volume=1234.0,
        )

        asyncio.run(handler.on_ohlc_update_from_exchange("drift", ohlc, "1h"))

        stored = handler.get_ohlc("SOL", interval="1h")
        assert len(stored) == 1
        assert stored[0].close == 105.0
