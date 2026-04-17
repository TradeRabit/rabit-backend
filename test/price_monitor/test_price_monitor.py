"""Test price monitoring functionality"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agents.tools.market.price_monitor_tools import (
    add_price_alert,
    remove_price_alert,
    list_price_alerts,
    get_price_alert,
    get_price_monitor_stats,
    start_price_monitor,
    stop_price_monitor
)


async def test_price_monitor():
    """Test price monitoring functionality"""
    print("=" * 60)
    print("TESTING PRICE MONITOR")
    print("=" * 60)
    
    # Test 1: Start monitor
    print("\n1. Starting price monitor...")
    result = await start_price_monitor()
    print(f"   Success: {result.get('success')}")
    print(f"   Message: {result.get('message')}")
    assert result["success"], "Failed to start monitor"
    
    # Test 2: Add LONG alert
    print("\n2. Adding LONG alert for BTC...")
    result = await add_price_alert(
        symbol="BTC",
        validation_price=100000,  # Price goes UP to validate
        invalidation_price=90000,  # Price goes DOWN to invalidate
        direction="LONG"
    )
    print(f"   Success: {result.get('success')}")
    print(f"   Alert ID: {result.get('alert_id')}")
    print(f"   Current Price: ${result.get('current_price'):,.2f}" if result.get('current_price') else "   Current Price: Not available yet")
    print(f"   Monitoring: {result.get('monitoring')}")
    assert result["success"], "Failed to add LONG alert"
    btc_long_alert_id = result.get('alert_id')
    
    # Test 3: Add SHORT alert
    print("\n3. Adding SHORT alert for ETH...")
    result = await add_price_alert(
        symbol="ETH",
        validation_price=3000,  # Price goes DOWN to validate
        invalidation_price=3500,  # Price goes UP to invalidate
        direction="SHORT"
    )
    print(f"   Success: {result.get('success')}")
    print(f"   Alert ID: {result.get('alert_id')}")
    print(f"   Current Price: ${result.get('current_price'):,.2f}" if result.get('current_price') else "   Current Price: Not available yet")
    assert result["success"], "Failed to add SHORT alert"
    eth_short_alert_id = result.get('alert_id')
    
    # Test 4: List alerts
    print("\n4. Listing all alerts...")
    result = await list_price_alerts()
    print(f"   Success: {result.get('success')}")
    print(f"   Total Alerts: {result.get('total_alerts')}")
    print(f"   Active Alerts: {result.get('active_alerts')}")
    print(f"   Summary: {result.get('summary')}")
    assert result["success"], "Failed to list alerts"
    assert result["total_alerts"] >= 2, "Should have at least 2 alerts"
    
    # Test 5: Get specific alert
    print("\n5. Getting BTC LONG alert details...")
    result = await get_price_alert(btc_long_alert_id)
    print(f"   Success: {result.get('success')}")
    if result.get('alert'):
        alert = result['alert']
        print(f"   Symbol: {alert['symbol']}")
        print(f"   Direction: {alert['direction']}")
        print(f"   Validation: ${alert['validation_price']:,.2f}")
        print(f"   Invalidation: ${alert['invalidation_price']:,.2f}")
        print(f"   Triggered: {alert['triggered']}")
    assert result["success"], "Failed to get alert"
    
    # Test 6: Get monitor stats
    print("\n6. Getting monitor statistics...")
    result = await get_price_monitor_stats()
    print(f"   Success: {result.get('success')}")
    if result.get('stats'):
        stats = result['stats']
        print(f"   Running: {stats['running']}")
        print(f"   Active Alerts: {stats['active_alerts']}")
        print(f"   Total Alerts: {stats['total_alerts']}")
        print(f"   Validations: {stats['validations']}")
        print(f"   Invalidations: {stats['invalidations']}")
    assert result["success"], "Failed to get stats"
    
    # Test 7: Wait for price updates
    print("\n7. Waiting 15 seconds for price updates...")
    print("   (Monitor polls every 10 seconds)")
    await asyncio.sleep(15)
    
    # Test 8: Check stats again
    print("\n8. Checking stats after price updates...")
    result = await get_price_monitor_stats()
    if result.get('stats'):
        stats = result['stats']
        print(f"   Price Checks: {stats['price_checks']}")
        print(f"   Cached Prices: {stats['cached_prices']}")
    
    # Test 9: Remove one alert
    print("\n9. Removing ETH SHORT alert...")
    result = await remove_price_alert(eth_short_alert_id)
    print(f"   Success: {result.get('success')}")
    print(f"   Message: {result.get('message')}")
    assert result["success"], "Failed to remove alert"
    
    # Test 10: List active alerts only
    print("\n10. Listing active alerts only...")
    result = await list_price_alerts(active_only=True)
    print(f"   Success: {result.get('success')}")
    print(f"   Active Alerts: {result.get('active_alerts')}")
    assert result["success"], "Failed to list active alerts"
    
    # Test 11: Stop monitor
    print("\n11. Stopping price monitor...")
    result = await stop_price_monitor()
    print(f"   Success: {result.get('success')}")
    print(f"   Message: {result.get('message')}")
    assert result["success"], "Failed to stop monitor"
    
    print("\n" + "=" * 60)
    print("✅ ALL PRICE MONITOR TESTS PASSED!")
    print("=" * 60)


async def test_error_handling():
    """Test error handling"""
    print("\n" + "=" * 60)
    print("TESTING ERROR HANDLING")
    print("=" * 60)
    
    # Test 1: Invalid symbol
    print("\n1. Testing invalid symbol (empty)...")
    result = await add_price_alert("", 100000, 90000, "LONG")
    print(f"   Success: {result.get('success')}")
    print(f"   Error: {result.get('error')}")
    print(f"   Suggestion: {result.get('suggestion')}")
    assert not result["success"], "Should fail with empty symbol"
    
    # Test 2: Invalid direction
    print("\n2. Testing invalid direction...")
    result = await add_price_alert("BTC", 100000, 90000, "INVALID")
    print(f"   Success: {result.get('success')}")
    print(f"   Error: {result.get('error')}")
    print(f"   Valid options: {result.get('valid_options')}")
    assert not result["success"], "Should fail with invalid direction"
    
    # Test 3: Invalid prices for LONG
    print("\n3. Testing invalid prices for LONG (validation < invalidation)...")
    result = await add_price_alert("BTC", 90000, 100000, "LONG")
    print(f"   Success: {result.get('success')}")
    print(f"   Error: {result.get('error')}")
    assert not result["success"], "Should fail with invalid LONG prices"
    
    # Test 4: Invalid prices for SHORT
    print("\n4. Testing invalid prices for SHORT (validation > invalidation)...")
    result = await add_price_alert("ETH", 3500, 3000, "SHORT")
    print(f"   Success: {result.get('success')}")
    print(f"   Error: {result.get('error')}")
    assert not result["success"], "Should fail with invalid SHORT prices"
    
    # Test 5: Remove non-existent alert
    print("\n5. Testing remove non-existent alert...")
    result = await remove_price_alert("non-existent-id")
    print(f"   Success: {result.get('success')}")
    print(f"   Error: {result.get('error')}")
    print(f"   Suggestion: {result.get('suggestion')}")
    assert not result["success"], "Should fail with non-existent alert"
    
    print("\n" + "=" * 60)
    print("✅ ALL ERROR HANDLING TESTS PASSED!")
    print("=" * 60)


async def main():
    """Run all tests"""
    try:
        await test_price_monitor()
        await test_error_handling()
        
        print("\n" + "=" * 60)
        print("🎉 ALL TESTS COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {str(e)}")
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
