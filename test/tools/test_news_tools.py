"""
Test News Tools - Polymorphic news search
"""

from agents.tools.market.news_tools import (
    get_latest_news,
    search_news_by_keywords,
    get_trending_news,
    search_news_by_symbols
)
import json


def test_latest_news():
    """Test get latest news"""
    print("\n" + "="*60)
    print("Test 1: Get Latest News (Crypto)")
    print("="*60)
    
    result = get_latest_news(category="crypto", max_results=3)
    
    print(f"\nSuccess: {result['success']}")
    print(f"Category: {result.get('category')}")
    print(f"Count: {result.get('count', 0)}")
    
    if result['success']:
        for i, news in enumerate(result['results'], 1):
            print(f"\n{i}. {news['title']}")
            print(f"   Source: {news['source']}")
            print(f"   Date: {news['date']}")
            print(f"   URL: {news['url']}")
            print(f"   Snippet: {news['snippet'][:100]}...")


def test_search_by_keywords_regex():
    """Test search news by keywords with regex"""
    print("\n" + "="*60)
    print("Test 2: Search News by Keywords (Regex: BTC|ETH|TRUMP)")
    print("="*60)
    
    result = search_news_by_keywords(keywords="BTC|ETH|TRUMP", max_results=5)
    
    print(f"\nSuccess: {result['success']}")
    print(f"Keywords: {result.get('keywords')}")
    print(f"Regex Enabled: {result.get('regex_enabled')}")
    print(f"Count: {result.get('count', 0)}")
    
    if result['success']:
        for i, news in enumerate(result['results'], 1):
            print(f"\n{i}. {news['title']}")
            print(f"   Matched: {news.get('matched_keywords', [])}")
            print(f"   Date: {news['date']}")
            print(f"   URL: {news['url']}")


def test_trending_news():
    """Test get trending news"""
    print("\n" + "="*60)
    print("Test 3: Get Trending News (24h)")
    print("="*60)
    
    result = get_trending_news(timeframe="24h", max_results=5)
    
    print(f"\nSuccess: {result['success']}")
    print(f"Timeframe: {result.get('timeframe')}")
    print(f"Count: {result.get('count', 0)}")
    
    if result['success']:
        for i, news in enumerate(result['results'], 1):
            print(f"\n{i}. {news['title']}")
            print(f"   Category: {news.get('category', 'N/A')}")
            print(f"   Source: {news['source']}")
            print(f"   Date: {news['date']}")


def test_search_by_symbols():
    """Test search news by multiple symbols"""
    print("\n" + "="*60)
    print("Test 4: Search News by Symbols (BTC,ETH,SOL)")
    print("="*60)
    
    result = search_news_by_symbols(symbols="BTC,ETH,SOL", max_results=2)
    
    print(f"\nSuccess: {result['success']}")
    print(f"Symbols: {result.get('symbols')}")
    print(f"Total Count: {result.get('count', 0)}")
    
    if result['success']:
        for symbol, news_list in result['results'].items():
            print(f"\n--- {symbol} ({len(news_list)} news) ---")
            for news in news_list[:2]:  # Show first 2
                print(f"  • {news['title']}")
                print(f"    Date: {news['date']}")


def test_json_response():
    """Test JSON response format"""
    print("\n" + "="*60)
    print("Test 5: JSON Response Format")
    print("="*60)
    
    result = get_latest_news(category="defi", max_results=2)
    
    json_str = json.dumps(result, indent=2)
    print(f"\nJSON Response ({len(json_str)} chars):")
    print(json_str)


def test_regex_patterns():
    """Test various regex patterns"""
    print("\n" + "="*60)
    print("Test 6: Advanced Regex Patterns")
    print("="*60)
    
    patterns = [
        "bitcoin.*(price|surge|rally)",
        "(pump|dump|moon)",
        "SOL|SOLANA"
    ]
    
    for pattern in patterns:
        print(f"\nPattern: {pattern}")
        result = search_news_by_keywords(keywords=pattern, max_results=2)
        
        if result['success']:
            print(f"  Found: {result['count']} results")
            for news in result['results'][:1]:
                print(f"  • {news['title']}")
                print(f"    Matched: {news.get('matched_keywords', [])}")
        else:
            print(f"  No results")


if __name__ == "__main__":
    print("="*60)
    print("News Tools Test Suite")
    print("="*60)
    
    try:
        test_latest_news()
        test_search_by_keywords_regex()
        test_trending_news()
        test_search_by_symbols()
        test_json_response()
        test_regex_patterns()
        
        print("\n" + "="*60)
        print("✅ All tests completed!")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
