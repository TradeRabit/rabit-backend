# Web Search Tool

## Overview

Rabit Agent includes a **100% FREE** web search tool powered by DuckDuckGo. No API keys, no Docker, no rate limits.

## Features

- ✅ **100% FREE** - No API keys required
- ✅ **No Docker** - Pure Python library
- ✅ **No Rate Limits** - Unlimited searches
- ✅ **Minimal JSON** - Token-efficient responses
- ✅ **Multiple Search Types**:
  - General web search
  - News search
  - Crypto-specific search

## Installation

```bash
pip install ddgs
```

Already included in `requirements.txt`.

## Usage

### 1. General Web Search

```python
from agents.tools.web_search import web_search

result = web_search("Bitcoin price prediction 2024", max_results=5)

if result['success']:
    for item in result['results']:
        print(f"Title: {item['title']}")
        print(f"URL: {item['url']}")
        print(f"Snippet: {item['snippet']}")
```

### 2. News Search

```python
from agents.tools.web_search import get_web_search_client

client = get_web_search_client()
results = client.search_news("Ethereum ETF", max_results=5)

for item in results:
    print(f"Title: {item['title']}")
    print(f"Date: {item['date']}")
    print(f"URL: {item['url']}")
```

### 3. Crypto Search

```python
client = get_web_search_client()
results = client.search_crypto("Solana DeFi", max_results=5)

for item in results:
    print(f"Title: {item['title']}")
    print(f"URL: {item['url']}")
```

## Response Format

### Success Response

```json
{
  "success": true,
  "query": "Bitcoin price",
  "count": 3,
  "results": [
    {
      "title": "Bitcoin Price Today...",
      "url": "https://example.com",
      "snippet": "Bitcoin is trading at..."
    }
  ]
}
```

### Error Response

```json
{
  "success": false,
  "error": "No results found for: invalid query",
  "results": []
}
```

## Token Efficiency

To minimize token usage:
- **Title**: Max 100 characters
- **Snippet**: Max 200 characters
- **Minimal fields**: Only essential data

Example: A 5-result response is ~700 chars (~175 tokens).

## Agent Integration

The `web_search` tool is automatically registered with TradingAgent:

```python
# Agent can use it directly
agent = TradingAgent(user_id="user123")
response = await agent.chat("Search for latest Bitcoin news")
```

The agent will automatically call `web_search` when needed.

## Testing

Run the test file:

```bash
python test_web_search.py
```

Tests include:
1. Basic web search
2. Crypto-specific search
3. News search
4. Minimal JSON response

## Advantages

| Feature | DuckDuckGo (ddgs) | SearXNG | Google API |
|---------|-------------------|---------|------------|
| **Cost** | FREE | FREE | $5/1000 queries |
| **Installation** | `pip install` | Docker required | API key required |
| **Rate Limits** | None | None | 100/day (free tier) |
| **Setup Time** | 1 minute | 10+ minutes | 5 minutes |
| **Maintenance** | None | Docker updates | API key management |

## Limitations

- No advanced filtering (date range, site-specific)
- Results may vary in quality
- No guaranteed uptime (depends on DuckDuckGo)

## Alternative: SearXNG (Optional)

If you need more control, you can use SearXNG with Docker:

```bash
docker-compose up -d searxng
```

Then update `.env`:

```env
SEARXNG_ENABLED=true
SEARXNG_URL=http://localhost:8888
```

See `searxng/settings.yml` for 40+ configured news sources.

## Troubleshooting

### Import Error

```bash
pip install ddgs
```

### No Results

- Check internet connection
- Try different query
- DuckDuckGo may be temporarily unavailable

### Slow Response

- Reduce `max_results`
- Use more specific queries
- Check network latency

## Related Files

- `agents/tools/web_search.py` - Main implementation
- `agents/examples/trading_tools.py` - Tool registration
- `test_web_search.py` - Test suite
- `docs/NEWS_SOURCES.md` - SearXNG news sources (optional)
