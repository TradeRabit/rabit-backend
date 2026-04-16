"""Test Backpack Exchange WebSocket client"""
import asyncio
from ws.backpack import BackpackWSClient
from ws.models import PriceUpdate


async def test_backpack_connection():
    """Test basic connection to Backpack WebSocket"""
    client = BackpackWSClient()
    
    try:
        # Connect
        print("Connecting to Backpack WebSocket...")
        await client.connect()
        print("✓ Connected successfully")
        
        # Wait a bit to ensure connection is stable
        await asyncio.sleep(2)
        
        # Disconnect
        print("Disconnecting...")
        await client.disconnect()
        print("✓ Disconnected successfully")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        raise


async def test_backpack_subscription():
    """Test subscribing to market data"""
    client = BackpackWSClient()
    received_updates = []
    
    async def on_price_update(price_update: PriceUpdate):
        """Callback for price updates"""
        print(f"📊 {price_update.symbol}: ${price_update.price:.2f}")
        if price_update.change_24h is not None:
            print(f"   24h Change: {price_update.change_24h:.2f}%")
        if price_update.volume_24h is not None:
            print(f"   24h Volume: ${price_update.volume_24h:,.2f}")
        if price_update.high_24h is not None:
            print(f"   24h High: ${price_update.high_24h:.2f}")
        if price_update.low_24h is not None:
            print(f"   24h Low: ${price_update.low_24h:.2f}")
        print()
        received_updates.append(price_update)
    
    try:
        # Connect
        print("Connecting to Backpack WebSocket...")
        await client.connect()
        print("✓ Connected\n")
        
        # Subscribe to SOL_USDC
        print("Subscribing to SOL_USDC...")
        await client.subscribe("SOL_USDC", on_price_update)
        print("✓ Subscribed\n")
        
        # Wait for some updates
        print("Waiting for price updates (30 seconds)...\n")
        await asyncio.sleep(30)
        
        # Check if we received updates
        if received_updates:
            print(f"\n✓ Received {len(received_updates)} price updates")
        else:
            print("\n⚠ No price updates received")
        
        # Unsubscribe
        print("\nUnsubscribing...")
        await client.unsubscribe("SOL_USDC")
        print("✓ Unsubscribed")
        
        # Disconnect
        print("\nDisconnecting...")
        await client.disconnect()
        print("✓ Disconnected")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        await client.disconnect()
        raise


async def test_backpack_multiple_symbols():
    """Test subscribing to multiple symbols"""
    client = BackpackWSClient()
    update_counts = {}
    
    async def on_price_update(price_update: PriceUpdate):
        """Callback for price updates"""
        symbol = price_update.symbol
        if symbol not in update_counts:
            update_counts[symbol] = 0
        update_counts[symbol] += 1
        
        print(f"📊 {symbol}: ${price_update.price:.2f} (update #{update_counts[symbol]})")
    
    try:
        # Connect
        print("Connecting to Backpack WebSocket...")
        await client.connect()
        print("✓ Connected\n")
        
        # Subscribe to multiple symbols
        symbols = ["SOL_USDC", "BTC_USDC", "ETH_USDC"]
        print(f"Subscribing to {len(symbols)} symbols: {', '.join(symbols)}...")
        
        for symbol in symbols:
            await client.subscribe(symbol, on_price_update)
            await asyncio.sleep(0.5)  # Small delay between subscriptions
        
        print("✓ All subscribed\n")
        
        # Wait for updates
        print("Waiting for price updates (30 seconds)...\n")
        await asyncio.sleep(30)
        
        # Print summary
        print("\n" + "="*50)
        print("SUMMARY")
        print("="*50)
        for symbol, count in update_counts.items():
            print(f"{symbol}: {count} updates")
        print("="*50)
        
        # Disconnect
        print("\nDisconnecting...")
        await client.disconnect()
        print("✓ Disconnected")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        await client.disconnect()
        raise


async def main():
    """Run all tests"""
    print("="*60)
    print("BACKPACK EXCHANGE WEBSOCKET CLIENT TESTS")
    print("="*60)
    print()
    
    # Test 1: Basic connection
    print("TEST 1: Basic Connection")
    print("-"*60)
    await test_backpack_connection()
    print()
    
    # Test 2: Single symbol subscription
    print("\nTEST 2: Single Symbol Subscription")
    print("-"*60)
    await test_backpack_subscription()
    print()
    
    # Test 3: Multiple symbols
    print("\nTEST 3: Multiple Symbols Subscription")
    print("-"*60)
    await test_backpack_multiple_symbols()
    print()
    
    print("="*60)
    print("ALL TESTS COMPLETED")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())



async def test_backpack_ohlc():
    """Test OHLC/Kline subscription"""
    client = BackpackWSClient()
    received_ohlc = []
    
    async def on_ohlc_update(ohlc):
        """Callback for OHLC updates"""
        print(f"📈 {ohlc.symbol} Candle:")
        print(f"   Time: {ohlc.timestamp}")
        print(f"   Open: ${ohlc.open:.2f}")
        print(f"   High: ${ohlc.high:.2f}")
        print(f"   Low: ${ohlc.low:.2f}")
        print(f"   Close: ${ohlc.close:.2f}")
        print(f"   Volume: {ohlc.volume:,.2f}")
        print()
        received_ohlc.append(ohlc)
    
    try:
        # Connect
        print("Connecting to Backpack WebSocket...")
        await client.connect()
        print("✓ Connected\n")
        
        # Subscribe to SOL with OHLC
        print("Subscribing to SOL with OHLC data...")
        await client.subscribe("SOL", lambda x: None, subscribe_ohlc=True)
        client.subscribe_ohlc("SOL", on_ohlc_update)
        print("✓ Subscribed\n")
        
        # Wait for OHLC updates (may take longer for candle close)
        print("Waiting for OHLC updates (60 seconds)...\n")
        await asyncio.sleep(60)
        
        # Check results
        if received_ohlc:
            print(f"\n✓ Received {len(received_ohlc)} OHLC updates")
        else:
            print("\n⚠ No OHLC updates received (may need to wait for candle close)")
        
        # Disconnect
        print("\nDisconnecting...")
        await client.disconnect()
        print("✓ Disconnected")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        await client.disconnect()
        raise


async def test_backpack_service():
    """Test Backpack service integration"""
    from ws.backpack import get_backpack_service
    from ws.handlers import MarketDataHandler
    
    print("Testing Backpack Service Integration...")
    print("-"*60)
    
    service = get_backpack_service()
    handler = MarketDataHandler()
    
    try:
        # Start service
        print("Starting Backpack service...")
        await service.start(handler)
        print(f"✓ Service started: {service.is_running()}\n")
        
        # Wait for data
        print("Waiting for market data (15 seconds)...\n")
        await asyncio.sleep(15)
        
        # Check subscriptions
        symbols = service.get_subscribed_symbols()
        print(f"📊 Subscribed to {len(symbols)} symbols")
        if symbols:
            print(f"   First 5: {symbols[:5]}")
        print()
        
        # Check handler data
        prices = handler.get_all_prices()
        print(f"💰 Handler has price data for {len(prices)} symbols")
        if prices:
            for symbol, price in list(prices.items())[:3]:
                print(f"   {symbol}: ${price.price:.2f}")
        print()
        
        # Check OHLC data
        ohlc_data = handler.get_all_ohlc()
        print(f"📈 Handler has OHLC data for {len(ohlc_data)} symbols")
        print()
        
        # Stop service
        print("Stopping service...")
        await service.stop()
        print(f"✓ Service stopped: {not service.is_running()}")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        await service.stop()
        raise


if __name__ == "__main__":
    # Run OHLC test
    print("="*60)
    print("BACKPACK OHLC TEST")
    print("="*60)
    print()
    asyncio.run(test_backpack_ohlc())
