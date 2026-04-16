"""Test script for TradingView tools"""
import asyncio
import aiohttp
from agents.tools.tradingview import (
    tv_get_state,
    tv_set_symbol,
    tv_set_timeframe,
    tv_get_quote,
    tv_get_ohlcv,
    tv_add_indicator,
    tv_get_indicator_values,
    tv_draw_horizontal_line,
)
from agents.tools.tradingview.client import get_client


async def test_health_check():
    """Test connection to TradingView chart"""
    print("\n=== Testing Health Check ===")
    
    # Test API server instead
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:3001/health") as response:
                if response.status == 200:
                    print("✅ API Server is accessible at http://localhost:3001")
                    return True
                else:
                    print(f"❌ API Server returned status {response.status}")
                    return False
    except Exception as e:
        print(f"❌ Cannot connect to API Server: {str(e)}")
        print("   Make sure API server is running: npm run api")
        return False


async def test_chart_control():
    """Test chart control tools"""
    print("\n=== Testing Chart Control ===")
    
    # Get current state
    print("\n1. Getting chart state...")
    result = await tv_get_state()
    print(f"   Result: {result}")
    
    # Set symbol
    print("\n2. Setting symbol to BTC...")
    result = await tv_set_symbol("BTC")
    print(f"   Result: {result}")
    
    await asyncio.sleep(2)  # Wait for chart to update
    
    # Set timeframe
    print("\n3. Setting timeframe to 1 hour...")
    result = await tv_set_timeframe("60")
    print(f"   Result: {result}")
    
    await asyncio.sleep(2)


async def test_data_reading():
    """Test data reading tools"""
    print("\n=== Testing Data Reading ===")
    
    # Get quote
    print("\n1. Getting quote...")
    result = await tv_get_quote()
    print(f"   Result: {result}")
    
    # Get OHLCV summary
    print("\n2. Getting OHLCV summary...")
    result = await tv_get_ohlcv(count=100, summary=True)
    print(f"   Result: {result}")


async def test_indicators():
    """Test indicator tools"""
    print("\n=== Testing Indicators ===")
    
    # Add RSI
    print("\n1. Adding RSI indicator...")
    result = await tv_add_indicator("RSI", {"length": 14})
    print(f"   Result: {result}")
    
    await asyncio.sleep(3)  # Wait for indicator to load
    
    # Get indicator values
    print("\n2. Getting indicator values...")
    result = await tv_get_indicator_values()
    print(f"   Result: {result}")


async def test_drawing():
    """Test drawing tools"""
    print("\n=== Testing Drawing ===")
    
    # Draw horizontal line
    print("\n1. Drawing horizontal line at 95000...")
    result = await tv_draw_horizontal_line(
        price=95000,
        color="#FD4C01",
        text="Test Level"
    )
    print(f"   Result: {result}")


async def main():
    """Run all tests"""
    print("=" * 60)
    print("TradingView Tools Test Suite")
    print("=" * 60)
    
    # Health check first
    if not await test_health_check():
        return
    
    try:
        # Run tests
        await test_chart_control()
        await test_data_reading()
        await test_indicators()
        await test_drawing()
        
        print("\n" + "=" * 60)
        print("✅ All tests completed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
