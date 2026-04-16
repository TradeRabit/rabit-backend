"""Test crypto category utilities"""
from ws.utils.categories import (
    normalize_category,
    normalize_categories,
    get_primary_category,
    filter_by_category,
    get_category_stats,
    get_coins_by_category,
    get_all_categories,
    is_primary_category,
    PRIMARY_CATEGORIES
)


def test_normalize_category():
    """Test category normalization"""
    print("=" * 60)
    print("Testing Category Normalization")
    print("=" * 60)
    
    tests = [
        ("layer 1", "Layer 1"),
        ("Layer-1", "Layer 1"),
        ("L1", "Layer 1"),
        ("Smart Contract Platform", "Layer 1"),
        ("layer 2", "Layer 2"),
        ("L2", "Layer 2"),
        ("DeFi", "DeFi"),
        ("Decentralized Finance", "DeFi"),
        ("AI", "AI"),
        ("Artificial Intelligence", "AI"),
        ("AI Agent", "AI Agent"),
        ("ai agents", "AI Agent"),
        ("Infrastructure", "Infrastructure"),
        ("Oracle", "Infrastructure"),
        ("Gaming", "Gaming"),
        ("GameFi", "Gaming"),
        ("NFT", "NFT"),
        ("Meme", "Meme"),
        ("meme coin", "Meme"),
        ("Privacy", "Privacy"),
        ("Stablecoin", "Stablecoin"),
        ("RWA", "RWA"),
        ("Real World Assets", "RWA"),
    ]
    
    for raw, expected in tests:
        result = normalize_category(raw)
        status = "✓" if result == expected else "✗"
        print(f"{status} {raw:30s} -> {result:20s} (expected: {expected})")
        assert result == expected, f"Failed: {raw} -> {result} (expected {expected})"
    
    print("\n✓ All normalizations correct")


def test_normalize_categories_list():
    """Test normalizing a list of categories"""
    print("\n" + "=" * 60)
    print("Testing Category List Normalization")
    print("=" * 60)
    
    raw_categories = [
        "layer 1",
        "DeFi",
        "Smart Contract Platform",  # Should merge with Layer 1
        "ai agent",
        "Infrastructure"
    ]
    
    normalized = normalize_categories(raw_categories)
    print(f"\nRaw: {raw_categories}")
    print(f"Normalized: {normalized}")
    
    # Should deduplicate "layer 1" and "Smart Contract Platform" into "Layer 1"
    assert "Layer 1" in normalized
    assert "DeFi" in normalized
    assert "AI Agent" in normalized
    assert "Infrastructure" in normalized
    assert len(normalized) == 4  # Deduplicated
    
    print("✓ List normalization working correctly")


def test_primary_category():
    """Test getting primary category"""
    print("\n" + "=" * 60)
    print("Testing Primary Category Selection")
    print("=" * 60)
    
    tests = [
        (["Layer 1", "DeFi", "Infrastructure"], "Layer 1"),
        (["Gaming", "NFT"], "Gaming"),
        (["AI Agent", "Infrastructure"], "AI Agent"),  # AI Agent has higher priority
        (["Meme", "Social"], "Meme"),
        ([], "Other"),
        (["Unknown Category"], "Unknown Category"),
    ]
    
    for categories, expected in tests:
        result = get_primary_category(categories)
        print(f"{categories} -> {result}")
        assert result == expected, f"Expected {expected}, got {result}"
    
    print("\n✓ Primary category selection working")


def test_filter_by_category():
    """Test filtering by category"""
    print("\n" + "=" * 60)
    print("Testing Category Filtering")
    print("=" * 60)
    
    coin_categories = ["layer 1", "DeFi", "Infrastructure"]
    
    tests = [
        ("Layer 1", True),
        ("l1", True),
        ("DeFi", True),
        ("defi", True),
        ("Gaming", False),
        ("NFT", False),
    ]
    
    for category, expected in tests:
        result = filter_by_category(category, coin_categories)
        status = "✓" if result == expected else "✗"
        print(f"{status} Filter '{category}': {result} (expected: {expected})")
        assert result == expected
    
    print("\n✓ Filtering working correctly")


def test_category_stats():
    """Test category statistics"""
    print("\n" + "=" * 60)
    print("Testing Category Statistics")
    print("=" * 60)
    
    coins_data = [
        {"symbol": "BTC", "categories": ["layer 1", "Store of Value"]},
        {"symbol": "ETH", "categories": ["layer 1", "DeFi", "Smart Contract Platform"]},
        {"symbol": "SOL", "categories": ["layer 1", "DeFi"]},
        {"symbol": "UNI", "categories": ["DeFi", "DEX"]},
        {"symbol": "LINK", "categories": ["Infrastructure", "Oracle"]},
    ]
    
    stats = get_category_stats(coins_data)
    print("\nCategory distribution:")
    for cat, count in stats.items():
        print(f"  {cat:20s}: {count}")
    
    # Layer 1 should appear 3 times (BTC, ETH, SOL)
    assert stats.get("Layer 1", 0) == 3
    # DeFi should appear 3 times (ETH, SOL, UNI)
    assert stats.get("DeFi", 0) == 3
    # Infrastructure should appear 1 time (LINK)
    assert stats.get("Infrastructure", 0) == 1
    
    print("\n✓ Statistics calculation correct")


def test_get_coins_by_category():
    """Test getting coins by category"""
    print("\n" + "=" * 60)
    print("Testing Get Coins by Category")
    print("=" * 60)
    
    coins_data = [
        {"symbol": "BTC", "name": "Bitcoin", "categories": ["layer 1"]},
        {"symbol": "ETH", "name": "Ethereum", "categories": ["layer 1", "DeFi"]},
        {"symbol": "UNI", "name": "Uniswap", "categories": ["DeFi"]},
        {"symbol": "LINK", "name": "Chainlink", "categories": ["Infrastructure"]},
    ]
    
    # Get Layer 1 coins
    l1_coins = get_coins_by_category("Layer 1", coins_data)
    print(f"\nLayer 1 coins: {[c['symbol'] for c in l1_coins]}")
    assert len(l1_coins) == 2  # BTC, ETH
    
    # Get DeFi coins
    defi_coins = get_coins_by_category("DeFi", coins_data)
    print(f"DeFi coins: {[c['symbol'] for c in defi_coins]}")
    assert len(defi_coins) == 2  # ETH, UNI
    
    # Get Infrastructure coins
    infra_coins = get_coins_by_category("Infrastructure", coins_data)
    print(f"Infrastructure coins: {[c['symbol'] for c in infra_coins]}")
    assert len(infra_coins) == 1  # LINK
    
    print("\n✓ Coin filtering working correctly")


def test_all_categories():
    """Test getting all categories"""
    print("\n" + "=" * 60)
    print("Testing All Categories List")
    print("=" * 60)
    
    all_cats = get_all_categories()
    print(f"\nTotal primary categories: {len(all_cats)}")
    print(f"Categories: {', '.join(all_cats)}")
    
    # Check some expected categories
    expected = ["Layer 1", "Layer 2", "DeFi", "AI", "AI Agent", "Infrastructure", "Gaming", "NFT", "Meme"]
    for cat in expected:
        assert cat in all_cats, f"{cat} should be in primary categories"
    
    print("\n✓ All categories list correct")


def test_is_primary():
    """Test primary category check"""
    print("\n" + "=" * 60)
    print("Testing Primary Category Check")
    print("=" * 60)
    
    tests = [
        ("Layer 1", True),
        ("DeFi", True),
        ("AI Agent", True),
        ("Infrastructure", True),
        ("Unknown Category", False),
        ("Random", False),
    ]
    
    for category, expected in tests:
        result = is_primary_category(category)
        status = "✓" if result == expected else "✗"
        print(f"{status} {category:20s}: {result} (expected: {expected})")
        assert result == expected
    
    print("\n✓ Primary check working correctly")


if __name__ == "__main__":
    test_normalize_category()
    test_normalize_categories_list()
    test_primary_category()
    test_filter_by_category()
    test_category_stats()
    test_get_coins_by_category()
    test_all_categories()
    test_is_primary()
    
    print("\n" + "=" * 60)
    print("All category tests passed! ✓")
    print("=" * 60)
    print(f"\nTotal primary categories: {len(PRIMARY_CATEGORIES)}")
    print(f"Categories: {', '.join(sorted(PRIMARY_CATEGORIES))}")
