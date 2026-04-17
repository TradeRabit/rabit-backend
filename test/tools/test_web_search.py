"""
Test Web Search Tool (DuckDuckGo)
"""

from agents.tools.market.web_search import web_search, get_web_search_client


def test_basic_search():
    """Test basic web search"""
    print("\n=== Test 1: Basic Web Search ===")
    print("Query: Bitcoin price prediction 2024")
    
    result = web_search("Bitcoin price prediction 2024", max_results=3)
    
    print(f"\nSuccess: {result['success']}")
    print(f"Count: {result.get('count', 0)}")
    
    if result['success']:
        for i, item in enumerate(result['results'], 1):
            print(f"\n{i}. {item['title']}")
            print(f"   URL: {item['url']}")
            print(f"   Snippet: {item['snippet']}")
    else:
        print(f"Error: {result.get('error')}")


def test_crypto_search():
    """Test crypto-specific search"""
    print("\n\n=== Test 2: Crypto Search ===")
    print("Query: Solana DeFi")
    
    client = get_web_search_client()
    results = client.search_crypto("Solana DeFi", max_results=3)
    
    print(f"\nFound {len(results)} results")
    
    for i, item in enumerate(results, 1):
        print(f"\n{i}. {item['title']}")
        print(f"   URL: {item['url']}")
        print(f"   Snippet: {item['snippet']}")


def test_news_search():
    """Test news search"""
    print("\n\n=== Test 3: News Search ===")
    print("Query: Ethereum ETF")
    
    client = get_web_search_client()
    results = client.search_news("Ethereum ETF", max_results=3)
    
    print(f"\nFound {len(results)} news results")
    
    for i, item in enumerate(results, 1):
        print(f"\n{i}. {item['title']}")
        print(f"   URL: {item['url']}")
        print(f"   Date: {item.get('date', 'N/A')}")
        print(f"   Snippet: {item['snippet']}")


def test_minimal_json():
    """Test minimal JSON response"""
    print("\n\n=== Test 4: Minimal JSON Response ===")
    print("Query: Drift Protocol")
    
    result = web_search("Drift Protocol", max_results=2)
    
    import json
    json_str = json.dumps(result, indent=2)
    print(f"\nJSON Response ({len(json_str)} chars):")
    print(json_str)


if __name__ == "__main__":
    print("=" * 60)
    print("Web Search Tool Test (DuckDuckGo)")
    print("=" * 60)
    
    try:
        test_basic_search()
        test_crypto_search()
        test_news_search()
        test_minimal_json()
        
        print("\n" + "=" * 60)
        print("✅ All tests completed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
