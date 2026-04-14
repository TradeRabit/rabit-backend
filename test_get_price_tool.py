"""Test get_price tool"""
import asyncio
from agents.examples import register_example_tools
from agents.tools import tool_registry
from ws.handlers import MarketDataHandler
from ws.models import PriceUpdate
from datetime import datetime


async def test_get_price_tool():
    """Test the get_price tool"""
    
    print("=" * 60)
    print("Testing get_price Tool")
    print("=" * 60)
    
    # Register tools
    register_example_tools()
    
    # Get the tool
    tool = tool_registry.get_tool("get_price")
    print(f"\n✅ Tool registered: {tool.name}")
    print(f"   Description: {tool.description}")
    print(f"   Parameters: {[p.name for p in tool.parameters]}")
    
    # Simulate WebSocket data (in real scenario, this comes from WebSocket)
    handler = MarketDataHandler()
    
    # Add mock price data
    mock_price = PriceUpdate(
        symbol="SOL",
        price=145.67,
        change_24h=5.23,
        volume_24h=1234567890.50,
        high_24h=148.90,
        low_24h=142.30,
        market_cap=65000000000.0,
        fdv=70000000000.0,
        open_interest=500000000.0,
        funding_rate=0.0001,
        timestamp=datetime.now()
    )
    
    await handler.on_price_update(mock_price)
    print(f"\n✅ Mock price data added for SOL")
    
    # Test 1: Get price for SOL (should succeed)
    print("\n" + "-" * 60)
    print("Test 1: Get price for SOL")
    print("-" * 60)
    
    result = await tool_registry.execute("get_price", {"symbol": "SOL"})
    
    if result.success:
        print("✅ SUCCESS")
        print(f"   Symbol: {result.data['symbol']}")
        print(f"   Price: ${result.data['price']:.2f}")
        print(f"   24h Change: {result.data['change_24h']:.2f}%")
        print(f"   24h Volume: ${result.data['volume_24h']:,.2f}")
        print(f"   24h High: ${result.data['high_24h']:.2f}")
        print(f"   24h Low: ${result.data['low_24h']:.2f}")
        print(f"   Market Cap: ${result.data['market_cap']:,.0f}")
        print(f"   FDV: ${result.data['fdv']:,.0f}")
        print(f"   Open Interest: ${result.data['open_interest']:,.0f}")
        print(f"   Funding Rate: {result.data['funding_rate']:.4f}%")
    else:
        print(f"❌ FAILED: {result.error}")
    
    # Test 2: Get price for BTC (should fail - no data)
    print("\n" + "-" * 60)
    print("Test 2: Get price for BTC (no data)")
    print("-" * 60)
    
    result = await tool_registry.execute("get_price", {"symbol": "BTC"})
    
    if result.success:
        if not result.data.get("success"):
            print("✅ Correctly returned error for missing data")
            print(f"   Error: {result.data['error']}")
            print(f"   Suggestion: {result.data['suggestion']}")
        else:
            print("❌ Should have failed but succeeded")
    else:
        print(f"❌ Tool execution failed: {result.error}")
    
    # Test 3: Missing required parameter
    print("\n" + "-" * 60)
    print("Test 3: Missing required parameter")
    print("-" * 60)
    
    result = await tool_registry.execute("get_price", {})
    
    if not result.success:
        print("✅ Correctly rejected missing parameter")
        print(f"   Error: {result.error}")
    else:
        print("❌ Should have failed but succeeded")
    
    # Test 4: Lowercase symbol (should auto-convert)
    print("\n" + "-" * 60)
    print("Test 4: Lowercase symbol (auto-convert)")
    print("-" * 60)
    
    result = await tool_registry.execute("get_price", {"symbol": "sol"})
    
    if result.success:
        print("✅ SUCCESS - Auto-converted to uppercase")
        print(f"   Symbol: {result.data['symbol']}")
        print(f"   Price: ${result.data['price']:.2f}")
    else:
        print(f"❌ FAILED: {result.error}")
    
    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_get_price_tool())
