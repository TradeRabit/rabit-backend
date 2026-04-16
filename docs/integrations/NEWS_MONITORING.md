# News Monitoring System

## Overview

Rabit Agent includes a **real-time news monitoring system** with automatic AI review and sentiment analysis. Perfect for **trading on news** - get instant alerts when breaking news appears with automatic analysis of impact and trading recommendations.

## Features

- ✅ **Real-time Monitoring** - Polls for new news every 5 minutes (configurable)
- ✅ **AI Review** - Automatic sentiment analysis and trading recommendations
- ✅ **Regex Keywords** - Monitor multiple symbols with `BTC|ETH|SOL`
- ✅ **WebSocket Broadcasting** - Real-time alerts to all subscribers
- ✅ **Sentiment Analysis** - POSITIVE/NEGATIVE/NEUTRAL classification
- ✅ **Impact Assessment** - HIGH/MEDIUM/LOW impact levels
- ✅ **Trading Signals** - BUY/SELL/HOLD/WAIT recommendations
- ✅ **Statistics Tracking** - Monitor performance and news counts

## Use Cases

### 1. Trading on News

Monitor breaking news and get instant trading signals:

```python
# User: "Start monitoring BTC and ETH news"
# Agent calls: start_news_monitoring(keywords="BTC|ETH", poll_interval=300)

# When bad news appears:
# - Sentiment: NEGATIVE
# - Impact: HIGH
# - Recommendation: SELL
# - Analysis: "Major exchange hack, sell immediately"

# When good news appears:
# - Sentiment: POSITIVE
# - Impact: HIGH
# - Recommendation: BUY
# - Analysis: "ETF approval, strong buy signal"
```

### 2. Portfolio Monitoring

Track news for your entire portfolio:

```python
# Monitor multiple assets
start_news_monitoring(
    keywords="BTC|ETH|SOL|DOGE|ARB",
    poll_interval=180  # 3 minutes
)
```

### 3. Risk Management

Get alerts for negative news (hacks, regulations, crashes):

```python
# Monitor risk keywords
start_news_monitoring(
    keywords="hack|exploit|scam|ban|regulation|crash",
    poll_interval=120  # 2 minutes
)
```

## Tools

### 1. start_news_monitoring

Start real-time monitoring with AI review.

**Parameters:**
- `keywords` (optional): Regex keywords (default: "BTC|ETH|SOL")
- `poll_interval` (optional): Seconds between polls (default: 300)

**Example:**

```python
from agents.tools.news_tools import start_news_monitoring

result = start_news_monitoring(
    keywords="BTC|ETH|TRUMP",
    poll_interval=300
)

# Response:
{
    "success": true,
    "message": "News monitoring started",
    "keywords": ["BTC|ETH|TRUMP"],
    "poll_interval": 300,
    "auto_review": true
}
```

### 2. stop_news_monitoring

Stop monitoring and get final statistics.

**Example:**

```python
from agents.tools.news_tools import stop_news_monitoring

result = stop_news_monitoring()

# Response:
{
    "success": true,
    "message": "News monitoring stopped",
    "stats": {
        "total_news": 45,
        "reviewed_news": 45,
        "positive_news": 12,
        "negative_news": 8,
        "neutral_news": 25
    }
}
```

### 3. get_monitoring_status

Get current status and statistics.

**Example:**

```python
from agents.tools.news_tools import get_monitoring_status

result = get_monitoring_status()

# Response:
{
    "success": true,
    "running": true,
    "poll_interval": 300,
    "keywords": ["BTC|ETH|SOL"],
    "subscribers": 2,
    "seen_urls": 127,
    "auto_review": true,
    "total_news": 45,
    "reviewed_news": 45,
    "positive_news": 12,
    "negative_news": 8,
    "neutral_news": 25
}
```

## AI Review System

### Sentiment Analysis

Each news article is automatically reviewed:

```json
{
    "title": "Bitcoin Surges to New All-Time High",
    "snippet": "Bitcoin breaks $100k barrier...",
    "review": {
        "sentiment": "POSITIVE",
        "impact": "HIGH",
        "symbols": ["BTC"],
        "recommendation": "BUY",
        "analysis": "Strong bullish signal, consider buying"
    }
}
```

### Review Process

1. **News Detection** - New article found
2. **AI Analysis** - Agent reviews title + snippet
3. **Sentiment Classification** - POSITIVE/NEGATIVE/NEUTRAL
4. **Impact Assessment** - HIGH/MEDIUM/LOW
5. **Symbol Extraction** - Affected cryptocurrencies
6. **Trading Recommendation** - BUY/SELL/HOLD/WAIT
7. **Brief Analysis** - 100-char summary

### Fallback: Simple Sentiment

If AI review fails, uses rule-based analysis:

**Positive Keywords:**
- surge, rally, pump, bullish, gain, rise, up, moon, breakthrough, adoption

**Negative Keywords:**
- crash, dump, bearish, loss, fall, down, hack, scam, ban, regulation

## WebSocket Broadcasting

### Message Format

```json
{
    "type": "news_update",
    "timestamp": "2024-01-15T10:30:00Z",
    "count": 3,
    "high_impact_count": 1,
    "negative_count": 1,
    "positive_count": 2,
    "news": [
        {
            "title": "Bitcoin Surges...",
            "url": "https://...",
            "snippet": "...",
            "date": "2024-01-15T10:00:00Z",
            "source": "CoinDesk",
            "detected_at": "2024-01-15T10:30:00Z",
            "keyword": "BTC|ETH|SOL",
            "review": {
                "sentiment": "POSITIVE",
                "impact": "HIGH",
                "symbols": ["BTC"],
                "recommendation": "BUY",
                "analysis": "Strong bullish signal"
            }
        }
    ],
    "stats": {
        "total_news": 45,
        "reviewed_news": 45,
        "positive_news": 12,
        "negative_news": 8,
        "neutral_news": 25
    }
}
```

### Subscribe to Updates

```python
from ws.news import get_news_monitor

monitor = get_news_monitor()

# Subscribe
queue = monitor.subscribe()

# Receive updates
while True:
    message = await queue.get()
    print(f"New news: {message['count']}")
    
    # Check for high-impact negative news
    for news in message['news']:
        if news['review']['impact'] == 'HIGH' and news['review']['sentiment'] == 'NEGATIVE':
            print(f"⚠️ ALERT: {news['title']}")
            print(f"   Recommendation: {news['review']['recommendation']}")
```

## Configuration

### Environment Variables

```env
# News monitoring (optional)
NEWS_MONITOR_ENABLED=true
NEWS_MONITOR_INTERVAL=300  # 5 minutes
NEWS_MONITOR_AUTO_REVIEW=true
```

### Programmatic Configuration

```python
from ws.news import get_news_monitor

monitor = get_news_monitor()

# Change poll interval
monitor.poll_interval = 180  # 3 minutes

# Add keywords
monitor.add_keyword("TRUMP|BIDEN")

# Remove keywords
monitor.remove_keyword("NFT")

# Enable/disable auto-review
monitor.enable_auto_review()
monitor.disable_auto_review()

# Set custom review callback
async def custom_review(prompt):
    # Your custom AI review logic
    return {"sentiment": "POSITIVE", ...}

monitor.set_review_callback(custom_review)
```

## Performance

### Polling Strategy

- **Default**: 5 minutes (300 seconds)
- **Aggressive**: 2-3 minutes (120-180 seconds)
- **Conservative**: 10-15 minutes (600-900 seconds)

### Resource Usage

- **Memory**: ~10MB for 1000 cached URLs
- **Network**: ~1-2 KB per news article
- **CPU**: Minimal (async polling)

### Caching

- Seen URLs cached to prevent duplicates
- Auto-cleanup when cache exceeds 1000 URLs
- Keeps most recent 500 URLs

## Best Practices

### 1. Keyword Selection

```python
# Good: Specific symbols
"BTC|ETH|SOL"

# Good: Risk monitoring
"hack|exploit|scam|ban"

# Good: Event monitoring
"ETF|approval|regulation"

# Bad: Too broad
"crypto|bitcoin|news"  # Too many results
```

### 2. Poll Interval

```python
# High-frequency trading
poll_interval=120  # 2 minutes

# Normal trading
poll_interval=300  # 5 minutes (default)

# Long-term investing
poll_interval=900  # 15 minutes
```

### 3. Review Callback

```python
# Use agent for AI review
from agents.core import TradingAgent

agent = TradingAgent(user_id="monitor")
monitor.set_review_callback(agent.chat)
```

## Example: Complete Workflow

```python
import asyncio
from agents.tools.news_tools import start_news_monitoring, get_monitoring_status
from ws.news import get_news_monitor

async def main():
    # 1. Start monitoring
    result = start_news_monitoring(
        keywords="BTC|ETH|SOL",
        poll_interval=300
    )
    print(f"Monitoring started: {result}")
    
    # 2. Subscribe to updates
    monitor = get_news_monitor()
    queue = monitor.subscribe()
    
    # 3. Process news updates
    while True:
        message = await queue.get()
        
        print(f"\n📰 {message['count']} new articles")
        print(f"   High Impact: {message['high_impact_count']}")
        print(f"   Negative: {message['negative_count']}")
        print(f"   Positive: {message['positive_count']}")
        
        # Check for trading signals
        for news in message['news']:
            review = news.get('review', {})
            
            if review.get('impact') == 'HIGH':
                print(f"\n⚠️ HIGH IMPACT NEWS:")
                print(f"   {news['title']}")
                print(f"   Sentiment: {review.get('sentiment')}")
                print(f"   Recommendation: {review.get('recommendation')}")
                print(f"   Analysis: {review.get('analysis')}")
                
                # Execute trading logic here
                if review.get('recommendation') == 'SELL':
                    print("   🔴 SELL SIGNAL - Consider closing positions")
                elif review.get('recommendation') == 'BUY':
                    print("   🟢 BUY SIGNAL - Consider opening positions")

if __name__ == "__main__":
    asyncio.run(main())
```

## Troubleshooting

### Monitor Not Starting

```python
# Check if already running
status = get_monitoring_status()
if status['running']:
    stop_news_monitoring()
    
# Start fresh
start_news_monitoring()
```

### No News Detected

- Check keywords are not too specific
- Verify internet connection
- Increase poll interval
- Check DuckDuckGo availability

### Review Errors

- Ensure AI agent is initialized
- Check review callback is set
- Falls back to simple sentiment if AI fails

## Related Files

- `agents/tools/news_tools.py` - News tools implementation
- `ws/news/monitor.py` - News monitor implementation
- `test_news_tools.py` - Test suite
- `docs/WEB_SEARCH.md` - Web search documentation
