"""Binance historical OHLC data downloader"""
import aiohttp
import asyncio
from typing import List, Optional
from datetime import datetime, timedelta
from config.settings import settings
from utils.logger import get_logger
from ws.models import OHLCData
from ws.database import get_ohlc_database
from ws.utils import get_interval_ms

logger = get_logger(__name__)


class BinanceHistoryDownloader:
    """Download historical OHLC data from Binance"""
    
    def __init__(self, auto_save: bool = True):
        """
        Initialize Binance history downloader
        
        Args:
            auto_save: Automatically save downloaded data to database
        """
        self.api_url = settings.BINANCE_API_URL
        self.interval = settings.BINANCE_OHLC_INTERVAL
        self.limit = settings.BINANCE_OHLC_DOWNLOAD_LIMIT
        self.auto_save = auto_save
        self.db = get_ohlc_database() if auto_save else None
    
    async def download_ohlc(
        self,
        symbol: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[OHLCData]:
        """
        Download OHLC data from Binance
        
        Args:
            symbol: Trading symbol (e.g., SOLUSDT, BTCUSDT)
            start_time: Start time for data
            end_time: End time for data
            limit: Number of candles to download
            
        Returns:
            List of OHLC data
        """
        try:
            if limit is None:
                limit = self.limit
            
            # Default to last N candles if no time specified
            if start_time is None and end_time is None:
                logger.info(f"Downloading last {limit} {self.interval} candles for {symbol}")
            else:
                logger.info(f"Downloading OHLC data for {symbol} from {start_time} to {end_time}")
            
            params = {
                "symbol": symbol,
                "interval": self.interval,
                "limit": limit
            }
            
            if start_time:
                params["startTime"] = int(start_time.timestamp() * 1000)
            
            if end_time:
                params["endTime"] = int(end_time.timestamp() * 1000)
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.api_url}/api/v3/klines",
                    params=params
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        ohlc_list = []
                        
                        for candle in data:
                            ohlc = OHLCData(
                                symbol=symbol,
                                timestamp=int(candle[0]),
                                open=float(candle[1]),
                                high=float(candle[2]),
                                low=float(candle[3]),
                                close=float(candle[4]),
                                volume=float(candle[5]),
                                quote_asset_volume=float(candle[7]),
                                number_of_trades=int(candle[8]),
                                taker_buy_base_asset_volume=float(candle[9]),
                                taker_buy_quote_asset_volume=float(candle[10])
                            )
                            ohlc_list.append(ohlc)
                        
                        logger.info(f"Downloaded {len(ohlc_list)} candles for {symbol}")
                        
                        # Auto-save to database
                        if self.auto_save and self.db and ohlc_list:
                            # Extract base symbol (e.g., "SOLUSDT" -> "SOL")
                            base_symbol = symbol.replace("USDT", "").replace("USDC", "").replace("BUSD", "")
                            self.db.save_candles(
                                symbol=base_symbol,
                                exchange="binance",
                                interval=self.interval,
                                candles=ohlc_list,
                                merge=True
                            )
                        
                        return ohlc_list
                    else:
                        logger.error(f"Error downloading OHLC data: {response.status}")
                        return []
        
        except Exception as e:
            logger.error(f"Error downloading OHLC data: {str(e)}")
            return []
    
    async def download_multiple(
        self,
        symbols: List[str],
        limit: Optional[int] = None
    ) -> dict:
        """
        Download OHLC data for multiple symbols
        
        Args:
            symbols: List of trading symbols
            limit: Number of candles per symbol
            
        Returns:
            Dictionary with symbol as key and OHLC list as value
        """
        tasks = [
            self.download_ohlc(symbol, limit=limit)
            for symbol in symbols
        ]
        
        results = await asyncio.gather(*tasks)
        
        return {
            symbol: ohlc_list
            for symbol, ohlc_list in zip(symbols, results)
        }
    
    def get_interval_ms(self) -> int:
        """Get interval in milliseconds"""
        return get_interval_ms(self.interval)
