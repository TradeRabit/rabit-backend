"""
News WebSocket Monitor
Real-time news monitoring with AI review and sentiment analysis
"""

import asyncio
import logging
from typing import Set, Dict, Optional, List, Callable
from datetime import datetime
from agents.tools.news_tools import get_news_client

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
                    new_articles.append({
                        **article,
                        "detected_at": datetime.now().isoformat(),
                        "keyword": keyword
                    })
            
            # Limit seen URLs to prevent memory growth
            if len(self.seen_urls) > 1000:
                # Keep only most recent 500
                self.seen_urls = set(list(self.seen_urls)[-500:])
        
        except Exception as e:
            logger.error(f"Check new news error: {e}")
        
        return new_articles
    
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
