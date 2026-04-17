"""
Test Regex News Search
Testing regex patterns separately
"""

from agents.tools.market.news_tools import search_news_by_keywords
import time


def test_single_keyword():
    """Test single keyword (no regex)"""
    print("\n" + "="*60)
    print("Test 1: Single Keyword (No Regex)")
    print("="*60)
    
    keywords = "Bitcoin"
    print(f"Keywords: {keywords}")
    
    result = search_news_by_keywords(keywords=keywords, max_results=3)
    
    print(f"\nSuccess: {result['success']}")
    print(f"Regex Enabled: {result.get('regex_enabled')}")
    print(f"Count: {result.get('count', 0)}")
    
    if result['success']:
        for i, news in enumerate(result['results'], 1):
            print(f"\n{i}. {news['title']}")
            print(f"   Matched: {news.get('matched_keywords', [])}")
    
    time.sleep(2)  # Rate limit


def test_simple_or_regex():
    """Test simple OR regex (BTC|ETH)"""
    print("\n" + "="*60)
    print("Test 2: Simple OR Regex (BTC|ETH)")
    print("="*60)
    
    keywords = "BTC|ETH"
    print(f"Keywords: {keywords}")
    
    result = search_news_by_keywords(keywords=keywords, max_results=3)
    
    print(f"\nSuccess: {result['success']}")
    print(f"Regex Enabled: {result.get('regex_enabled')}")
    print(f"Count: {result.get('count', 0)}")
    
    if result['success']:
        for i, news in enumerate(result['results'], 1):
            print(f"\n{i}. {news['title']}")
            print(f"   Matched: {news.get('matched_keywords', [])}")
    else:
        print(f"Error: {result.get('error')}")
    
    time.sleep(2)


def test_three_symbols_regex():
    """Test three symbols (BTC|ETH|SOL)"""
    print("\n" + "="*60)
    print("Test 3: Three Symbols (BTC|ETH|SOL)")
    print("="*60)
    
    keywords = "BTC|ETH|SOL"
    print(f"Keywords: {keywords}")
    
    result = search_news_by_keywords(keywords=keywords, max_results=3)
    
    print(f"\nSuccess: {result['success']}")
    print(f"Regex Enabled: {result.get('regex_enabled')}")
    print(f"Count: {result.get('count', 0)}")
    
    if result['success']:
        for i, news in enumerate(result['results'], 1):
            print(f"\n{i}. {news['title']}")
            print(f"   Matched: {news.get('matched_keywords', [])}")
    else:
        print(f"Error: {result.get('error')}")
    
    time.sleep(2)


def test_word_regex():
    """Test word-based regex (pump|dump)"""
    print("\n" + "="*60)
    print("Test 4: Word Regex (pump|dump)")
    print("="*60)
    
    keywords = "pump|dump"
    print(f"Keywords: {keywords}")
    
    result = search_news_by_keywords(keywords=keywords, max_results=3)
    
    print(f"\nSuccess: {result['success']}")
    print(f"Regex Enabled: {result.get('regex_enabled')}")
    print(f"Count: {result.get('count', 0)}")
    
    if result['success']:
        for i, news in enumerate(result['results'], 1):
            print(f"\n{i}. {news['title']}")
            print(f"   Matched: {news.get('matched_keywords', [])}")
    else:
        print(f"Error: {result.get('error')}")
    
    time.sleep(2)


def test_mixed_regex():
    """Test mixed symbols and words"""
    print("\n" + "="*60)
    print("Test 5: Mixed Regex (Bitcoin|Ethereum|surge)")
    print("="*60)
    
    keywords = "Bitcoin|Ethereum|surge"
    print(f"Keywords: {keywords}")
    
    result = search_news_by_keywords(keywords=keywords, max_results=3)
    
    print(f"\nSuccess: {result['success']}")
    print(f"Regex Enabled: {result.get('regex_enabled')}")
    print(f"Count: {result.get('count', 0)}")
    
    if result['success']:
        for i, news in enumerate(result['results'], 1):
            print(f"\n{i}. {news['title']}")
            print(f"   Matched: {news.get('matched_keywords', [])}")
    else:
        print(f"Error: {result.get('error')}")
    
    time.sleep(2)


def test_case_insensitive():
    """Test case insensitive matching"""
    print("\n" + "="*60)
    print("Test 6: Case Insensitive (btc|eth|sol)")
    print("="*60)
    
    keywords = "btc|eth|sol"
    print(f"Keywords: {keywords}")
    
    result = search_news_by_keywords(keywords=keywords, max_results=3)
    
    print(f"\nSuccess: {result['success']}")
    print(f"Regex Enabled: {result.get('regex_enabled')}")
    print(f"Count: {result.get('count', 0)}")
    
    if result['success']:
        for i, news in enumerate(result['results'], 1):
            print(f"\n{i}. {news['title']}")
            print(f"   Matched: {news.get('matched_keywords', [])}")
    else:
        print(f"Error: {result.get('error')}")


def test_indonesian_regex():
    """Test Indonesian keywords with regex"""
    print("\n" + "="*60)
    print("Test 7: Indonesian Regex (Bareskrim|narkoba|polisi)")
    print("="*60)
    
    keywords = "Bareskrim|narkoba|polisi"
    print(f"Keywords: {keywords}")
    
    result = search_news_by_keywords(keywords=keywords, max_results=3)
    
    print(f"\nSuccess: {result['success']}")
    print(f"Regex Enabled: {result.get('regex_enabled')}")
    print(f"Count: {result.get('count', 0)}")
    
    if result['success']:
        for i, news in enumerate(result['results'], 1):
            print(f"\n{i}. {news['title']}")
            print(f"   Source: {news['source']}")
            print(f"   Matched: {news.get('matched_keywords', [])}")
    else:
        print(f"Error: {result.get('error')}")


if __name__ == "__main__":
    print("="*60)
    print("Regex News Search Test Suite")
    print("Testing different regex patterns separately")
    print("="*60)
    
    try:
        test_single_keyword()
        test_simple_or_regex()
        test_three_symbols_regex()
        test_word_regex()
        test_mixed_regex()
        test_case_insensitive()
        test_indonesian_regex()
        
        print("\n" + "="*60)
        print("✅ All regex tests completed!")
        print("="*60)
        
        print("\n📊 Summary:")
        print("- Single keyword: Basic search")
        print("- BTC|ETH: OR logic for 2 symbols")
        print("- BTC|ETH|SOL: OR logic for 3+ symbols")
        print("- pump|dump: Word-based matching")
        print("- Mixed: Symbols + words")
        print("- Case insensitive: Lowercase works")
        print("- Indonesian: Local news support")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
