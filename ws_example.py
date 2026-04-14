"""WebSocket usage examples"""
import asyncio
from ws import (
    DriftWSClient,
    BinanceClient,
    BinanceHistoryDownloader,
    MarketDataHandler
)
from utils.logger import get_logger

logger = get_logger(__name__)


async def example_drift_prices():
    """Example: Subscribe to Drift price updates"""
    logger.info("\n=== Example 1: Drift Price Updates ===")
    
    drift_client = DriftWSClient()
    handler = MarketDataHandler()
    
    try:
        # Connect
        await drift_client.connect()
        
        # Subscribe to a few symbols
        symbols = ["SOL", "BTC", "ETH"]
        for symbol in symbols:
            await drift_client.subscribe(symbol, handler.on_price_update)
        
        # Wait for updates
        logger.info("Listening for price updates (10 seconds)...")
        await asyncio.sleep(10)
        
        # Get latest prices
        logger.info("\nLatest prices:")
        for symbol in symbols:
            price = handler.get_price(symbol)
            if price:
                logger.info(f"  {symbol}: ${price.price} (24h: {price.change_24h}%)")
    
    finally:
        await drift_client.disconnect()


async def example_binance_ohlc():
    """Example: Subscribe to Binance OHLC updates"""
    logger.info("\n=== Example 2: Binance OHLC Updates ===")
    
    binance_client = BinanceClient()
    handler = MarketDataHandler()
    
    try:
        # Connect
        await binance_client.connect()
        
        # Subscribe to OHLC
        symbols = ["SOLUSDT", "BTCUSDT", "ETHUSDT"]
        for symbol in symbols:
            await binance_client.subscribe_ohlc(symbol, handler.on_ohlc_update)
        
        # Wait for updates
        logger.info("Listening for OHLC updates (10 seconds)...")
        await asyncio.sleep(10)
        
        # Get latest OHLC
        logger.info("\nLatest OHLC (last 3 candles):")
        for symbol in symbols:
            ohlc_list = handler.get_ohlc(symbol, limit=3)
            if ohlc_list:
                logger.info(f"  {symbol}:")
                for ohlc in ohlc_list:
                    logger.info(f"    Close: {ohlc.close}, Volume: {ohlc.volume}")
    
    finally:
        await binance_client.disconnect()


async def example_historical_ohlc():
    """Example: Download historical OHLC data"""
    logger.info("\n=== Example 3: Historical OHLC Data ===")
    
    downloader = BinanceHistoryDownloader()
    
    # Download last 100 candles
    logger.info("Downloading last 100 candles for SOLUSDT...")
    ohlc_data = await downloader.download_ohlc("SOLUSDT")
    
    if ohlc_data:
        logger.info(f"Downloaded {len(ohlc_data)} candles")
        logger.info("First 3 candles:")
        for ohlc in ohlc_data[:3]:
            logger.info(f"  {ohlc.timestamp}: O={ohlc.open}, H={ohlc.high}, L={ohlc.low}, C={ohlc.close}")
        
        logger.info("Last 3 candles:")
        for ohlc in ohlc_data[-3:]:
            logger.info(f"  {ohlc.timestamp}: O={ohlc.open}, H={ohlc.high}, L={ohlc.low}, C={ohlc.close}")


async def example_multiple_symbols():
    """Example: Download OHLC for multiple symbols"""
    logger.info("\n=== Example 4: Multiple Symbols ===")
    
    downloader = BinanceHistoryDownloader()
    
    symbols = ["SOLUSDT", "BTCUSDT", "ETHUSDT"]
    logger.info(f"Downloading OHLC for {symbols}...")
    
    all_data = await downloader.download_multiple(symbols, limit=10)
    
    for symbol, ohlc_list in all_data.items():
        logger.info(f"{symbol}: {len(ohlc_list)} candles")
        if ohlc_list:
            latest = ohlc_list[-1]
            logger.info(f"  Latest: Close={latest.close}, Volume={latest.volume}")


async def main():
    """Run all examples"""
    logger.info("WebSocket Examples")
    logger.info("=" * 50)
    
    try:
        # Example 1: Drift prices
        # await example_drift_prices()
        
        # Example 2: Binance OHLC
        # await example_binance_ohlc()
        
        # Example 3: Historical OHLC
        await example_historical_ohlc()
        
        # Example 4: Multiple symbols
        await example_multiple_symbols()
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())
