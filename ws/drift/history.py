"""Drift Protocol historical OHLC data downloader"""
import aiohttp
import asyncio
from typing import List, Optional
from datetime import datetime
from config.settings import settings
from utils.logger import get_logger
from ws.models import OHLCData
from ws.database import get_ohlc_database

logger = get_logger(__name__)


class DriftHistoryDownloader:
    """Download historical OHLC data from Drift Protocol"""

    def __init__(self, auto_save: bool = True):
        """
        Initialize Drift history downloader
        
        Args:
            auto_save: Automatically save downloaded data to database
        """
        # Drift doesn't have a public REST API for historical OHLC data
        # This is a placeholder for future implementation
        self.api_url = "https://drift-mainnet.rpc.drift.trade"  # Placeholder
        self.limit = 100
        self.auto_save = auto_save
        self.db = get_ohlc_database() if auto_save else None

    async def download_ohlc(
        self,
        symbol: str,
        interval: str = "1h",
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[OHLCData]:
        """
        Download OHLC data from Drift

        Args:
            symbol: Trading symbol (e.g., SOL, BTC)
            interval: Candle interval (e.g., 1m, 5m, 1h, 1d)
            start_time: Start time for data
            end_time: End time for data
            limit: Number of candles to download

        Returns:
            List of OHLC data
        """
        try:
            if limit is None:
                limit = self.limit

            # Normalize symbol
            base_symbol = symbol.split("-")[0].split("_")[0].upper()

            logger.info(f"Downloading {limit} {interval} candles for {base_symbol}")

            # TODO: Implement actual API call when Drift provides REST API
            # For now, return empty list
            logger.warning("Drift historical data API not yet available")
            
            # If auto_save enabled and data exists, it would be saved here
            # if self.auto_save and self.db and ohlc_list:
            #     self.db.save_candles(
            #         symbol=base_symbol,
            #         exchange="drift",
            #         interval=interval,
            #         candles=ohlc_list,
            #         merge=True
            #     )
            
            return []

        except Exception as e:
            logger.error(f"Error downloading OHLC data: {str(e)}")
            return []

    async def download_multiple(
        self,
        symbols: List[str],
        interval: str = "1h",
        limit: Optional[int] = None
    ) -> dict:
        """
        Download OHLC data for multiple symbols

        Args:
            symbols: List of trading symbols
            interval: Candle interval
            limit: Number of candles per symbol

        Returns:
            Dictionary with symbol as key and OHLC list as value
        """
        tasks = [
            self.download_ohlc(symbol, interval=interval, limit=limit)
            for symbol in symbols
        ]

        results = await asyncio.gather(*tasks)

        return {
            symbol: ohlc_list
            for symbol, ohlc_list in zip(symbols, results)
        }
