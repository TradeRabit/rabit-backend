"""Test interval utilities"""
from ws.utils import (
    SUPPORTED_INTERVALS,
    get_interval_ms,
    get_interval_seconds,
    is_valid_interval,
    get_interval_category,
    get_intervals_by_category,
    format_interval_human
)


def test_supported_intervals():
    """Test all supported intervals are defined"""
    print("=" * 60)
    print("Testing Supported Intervals")
    print("=" * 60)
    
    print(f"\nTotal intervals: {len(SUPPORTED_INTERVALS)}")
    print(f"Intervals: {SUPPORTED_INTERVALS}")
    
    # Check expected intervals
    expected = [
        "1m", "3m", "5m", "15m", "30m",
        "1h", "2h", "4h", "6h", "8h", "12h",
        "1d", "3d",
        "1w",
        "1M"
    ]
    
    assert len(SUPPORTED_INTERVALS) == len(expected), "Interval count mismatch"
    assert set(SUPPORTED_INTERVALS) == set(expected), "Interval set mismatch"
    
    print("✓ All expected intervals present")


def test_interval_ms():
    """Test interval millisecond conversion"""
    print("\n" + "=" * 60)
    print("Testing Interval Milliseconds")
    print("=" * 60)
    
    tests = [
        ("1m", 60 * 1000),
        ("5m", 5 * 60 * 1000),
        ("1h", 60 * 60 * 1000),
        ("4h", 4 * 60 * 60 * 1000),
        ("1d", 24 * 60 * 60 * 1000),
        ("1w", 7 * 24 * 60 * 60 * 1000),
    ]
    
    for interval, expected_ms in tests:
        result = get_interval_ms(interval)
        print(f"{interval:4s} = {result:12,} ms (expected: {expected_ms:12,})")
        assert result == expected_ms, f"Mismatch for {interval}"
    
    print("✓ All conversions correct")


def test_interval_seconds():
    """Test interval seconds conversion"""
    print("\n" + "=" * 60)
    print("Testing Interval Seconds")
    print("=" * 60)
    
    tests = [
        ("1m", 60),
        ("1h", 3600),
        ("1d", 86400),
    ]
    
    for interval, expected_sec in tests:
        result = get_interval_seconds(interval)
        print(f"{interval:4s} = {result:8,} seconds")
        assert result == expected_sec, f"Mismatch for {interval}"
    
    print("✓ All conversions correct")


def test_is_valid():
    """Test interval validation"""
    print("\n" + "=" * 60)
    print("Testing Interval Validation")
    print("=" * 60)
    
    valid = ["1m", "5m", "1h", "4h", "1d", "1w", "1M"]
    invalid = ["10m", "7h", "2d", "2w", "3M", "invalid"]
    
    print("\nValid intervals:")
    for interval in valid:
        result = is_valid_interval(interval)
        print(f"  {interval:6s} -> {result}")
        assert result is True, f"{interval} should be valid"
    
    print("\nInvalid intervals:")
    for interval in invalid:
        result = is_valid_interval(interval)
        print(f"  {interval:8s} -> {result}")
        assert result is False, f"{interval} should be invalid"
    
    print("✓ Validation working correctly")


def test_interval_category():
    """Test interval category detection"""
    print("\n" + "=" * 60)
    print("Testing Interval Categories")
    print("=" * 60)
    
    tests = [
        ("1m", "minute"),
        ("5m", "minute"),
        ("1h", "hour"),
        ("4h", "hour"),
        ("1d", "day"),
        ("3d", "day"),
        ("1w", "week"),
        ("1M", "month"),
    ]
    
    for interval, expected_cat in tests:
        result = get_interval_category(interval)
        print(f"{interval:4s} -> {result:8s}")
        assert result == expected_cat, f"Category mismatch for {interval}"
    
    print("✓ All categories correct")


def test_intervals_by_category():
    """Test grouping intervals by category"""
    print("\n" + "=" * 60)
    print("Testing Intervals by Category")
    print("=" * 60)
    
    by_category = get_intervals_by_category()
    
    for category, intervals in by_category.items():
        print(f"\n{category.capitalize()}:")
        print(f"  {', '.join(intervals)}")
    
    # Verify counts
    assert len(by_category["minute"]) == 5, "Should have 5 minute intervals"
    assert len(by_category["hour"]) == 6, "Should have 6 hour intervals"
    assert len(by_category["day"]) == 2, "Should have 2 day intervals"
    assert len(by_category["week"]) == 1, "Should have 1 week interval"
    assert len(by_category["month"]) == 1, "Should have 1 month interval"
    
    print("\n✓ All categories have correct counts")


def test_format_human():
    """Test human-readable formatting"""
    print("\n" + "=" * 60)
    print("Testing Human-Readable Format")
    print("=" * 60)
    
    tests = [
        ("1m", "1 minute"),
        ("5m", "5 minutes"),
        ("1h", "1 hour"),
        ("4h", "4 hours"),
        ("1d", "1 day"),
        ("3d", "3 days"),
        ("1w", "1 week"),
        ("1M", "1 month"),
    ]
    
    for interval, expected in tests:
        result = format_interval_human(interval)
        print(f"{interval:4s} -> {result}")
        assert result == expected, f"Format mismatch for {interval}"
    
    print("✓ All formats correct")


if __name__ == "__main__":
    test_supported_intervals()
    test_interval_ms()
    test_interval_seconds()
    test_is_valid()
    test_interval_category()
    test_intervals_by_category()
    test_format_human()
    
    print("\n" + "=" * 60)
    print("All interval tests passed! ✓")
    print("=" * 60)
