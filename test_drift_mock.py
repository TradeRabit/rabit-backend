"""Mock test for Drift WebSocket (without network)"""
import asyncio
from datetime import datetime
from utils.logger import get_logger
from ws import MarketDataHandler, PriceUpdate

logger = get_logger(__name__)


async def test_drift_mock():
    """Test Drift price handling with mock data"""
    logger.info("\n" + "="*60)
    logger.info("TEST: Drift Mock Price Handling")
    logger.info("="*60)
    
    handler = MarketDataHandler()
    
    try:
        # Simulate Drift price updates
        logger.info("\nSimulating Drift price updates...")
        
        # Create mock price data (as if from Drift WebSocket)
        mock_prices = [
            PriceUpdate(
                symbol="SOL",
                price=150.50,
                change_24h=5.25,
                volume_24h=1000000.0,
                open_interest=500000.0,
                funding_rate=0.05
            ),
            PriceUpdate(
                symbol="BTC",
                price=65000.0,
                change_24h=3.50,
                volume_24h=5000000.0,
                open_interest=2000000.0,
                funding_rate=0.08
            ),
            PriceUpdate(
                symbol="ETH",
                price=3500.0,
                change_24h=2.75,
                volume_24h=2000000.0,
                open_interest=1000000.0,
                funding_rate=0.06
            )
        ]
        
        # Process mock prices
        for price in mock_prices:
            await handler.on_price_update(price)
            logger.info(f"  ✅ Processed {price.symbol}: ${price.price}")
        
        # Verify prices were stored
        logger.info("\n" + "="*60)
        logger.info("Verifying Stored Prices:")
        logger.info("="*60)
        
        all_prices = handler.get_all_prices()
        logger.info(f"\n✅ Total prices stored: {len(all_prices)}")
        
        for symbol, price in all_prices.items():
            logger.info(f"\n{symbol}:")
            logger.info(f"  Price: ${price.price}")
            logger.info(f"  24h Change: {price.change_24h}%")
            logger.info(f"  24h Volume: ${price.volume_24h:,.0f}")
            logger.info(f"  Open Interest: ${price.open_interest:,.0f}")
            logger.info(f"  Funding Rate: {price.funding_rate}%")
        
        # Test individual retrieval
        logger.info("\n" + "="*60)
        logger.info("Testing Individual Price Retrieval:")
        logger.info("="*60)
        
        sol_price = handler.get_price("SOL")
        if sol_price:
            logger.info(f"\n✅ Retrieved SOL price: ${sol_price.price}")
            logger.info(f"   24h Change: {sol_price.change_24h}%")
        else:
            logger.warning("❌ Failed to retrieve SOL price")
            return False
        
        btc_price = handler.get_price("BTC")
        if btc_price:
            logger.info(f"\n✅ Retrieved BTC price: ${btc_price.price}")
            logger.info(f"   24h Change: {btc_price.change_24h}%")
        else:
            logger.warning("❌ Failed to retrieve BTC price")
            return False
        
        # Test event listeners
        logger.info("\n" + "="*60)
        logger.info("Testing Event Listeners:")
        logger.info("="*60)
        
        listener_calls = []
        
        def price_listener(price):
            listener_calls.append(price)
            logger.info(f"  📢 Listener triggered: {price.symbol} = ${price.price}")
        
        handler.subscribe("price:SOL", price_listener)
        logger.info("✅ Subscribed to price:SOL event")
        
        # Trigger event
        new_price = PriceUpdate(
            symbol="SOL",
            price=155.00,
            change_24h=6.50,
            volume_24h=1100000.0,
            open_interest=550000.0,
            funding_rate=0.06
        )
        
        await handler.on_price_update(new_price)
        
        if listener_calls:
            logger.info(f"✅ Listener called {len(listener_calls)} time(s)")
            logger.info(f"   Latest price: ${listener_calls[-1].price}")
        else:
            logger.warning("❌ Listener was not called")
            return False
        
        logger.info("\n" + "="*60)
        logger.info("✅ All mock tests passed!")
        logger.info("="*60)
        
        return True
    
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run mock test"""
    logger.info("\n" + "="*60)
    logger.info("Drift Mock Tests (No Network Required)")
    logger.info("="*60)
    
    result = await test_drift_mock()
    
    logger.info("\n" + "="*60)
    logger.info("Test Result")
    logger.info("="*60)
    
    if result:
        logger.info("✅ Mock test PASSED")
        logger.info("\nThis confirms that:")
        logger.info("  ✓ PriceUpdate model works correctly")
        logger.info("  ✓ MarketDataHandler stores prices")
        logger.info("  ✓ Price retrieval works")
        logger.info("  ✓ Event listeners work")
        logger.info("\nWhen connected to real Drift WebSocket:")
        logger.info("  → Prices will be automatically collected")
        logger.info("  → Data will be stored and accessible")
        logger.info("  → Listeners will be notified of updates")
    else:
        logger.warning("❌ Mock test FAILED")


if __name__ == "__main__":
    asyncio.run(main())
