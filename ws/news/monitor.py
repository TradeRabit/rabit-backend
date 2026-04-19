"""
News WebSocket Monitor
Real-time news monitoring with AI review and sentiment analysis.
"""

import asyncio
import logging
import re
from collections import deque
from typing import Set, Dict, Optional, List, Callable
from datetime import datetime

from agents.tools.market.news_tools import get_news_client
from config.settings import settings

logger = logging.getLogger(__name__)


class NewsMonitor:
    """
    Real-time news monitor with AI review
    Polls for new news, analyzes sentiment, and broadcasts alerts
    """
    
    def __init__(
        self,
        poll_interval: int = 300,  # 5 minutes
        keywords: Optional[List[str]] = None,
        auto_review: bool = True,
        review_callback: Optional[Callable] = None
    ):
        """
        Initialize news monitor
        
        Args:
            poll_interval: Polling interval in seconds (default: 300)
            keywords: Keywords to monitor (default: crypto-related)
            auto_review: Enable automatic AI review (default: True)
            review_callback: Callback function for AI review (agent.chat)
        """
        self.poll_interval = poll_interval
        self.keywords = keywords or [
            "BTC|ETH|SOL",
            "crypto market",
            "DeFi",
            "NFT"
        ]
        self.auto_review = auto_review
        self.review_callback = review_callback
        
        self.running = False
        self.seen_urls: Set[str] = set()
        self.subscribers: Set[asyncio.Queue] = set()
        self.news_client = get_news_client()
        self.tracked_symbols = {
            str(symbol).strip().upper()
            for symbol in settings.TRADING_ASSETS
            if str(symbol).strip()
        }
        self.general_history = deque(maxlen=200)
        self.asset_history: Dict[str, deque] = {
            symbol: deque(maxlen=50) for symbol in self.tracked_symbols
        }
        
        # Statistics
        self.stats = {
            "total_news": 0,
            "reviewed_news": 0,
            "positive_news": 0,
            "negative_news": 0,
            "neutral_news": 0
        }
        
        logger.info(f"News monitor initialized (poll: {poll_interval}s, auto_review: {auto_review})")
    
    async def start(self):
        """Start monitoring news"""
        if self.running:
            logger.warning("News monitor already running")
            return
        
        self.running = True
        logger.info("News monitor started")
        
        # Start monitoring loop
        asyncio.create_task(self._monitor_loop())
    
    async def stop(self):
        """Stop monitoring news"""
        self.running = False
        logger.info("News monitor stopped")
    
    def subscribe(self) -> asyncio.Queue:
        """
        Subscribe to news updates
        
        Returns:
            Queue that receives news updates
        """
        queue = asyncio.Queue()
        self.subscribers.add(queue)
        logger.info(f"New subscriber added (total: {len(self.subscribers)})")
        return queue

    def ensure_symbols(self, symbols: List[str]) -> None:
        """Ensure requested asset symbols are covered by the polling keyword set."""
        for symbol in symbols:
            normalized = str(symbol).strip().upper()
            if not normalized:
                continue
            if normalized not in self.tracked_symbols:
                self.tracked_symbols.add(normalized)
                self.asset_history[normalized] = deque(maxlen=50)

            covered = any(
                normalized in {
                    token.strip().upper()
                    for token in re.split(r"[|,]", keyword)
                    if token.strip()
                }
                for keyword in self.keywords
            )
            if not covered:
                self.add_keyword(normalized)
    
    def unsubscribe(self, queue: asyncio.Queue):
        """Unsubscribe from news updates"""
        if queue in self.subscribers:
            self.subscribers.remove(queue)
            logger.info(f"Subscriber removed (total: {len(self.subscribers)})")
    
    async def _monitor_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                # Check for new news
                new_news = await self._check_new_news()
                
                if new_news:
                    logger.info(f"Found {len(new_news)} new articles")
                    
                    # Auto-review news if enabled
                    if self.auto_review and self.review_callback:
                        reviewed_news = await self._review_news(new_news)
                    else:
                        reviewed_news = new_news
                    
                    # Broadcast to all subscribers
                    await self._broadcast(reviewed_news)
                
                # Wait before next poll
                await asyncio.sleep(self.poll_interval)
            
            except Exception as e:
                logger.error(f"Monitor loop error: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error
    
    async def _check_new_news(self) -> List[Dict]:
        """Check for new news articles"""
        new_articles = []
        
        try:
            # Search for each keyword
            for keyword in self.keywords:
                results = self.news_client.search_news_by_keywords(
                    keyword,
                    max_results=5,
                    use_regex=True
                )
                
                for article in results:
                    url = article.get("url", "")
                    
                    # Skip if already seen
                    if url in self.seen_urls:
                        continue
                    
                    # Mark as seen
                    self.seen_urls.add(url)
                    
                    # Add to new articles
                    normalized_article = {
                        **article,
                        "detected_at": datetime.now().isoformat(),
                        "keyword": keyword,
                    }
                    normalized_article["symbols"] = self._extract_symbols(normalized_article)
                    new_articles.append(normalized_article)
            
            # Limit seen URLs to prevent memory growth
            if len(self.seen_urls) > 1000:
                # Keep only most recent 500
                self.seen_urls = set(list(self.seen_urls)[-500:])
        
        except Exception as e:
            logger.error(f"Check new news error: {e}")
        
        return new_articles

    def _extract_symbols(self, article: Dict) -> List[str]:
        """Infer tracked symbols mentioned in one article."""
        discovered: Set[str] = set()

        raw_symbols = article.get("symbols")
        if isinstance(raw_symbols, list):
            for symbol in raw_symbols:
                normalized = str(symbol).strip().upper()
                if normalized:
                    discovered.add(normalized)
        elif isinstance(raw_symbols, str):
            normalized = raw_symbols.strip().upper()
            if normalized:
                discovered.add(normalized)

        keyword = str(article.get("keyword", "")).strip()
        if keyword:
            for token in re.split(r"[|,]", keyword):
                normalized = token.strip().upper()
                if normalized in self.tracked_symbols:
                    discovered.add(normalized)

        matched_keywords = article.get("matched_keywords") or []
        if isinstance(matched_keywords, list):
            for token in matched_keywords:
                normalized = str(token).strip().upper()
                if normalized in self.tracked_symbols:
                    discovered.add(normalized)

        haystack = f"{article.get('title', '')} {article.get('snippet', '')}".upper()
        for symbol in self.tracked_symbols:
            if re.search(rf"\b{re.escape(symbol)}\b", haystack):
                discovered.add(symbol)

        return sorted(discovered)

    def _store_history(self, news_list: List[Dict]) -> None:
        """Store general and per-asset headline history."""
        for article in news_list:
            compact = {
                "title": article.get("title", ""),
                "url": article.get("url", ""),
                "snippet": article.get("snippet", ""),
                "date": article.get("date", ""),
                "source": article.get("source", "Unknown"),
                "detected_at": article.get("detected_at", datetime.now().isoformat()),
                "symbols": list(article.get("symbols") or []),
                "review": article.get("review"),
            }
            self.general_history.append(compact)
            for symbol in compact["symbols"]:
                if symbol not in self.asset_history:
                    self.asset_history[symbol] = deque(maxlen=50)
                self.asset_history[symbol].append(compact)

    def get_asset_news_snapshot(self, symbols: Optional[List[str]] = None, tail: int = 5) -> Dict[str, List[Dict]]:
        """Return the latest stored news items grouped by asset symbol."""
        normalized_symbols = [
            str(symbol).strip().upper()
            for symbol in (symbols or [])
            if str(symbol).strip()
        ]
        if not normalized_symbols:
            normalized_symbols = sorted(self.tracked_symbols)[:10]

        result: Dict[str, List[Dict]] = {}
        for symbol in normalized_symbols:
            items = list(self.asset_history.get(symbol, deque()))
            result[symbol] = items[-max(0, int(tail or 0)) :]
        return result

    def get_tail_titles(self, symbol: Optional[str] = None, limit: int = 5) -> List[str]:
        """Return the latest headline titles for one asset or the global stream."""
        normalized = str(symbol).strip().upper() if symbol else None
        if normalized:
            items = list(self.asset_history.get(normalized, deque()))
        else:
            items = list(self.general_history)
        return [item.get("title", "") for item in items[-max(0, int(limit or 0)) :] if item.get("title")]
    
    async def _review_news(self, news_list: List[Dict]) -> List[Dict]:
        """
        Review news using AI agent
        Analyzes sentiment and provides trading recommendations
        """
        reviewed = []
        
        for article in news_list:
            try:
                # Build review prompt
                prompt = f"""Review this crypto news and provide:
1. Sentiment (POSITIVE/NEGATIVE/NEUTRAL)
2. Impact level (HIGH/MEDIUM/LOW)
3. Affected symbols (if any)
4. Trading recommendation (BUY/SELL/HOLD/WAIT)
5. Brief analysis (max 100 chars)

News:
Title: {article['title']}
Snippet: {article['snippet']}

Respond in JSON format:
{{"sentiment": "...", "impact": "...", "symbols": [...], "recommendation": "...", "analysis": "..."}}"""

                # Call review callback (agent.chat)
                if self.review_callback:
                    review_result = await self.review_callback(prompt)
                    
                    # Parse AI response
                    import json
                    import re
                    
                    # Extract JSON from response
                    json_match = re.search(r'\{.*\}', review_result, re.DOTALL)
                    if json_match:
                        review_data = json.loads(json_match.group())
                        
                        # Add review to article
                        article['review'] = review_data
                        
                        # Update statistics
                        sentiment = review_data.get('sentiment', 'NEUTRAL').upper()
                        if sentiment == 'POSITIVE':
                            self.stats['positive_news'] += 1
                        elif sentiment == 'NEGATIVE':
                            self.stats['negative_news'] += 1
                        else:
                            self.stats['neutral_news'] += 1
                        
                        self.stats['reviewed_news'] += 1
                        
                        logger.info(f"Reviewed: {article['title'][:50]}... | Sentiment: {sentiment}")
                    else:
                        # Fallback: simple sentiment analysis
                        article['review'] = self._simple_sentiment(article)
                else:
                    # No callback, use simple sentiment
                    article['review'] = self._simple_sentiment(article)
                
                reviewed.append(article)
                
            except Exception as e:
                logger.error(f"Review error: {e}")
                # Add article without review
                article['review'] = {"error": str(e)}
                reviewed.append(article)
        
        return reviewed
    
    def _simple_sentiment(self, article: Dict) -> Dict:
        """Simple rule-based sentiment analysis (fallback)"""
        text = (article['title'] + " " + article['snippet']).lower()
        
        # Positive keywords
        positive_words = ['surge', 'rally', 'pump', 'bullish', 'gain', 'rise', 'up', 'moon', 'breakthrough', 'adoption']
        # Negative keywords
        negative_words = ['crash', 'dump', 'bearish', 'loss', 'fall', 'down', 'hack', 'scam', 'ban', 'regulation']
        
        positive_count = sum(1 for word in positive_words if word in text)
        negative_count = sum(1 for word in negative_words if word in text)
        
        if positive_count > negative_count:
            sentiment = "POSITIVE"
            recommendation = "BUY"
        elif negative_count > positive_count:
            sentiment = "NEGATIVE"
            recommendation = "SELL"
        else:
            sentiment = "NEUTRAL"
            recommendation = "HOLD"
        
        impact = "HIGH" if (positive_count + negative_count) >= 3 else "MEDIUM" if (positive_count + negative_count) >= 1 else "LOW"
        
        return {
            "sentiment": sentiment,
            "impact": impact,
            "symbols": [],
            "recommendation": recommendation,
            "analysis": "Auto-generated sentiment analysis",
            "method": "simple"
        }
    
    async def _broadcast(self, news: List[Dict]):
        """Broadcast news to all subscribers"""
        if not self.subscribers:
            self._store_history(news)
            return
        
        # Separate by sentiment for prioritization
        high_impact = [n for n in news if n.get('review', {}).get('impact') == 'HIGH']
        negative = [n for n in news if n.get('review', {}).get('sentiment') == 'NEGATIVE']
        positive = [n for n in news if n.get('review', {}).get('sentiment') == 'POSITIVE']
        
        message = {
            "type": "news_update",
            "timestamp": datetime.now().isoformat(),
            "count": len(news),
            "high_impact_count": len(high_impact),
            "negative_count": len(negative),
            "positive_count": len(positive),
            "news": news,
            "stats": self.stats
        }
        self._store_history(news)
        
        # Send to all subscribers
        dead_queues = []
        for queue in self.subscribers:
            try:
                await queue.put(message)
            except Exception as e:
                logger.error(f"Broadcast error: {e}")
                dead_queues.append(queue)
        
        # Remove dead queues
        for queue in dead_queues:
            self.unsubscribe(queue)
    
    def add_keyword(self, keyword: str):
        """Add keyword to monitor"""
        if keyword not in self.keywords:
            self.keywords.append(keyword)
            logger.info(f"Added keyword: {keyword}")
    
    def remove_keyword(self, keyword: str):
        """Remove keyword from monitoring"""
        if keyword in self.keywords:
            self.keywords.remove(keyword)
            logger.info(f"Removed keyword: {keyword}")
    
    def get_stats(self) -> Dict:
        """Get monitor statistics"""
        return {
            "running": self.running,
            "poll_interval": self.poll_interval,
            "keywords": self.keywords,
            "subscribers": len(self.subscribers),
            "seen_urls": len(self.seen_urls),
            "auto_review": self.auto_review,
            **self.stats
        }
    
    def set_review_callback(self, callback: Callable):
        """Set AI review callback function"""
        self.review_callback = callback
        logger.info("Review callback set")
    
    def enable_auto_review(self):
        """Enable automatic AI review"""
        self.auto_review = True
        logger.info("Auto-review enabled")
    
    def disable_auto_review(self):
        """Disable automatic AI review"""
        self.auto_review = False
        logger.info("Auto-review disabled")


# Singleton instance
_news_monitor: Optional[NewsMonitor] = None


def get_news_monitor() -> NewsMonitor:
    """Get or create NewsMonitor singleton"""
    global _news_monitor
    if _news_monitor is None:
        _news_monitor = NewsMonitor()
    return _news_monitor
