"""
Test Specific News Search
Testing if tools can find specific news about N Co Living
"""

from agents.tools.market.news_tools import (
    search_news_by_keywords,
    get_latest_news
)
import json


def test_search_n_co_living():
    """Test search for N Co Living news"""
    print("\n" + "="*60)
    print("Test 1: Search 'N Co Living' or 'Bareskrim narkoba'")
    print("="*60)
    
    # Try different keyword combinations
    keywords_list = [
        "N Co Living",
        "Bareskrim narkoba",
        "kelab malam Jakarta",
        "N Co Living|Bareskrim|narkoba"
    ]
    
    for keywords in keywords_list:
        print(f"\n--- Keywords: {keywords} ---")
        result = search_news_by_keywords(keywords=keywords, max_results=3)
        
        print(f"Success: {result['success']}")
        print(f"Count: {result.get('count', 0)}")
        
        if result['success']:
            for i, news in enumerate(result['results'], 1):
                print(f"\n{i}. {news['title']}")
                print(f"   Source: {news['source']}")
                print(f"   Date: {news['date']}")
                print(f"   URL: {news['url']}")
                print(f"   Matched: {news.get('matched_keywords', [])}")
        else:
            print(f"Error: {result.get('error')}")


def test_search_indonesia_news():
    """Test search for Indonesian news"""
    print("\n" + "="*60)
    print("Test 2: Search Indonesian News (Detik, Kompas)")
    print("="*60)
    
    keywords = "Indonesia berita terbaru"
    result = search_news_by_keywords(keywords=keywords, max_results=5)
    
    print(f"Success: {result['success']}")
    print(f"Count: {result.get('count', 0)}")
    
    if result['success']:
        for i, news in enumerate(result['results'], 1):
            print(f"\n{i}. {news['title']}")
            print(f"   Source: {news['source']}")
            print(f"   URL: {news['url']}")


def test_general_search():
    """Test general web search"""
    print("\n" + "="*60)
    print("Test 3: General Web Search")
    print("="*60)
    
    from agents.tools.market.web_search import web_search
    
    result = web_search("N Co Living Bareskrim narkoba", max_results=5)
    
    print(f"Success: {result['success']}")
    print(f"Count: {result.get('count', 0)}")
    
    if result['success']:
        for i, item in enumerate(result['results'], 1):
            print(f"\n{i}. {item['title']}")
            print(f"   URL: {item['url']}")
            print(f"   Snippet: {item['snippet'][:100]}...")


def test_latest_general_news():
    """Test latest general news"""
    print("\n" + "="*60)
    print("Test 4: Latest General News")
    print("="*60)
    
    result = get_latest_news(category="general", max_results=5)
    
    print(f"Success: {result['success']}")
    print(f"Count: {result.get('count', 0)}")
    
    if result['success']:
        for i, news in enumerate(result['results'], 1):
            print(f"\n{i}. {news['title']}")
            print(f"   Source: {news['source']}")
            print(f"   Date: {news['date']}")


if __name__ == "__main__":
    print("="*60)
    print("Specific News Search Test")
    print("Target: N Co Living / Bareskrim narkoba news")
    print("="*60)
    
    try:
        test_search_n_co_living()
        test_search_indonesia_news()
        test_general_search()
        test_latest_general_news()
        
        print("\n" + "="*60)
        print("✅ All tests completed!")
        print("="*60)
        
        print("\n📝 Note:")
        print("DuckDuckGo may not index all Indonesian news sites immediately.")
        print("For specific Indonesian news, consider adding direct RSS feeds.")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
