"""Test WebSocket functionality"""
import asyncio
from utils.logger import get_logger
from ws import (
    DriftWSClient,
    BinanceClient,
    BinanceHistoryDownloader,
    MarketDataHandler
)

logger = get_logger(__name__)


async def test_drift_connection():
    """Test Drift WebSocket connection and price retrieval"""
    logger.info("\n" + "="*60)
    logger.info("TEST 1: Drift WebSocket Connection")
    logger.info("="*60)
    
    drift_client = DriftWSClient()
    handler = MarketDataHandler()
    
    try:
        logger.info("Connecting to Drift WebSocket...")
        await drift_client.connect()
        logger.info("✅ Connected to Drift WebSocket")
        
        # Subscribe to a symbol
        symbol = "SOL"
        logger.info(f"Subscribing to {symbol}...")
        await drift_client.subscribe(symbol, handler.on_price_update)
        logger.info(f"✅ Subscribed to {symbol}")
        
        # Wait for price updates
        logger.info("Waiting for price updates (5 seconds)...")
        await asyncio.sleep(5)
        
        # Get price
        price = handler.get_price(symbol)
        if price:
            logger.info(f"✅ Got price for {symbol}:")
            logger.info(f"   Price: ${price.price}")
            logger.info(f"   24h Change: {price.change_24h}%")
            logger.info(f"   24h Volume: {price.volume_24h}")
            logger.info(f"   Open Interest: {price.open_interest}")
            logger.info(f"   Funding Rate: {price.funding_rate}%")
            return True
        else:
            logger.warning(f"❌ No price data received for {symbol}")
            return False
    
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
        return False
    
    finally:
        logger.info("Disconnecting from Drift...")
        await drift_client.disconnect()
        logger.info("✅ Disconnected")


async def test_binance_ohlc():
    """Test Binance OHLC WebSocket"""
    logger.info("\n" + "="*60)
    logger.info("TEST 2: Binance OHLC WebSocket")
    logger.info("="*60)
    
    binance_client = BinanceClient()
    handler = MarketDataHandler()
    
    try:
        logger.info("Connecting to Binance WebSocket...")
        await binance_client.connect()
        logger.info("✅ Connected to Binance WebSocket")
        
        # Subscribe to OHLC
        symbol = "SOLUSDT"
        logger.info(f"Subscribing to OHLC {symbol}...")
        await binance_client.subscribe_ohlc(symbol, handler.on_ohlc_update)
        logger.info(f"✅ Subscribed to OHLC {symbol}")
        
        # Wait for OHLC updates
        logger.info("Waiting for OHLC updates (5 seconds)...")
        await asyncio.sleep(5)
        
        # Get OHLC data
        ohlc_list = handler.get_ohlc(symbol)
        if ohlc_list:
            logger.info(f"✅ Got {len(ohlc_list)} OHLC candles for {symbol}:")
            latest = ohlc_list[-1]
            logger.info(f"   Latest Candle:")
            logger.info(f"   Open: {latest.open}")
            logger.info(f"   High: {latest.high}")
            logger.info(f"   Low: {latest.low}")
            logger.info(f"   Close: {latest.close}")
            logger.info(f"   Volume: {latest.volume}")
            logger.info(f"   Trades: {latest.number_of_trades}")
            return True
        else:
            logger.warning(f"❌ No OHLC data received for {symbol}")
            return False
    
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
        return False
    
    finally:
        logger.info("Disconnecting from Binance...")
        await binance_client.disconnect()
        logger.info("✅ Disconnected")


async def test_binance_history():
    """Test Binance historical OHLC download"""
    logger.info("\n" + "="*60)
    logger.info("TEST 3: Binance Historical OHLC Download")
    logger.info("="*60)
    
    downloader = BinanceHistoryDownloader()
    
    try:
        symbol = "SOLUSDT"
        logger.info(f"Downloading historical OHLC for {symbol}...")
        
        ohlc_data = await downloader.download_ohlc(symbol, limit=10)
        
        if ohlc_data:
            logger.info(f"✅ Downloaded {len(ohlc_data)} candles for {symbol}:")
            logger.info("First 3 candles:")
            for i, ohlc in enumerate(ohlc_data[:3]):
                logger.info(f"  Candle {i+1}:")
                logger.info(f"    Open: {ohlc.open}, Close: {ohlc.close}")
                logger.info(f"    High: {ohlc.high}, Low: {ohlc.low}")
                logger.info(f"    Volume: {ohlc.volume}")
            
            logger.info("Last 3 candles:")
            for i, ohlc in enumerate(ohlc_data[-3:]):
                logger.info(f"  Candle {len(ohlc_data)-2+i}:")
                logger.info(f"    Open: {ohlc.open}, Close: {ohlc.close}")
                logger.info(f"    High: {ohlc.high}, Low: {ohlc.low}")
                logger.info(f"    Volume: {ohlc.volume}")
            
            return True
        else:
            logger.warning(f"❌ No historical data received for {symbol}")
            return False
    
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
        return False


async def test_multiple_symbols():
    """Test downloading OHLC for multiple symbols"""
    logger.info("\n" + "="*60)
    logger.info("TEST 4: Multiple Symbols OHLC Download")
    logger.info("="*60)
    
    downloader = BinanceHistoryDownloader()
    
    try:
        symbols = ["SOLUSDT", "BTCUSDT", "ETHUSDT"]
        logger.info(f"Downloading OHLC for {symbols}...")
        
        all_data = await downloader.download_multiple(symbols, limit=5)
        
        success = True
        for symbol, ohlc_list in all_data.items():
            if ohlc_list:
                logger.info(f"✅ {symbol}: {len(ohlc_list)} candles")
                latest = ohlc_list[-1]
                logger.info(f"   Latest Close: {latest.close}, Volume: {latest.volume}")
            else:
                logger.warning(f"❌ {symbol}: No data")
                success = False
        
        return success
    
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
        return False


async def main():
    """Run all tests"""
    logger.info("\n" + "="*60)
    logger.info("WebSocket Tests")
    logger.info("="*60)
    
    results = {}
    
    # Test 1: Drift connection (optional - requires real connection)
    # results["Drift Connection"] = await test_drift_connection()
    
    # Test 2: Binance OHLC (optional - requires real connection)
    # results["Binance OHLC"] = await test_binance_ohlc()
    
    # Test 3: Binance History (should work)
    results["Binance History"] = await test_binance_history()
    
    # Test 4: Multiple Symbols (should work)
    results["Multiple Symbols"] = await test_multiple_symbols()
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("Test Summary")
    logger.info("="*60)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{test_name}: {status}")
    
    total = len(results)
    passed = sum(1 for r in results.values() if r)
    logger.info(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("✅ All tests passed!")
    else:
        logger.warning(f"❌ {total - passed} test(s) failed")


if __name__ == "__main__":
    asyncio.run(main())
