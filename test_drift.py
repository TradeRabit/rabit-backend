"""Test Drift WebSocket functionality"""
import asyncio
from utils.logger import get_logger
from ws import DriftWSClient, MarketDataHandler

logger = get_logger(__name__)


async def test_drift_price():
    """Test Drift WebSocket price retrieval"""
    logger.info("\n" + "="*60)
    logger.info("TEST: Drift WebSocket Price Retrieval")
    logger.info("="*60)
    
    drift_client = DriftWSClient()
    handler = MarketDataHandler()
    
    try:
        logger.info("Connecting to Drift WebSocket...")
        logger.info(f"URL: {drift_client.url}")
        
        await drift_client.connect()
        logger.info("✅ Connected to Drift WebSocket")
        
        # Subscribe to multiple symbols
        symbols = ["SOL", "BTC", "ETH"]
        logger.info(f"\nSubscribing to symbols: {symbols}")
        
        for symbol in symbols:
            await drift_client.subscribe(symbol, handler.on_price_update)
            logger.info(f"  ✅ Subscribed to {symbol}")
        
        # Wait for price updates
        logger.info("\nWaiting for price updates (15 seconds)...")
        logger.info("(This will collect real-time data from Drift)")
        
        for i in range(15):
            await asyncio.sleep(1)
            logger.info(f"  [{i+1}/15] Waiting...")
        
        # Get prices
        logger.info("\n" + "="*60)
        logger.info("Price Data Received:")
        logger.info("="*60)
        
        all_prices = handler.get_all_prices()
        
        if all_prices:
            logger.info(f"✅ Received {len(all_prices)} price updates\n")
            
            for symbol, price in all_prices.items():
                logger.info(f"Symbol: {symbol}")
                logger.info(f"  Price: ${price.price}")
                logger.info(f"  24h Change: {price.change_24h}%")
                logger.info(f"  24h Volume: {price.volume_24h}")
                logger.info(f"  Open Interest: {price.open_interest}")
                logger.info(f"  Funding Rate: {price.funding_rate}%")
                logger.info(f"  Timestamp: {price.timestamp}\n")
            
            return True
        else:
            logger.warning("❌ No price data received")
            logger.info("Possible reasons:")
            logger.info("  - WebSocket connection issue")
            logger.info("  - Drift server not responding")
            logger.info("  - Network connectivity issue")
            return False
    
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        logger.info("\nDisconnecting from Drift...")
        await drift_client.disconnect()
        logger.info("✅ Disconnected")


async def test_drift_subscription():
    """Test Drift subscription management"""
    logger.info("\n" + "="*60)
    logger.info("TEST: Drift Subscription Management")
    logger.info("="*60)
    
    drift_client = DriftWSClient()
    
    try:
        logger.info("Connecting to Drift WebSocket...")
        await drift_client.connect()
        logger.info("✅ Connected")
        
        # Test subscription
        logger.info("\nTesting subscription...")
        
        async def dummy_callback(price):
            pass
        
        await drift_client.subscribe("SOL", dummy_callback)
        logger.info("✅ Subscribed to SOL")
        
        subscribed = drift_client.get_subscribed_symbols()
        logger.info(f"✅ Subscribed symbols: {subscribed}")
        
        is_subscribed = drift_client.is_subscribed("SOL")
        logger.info(f"✅ Is SOL subscribed: {is_subscribed}")
        
        # Test unsubscription
        logger.info("\nTesting unsubscription...")
        await drift_client.unsubscribe("SOL")
        logger.info("✅ Unsubscribed from SOL")
        
        subscribed = drift_client.get_subscribed_symbols()
        logger.info(f"✅ Subscribed symbols: {subscribed}")
        
        return True
    
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
        return False
    
    finally:
        await drift_client.disconnect()


async def test_drift_connection_status():
    """Test Drift connection status"""
    logger.info("\n" + "="*60)
    logger.info("TEST: Drift Connection Status")
    logger.info("="*60)
    
    drift_client = DriftWSClient()
    
    try:
        logger.info(f"Initial status: connected={drift_client.connected}")
        
        logger.info("\nConnecting...")
        await drift_client.connect()
        logger.info(f"After connect: connected={drift_client.connected}")
        
        if drift_client.connected:
            logger.info("✅ Connection successful")
        else:
            logger.warning("❌ Connection failed")
        
        logger.info("\nDisconnecting...")
        await drift_client.disconnect()
        logger.info(f"After disconnect: connected={drift_client.connected}")
        
        return drift_client.connected == False
    
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
        return False


async def main():
    """Run all Drift tests"""
    logger.info("\n" + "="*60)
    logger.info("Drift WebSocket Tests")
    logger.info("="*60)
    
    results = {}
    
    # Test 1: Connection status
    logger.info("\n[1/3] Testing connection status...")
    results["Connection Status"] = await test_drift_connection_status()
    
    # Test 2: Subscription management
    logger.info("\n[2/3] Testing subscription management...")
    results["Subscription Management"] = await test_drift_subscription()
    
    # Test 3: Price retrieval (main test)
    logger.info("\n[3/3] Testing price retrieval...")
    results["Price Retrieval"] = await test_drift_price()
    
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
