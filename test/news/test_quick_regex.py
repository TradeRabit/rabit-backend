from agents.tools.news_tools import search_news_by_keywords

# Test 1: BTC|ETH|SOL
print("Test 1: BTC|ETH|SOL")
r = search_news_by_keywords('BTC|ETH|SOL', 3)
print(f"Success: {r['success']}, Count: {r.get('count', 0)}")
for i, n in enumerate(r.get('results', []), 1):
    print(f"{i}. {n['title']}")
    print(f"   Matched: {n.get('matched_keywords', [])}")

print("\n" + "="*60 + "\n")

# Test 2: Bareskrim|narkoba
print("Test 2: Bareskrim|narkoba")
r = search_news_by_keywords('Bareskrim|narkoba', 3)
print(f"Success: {r['success']}, Count: {r.get('count', 0)}")
for i, n in enumerate(r.get('results', []), 1):
    print(f"{i}. {n['title']}")
    print(f"   Matched: {n.get('matched_keywords', [])}")

print("\n" + "="*60 + "\n")

# Test 3: pump|dump|moon
print("Test 3: pump|dump|moon")
r = search_news_by_keywords('pump|dump|moon', 3)
print(f"Success: {r['success']}, Count: {r.get('count', 0)}")
for i, n in enumerate(r.get('results', []), 1):
    print(f"{i}. {n['title']}")
    print(f"   Matched: {n.get('matched_keywords', [])}")

print("\nAll tests completed!")
