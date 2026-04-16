"""Test OHLC Database functionality"""
import asyncio
from datetime import datetime
from ws.database import get_ohlc_database
from ws.models import OHLCData
from ws.binance.history import BinanceHistoryDownloader


async def test_database():
    """Test OHLC database operations"""
    
    print("=" * 60)
    print("Testing OHLC Database")
    print("=" * 60)
    
    # Get database instance
    db = get_ohlc_database()
    
    # Clear database for clean test
    print("\n1. Clearing database...")
    db.clear_all()
    
    # Create sample OHLC data
    print("\n2. Creating sample OHLC data...")
    sample_candles = [
        OHLCData(
            symbol="BTC",
            timestamp=int(datetime.now().timestamp() * 1000) - (i * 3600000),  # 1 hour intervals
            open=50000.0 + i * 100,
            high=51000.0 + i * 100,
            low=49000.0 + i * 100,
            close=50500.0 + i * 100,
            volume=1000.0 + i * 10
        )
        for i in range(10)
    ]
    
    # Save to database
    print("\n3. Saving candles to database...")
    db.save_candles(
        symbol="BTC",
        exchange="binance",
        interval="1h",
        candles=sample_candles,
        merge=False
    )
    
    # Retrieve candles
    print("\n4. Retrieving candles from database...")
    retrieved = db.get_candles("BTC", "binance", "1h")
    print(f"   Retrieved {len(retrieved)} candles")
    
    # Get latest candle
    print("\n5. Getting latest candle...")
    latest = db.get_latest_candle("BTC", "binance", "1h")
    if latest:
        print(f"   Latest: {latest.symbol} @ {latest.close}")
    
    # Test merge functionality
    print("\n6. Testing merge (adding duplicate + new candles)...")
    new_candles = [
        sample_candles[0],  # Duplicate
        OHLCData(
            symbol="BTC",
            timestamp=int(datetime.now().timestamp() * 1000),
            open=51000.0,
            high=52000.0,
            low=50000.0,
            close=51500.0,
            volume=1500.0
        )
    ]
    
    db.save_candles(
        symbol="BTC",
        exchange="binance",
        interval="1h",
        candles=new_candles,
        merge=True
    )
    
    merged = db.get_candles("BTC", "binance", "1h")
    print(f"   After merge: {len(merged)} candles (should be 11, not 12)")
    
    # Test multiple exchanges
    print("\n7. Testing multiple exchanges...")
    db.save_candles("SOL", "backpack", "1h", sample_candles[:5], merge=False)
    db.save_candles("SOL", "drift", "1h", sample_candles[:3], merge=False)
    
    # Get available symbols
    print("\n8. Getting available symbols...")
    all_symbols = db.get_available_symbols()
    print(f"   All symbols: {all_symbols}")
    
    binance_symbols = db.get_available_symbols("binance")
    print(f"   Binance symbols: {binance_symbols}")
    
    # Get available intervals
    print("\n9. Getting available intervals...")
    intervals = db.get_available_intervals("BTC", "binance")
    print(f"   BTC intervals on Binance: {intervals}")
    
    # Get statistics
    print("\n10. Database statistics:")
    stats = db.get_stats()
    print(f"   Total symbols: {stats['total_symbols']}")
    print(f"   Total candles: {stats['total_candles']}")
    print(f"   Exchanges: {list(stats['exchanges'].keys())}")
    for exchange, exchange_stats in stats['exchanges'].items():
        print(f"     - {exchange}: {exchange_stats['symbols']} symbols, {exchange_stats['total_candles']} candles")
    
    print("\n" + "=" * 60)
    print("Database test completed!")
    print("=" * 60)


async def test_binance_download():
    """Test Binance history downloader with auto-save"""
    
    print("\n" + "=" * 60)
    print("Testing Binance History Download with Auto-Save")
    print("=" * 60)
    
    downloader = BinanceHistoryDownloader(auto_save=True)
    
    print("\n1. Downloading SOLUSDT history (last 10 candles)...")
    candles = await downloader.download_ohlc("SOLUSDT", limit=10)
    
    if candles:
        print(f"   Downloaded {len(candles)} candles")
        print(f"   First candle: {candles[0].timestamp} - Close: {candles[0].close}")
        print(f"   Last candle: {candles[-1].timestamp} - Close: {candles[-1].close}")
        
        # Check if saved to database
        db = get_ohlc_database()
        saved = db.get_candles("SOL", "binance", "1h")
        print(f"\n2. Checking database...")
        print(f"   Found {len(saved)} candles in database for SOL")
    else:
        print("   Failed to download candles")
    
    print("\n" + "=" * 60)
    print("Binance download test completed!")
    print("=" * 60)


if __name__ == "__main__":
    # Run database test
    asyncio.run(test_database())
    
    # Run Binance download test
    asyncio.run(test_binance_download())
