"""
News Tools - Polymorphic news search and monitoring
Supports regex keyword matching for multi-symbol search
"""

import logging
import re
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from ddgs import DDGS

logger = logging.getLogger(__name__)


class NewsClient:
    """
    News client with polymorphic search capabilities
    Supports regex keyword matching for advanced filtering
    """
    
    def __init__(self):
        """Initialize news client"""
        self.enabled = True
        self.cache = {}  # Simple cache for trending news
        self.cache_ttl = 300  # 5 minutes
        
        logger.info("News client initialized")
    
    def get_latest_news(
        self, 
        category: str = "crypto",
        max_results: int = 10
    ) -> List[Dict[str, str]]:
        """
        Get latest news from specific category
        
        Args:
            category: News category (crypto, general, finance)
            max_results: Maximum results (default: 10)
            
        Returns:
            List of latest news with title, url, snippet, date
        """
        try:
            # Build query based on category
            queries = {
                "crypto": "cryptocurrency bitcoin ethereum solana",
                "general": "breaking news today",
                "finance": "financial markets trading",
                "defi": "DeFi decentralized finance",
                "nft": "NFT non-fungible token"
            }
            
            query = queries.get(category, queries["crypto"])
            
            with DDGS() as ddgs:
                results = []
                
                for result in ddgs.news(query, max_results=max_results):
                    results.append({
                        "title": result.get("title", "")[:100],
                        "url": result.get("url", ""),
                        "snippet": result.get("body", "")[:200],
                        "date": result.get("date", ""),
                        "source": result.get("source", "Unknown")
                    })
                
                logger.info(f"Found {len(results)} latest {category} news")
                return results
        
        except Exception as e:
            logger.error(f"Get latest news error: {e}")
            return []
    
    def search_news_by_keywords(
        self,
        keywords: str,
        max_results: int = 10,
        use_regex: bool = True
    ) -> List[Dict[str, str]]:
        """
        Search news by keywords with regex support
        
        Args:
            keywords: Keywords to search (supports regex like "BTC|ETH|TRUMP")
            max_results: Maximum results (default: 10)
            use_regex: Enable regex matching (default: True)
            
        Returns:
            List of news matching keywords
        """
        try:
            # If regex enabled, convert to search query
            if use_regex and "|" in keywords:
                # Convert "BTC|ETH|TRUMP" to search for each term
                # Then filter with regex (more reliable than complex OR queries)
                search_terms = keywords.split("|")
                
                # Use first term for search, then filter with regex
                query = search_terms[0].strip()
            else:
                query = keywords
            
            with DDGS() as ddgs:
                results = []
                
                # Get more results for filtering
                search_limit = max_results * 3 if use_regex and "|" in keywords else max_results
                
                for result in ddgs.news(query, max_results=search_limit):
                    title = result.get("title", "")
                    body = result.get("body", "")
                    
                    # Apply regex filter if enabled
                    if use_regex and "|" in keywords:
                        pattern = re.compile(keywords, re.IGNORECASE)
                        if not (pattern.search(title) or pattern.search(body)):
                            continue
                    
                    results.append({
                        "title": title[:100],
                        "url": result.get("url", ""),
                        "snippet": body[:200],
                        "date": result.get("date", ""),
                        "source": result.get("source", "Unknown"),
                        "matched_keywords": self._extract_matched_keywords(
                            title + " " + body, 
                            keywords
                        )
                    })
                    
                    if len(results) >= max_results:
                        break
                
                logger.info(f"Found {len(results)} news for keywords: {keywords}")
                return results
        
        except Exception as e:
            logger.error(f"Search news by keywords error: {e}")
            return []
    
    def get_trending_news(
        self,
        timeframe: str = "24h",
        max_results: int = 10
    ) -> List[Dict[str, str]]:
        """
        Get trending crypto news
        
        Args:
            timeframe: Time frame (24h, 7d, 30d)
            max_results: Maximum results (default: 10)
            
        Returns:
            List of trending news
        """
        try:
            # Check cache
            cache_key = f"trending_{timeframe}"
            if cache_key in self.cache:
                cached_time, cached_data = self.cache[cache_key]
                if (datetime.now() - cached_time).seconds < self.cache_ttl:
                    logger.info(f"Returning cached trending news ({timeframe})")
                    return cached_data
            
            # Trending crypto topics
            trending_queries = [
                "bitcoin price surge",
                "ethereum breaking news",
                "crypto market rally",
                "altcoin pump",
                "defi protocol hack",
                "crypto regulation news"
            ]
            
            all_results = []
            
            with DDGS() as ddgs:
                for query in trending_queries[:3]:  # Limit queries
                    for result in ddgs.news(query, max_results=5):
                        all_results.append({
                            "title": result.get("title", "")[:100],
                            "url": result.get("url", ""),
                            "snippet": result.get("body", "")[:200],
                            "date": result.get("date", ""),
                            "source": result.get("source", "Unknown"),
                            "category": self._categorize_news(result.get("title", ""))
                        })
            
            # Sort by date (most recent first)
            all_results.sort(
                key=lambda x: x.get("date", ""), 
                reverse=True
            )
            
            # Remove duplicates by URL
            seen_urls = set()
            unique_results = []
            for result in all_results:
                if result["url"] not in seen_urls:
                    seen_urls.add(result["url"])
                    unique_results.append(result)
                    if len(unique_results) >= max_results:
                        break
            
            # Cache results
            self.cache[cache_key] = (datetime.now(), unique_results)
            
            logger.info(f"Found {len(unique_results)} trending news")
            return unique_results
        
        except Exception as e:
            logger.error(f"Get trending news error: {e}")
            return []
    
    def search_news_by_symbols(
        self,
        symbols: List[str],
        max_results: int = 10
    ) -> Dict[str, List[Dict[str, str]]]:
        """
        Search news for multiple symbols
        
        Args:
            symbols: List of symbols (e.g., ["BTC", "ETH", "SOL"])
            max_results: Maximum results per symbol
            
        Returns:
            Dictionary mapping symbol to news list
        """
        try:
            results = {}
            
            for symbol in symbols:
                # Search for symbol-specific news
                query = f"{symbol} cryptocurrency"
                
                with DDGS() as ddgs:
                    symbol_news = []
                    
                    for result in ddgs.news(query, max_results=max_results):
                        symbol_news.append({
                            "title": result.get("title", "")[:100],
                            "url": result.get("url", ""),
                            "snippet": result.get("body", "")[:200],
                            "date": result.get("date", ""),
                            "source": result.get("source", "Unknown"),
                            "symbol": symbol
                        })
                    
                    results[symbol] = symbol_news
                    logger.info(f"Found {len(symbol_news)} news for {symbol}")
            
            return results
        
        except Exception as e:
            logger.error(f"Search news by symbols error: {e}")
            return {}
    
    def _extract_matched_keywords(self, text: str, keywords: str) -> List[str]:
        """Extract matched keywords from text"""
        try:
            pattern = re.compile(keywords, re.IGNORECASE)
            matches = pattern.findall(text)
            return list(set(matches))[:5]  # Max 5 unique matches
        except:
            return []
    
    def _categorize_news(self, title: str) -> str:
        """Categorize news based on title"""
        title_lower = title.lower()
        
        if any(word in title_lower for word in ["price", "surge", "rally", "pump", "dump"]):
            return "price_movement"
        elif any(word in title_lower for word in ["hack", "exploit", "scam", "fraud"]):
            return "security"
        elif any(word in title_lower for word in ["regulation", "sec", "law", "ban"]):
            return "regulation"
        elif any(word in title_lower for word in ["launch", "release", "upgrade", "update"]):
            return "development"
        else:
            return "general"


# Singleton instance
_news_client: Optional[NewsClient] = None


def get_news_client() -> NewsClient:
    """Get or create NewsClient singleton"""
    global _news_client
    if _news_client is None:
        _news_client = NewsClient()
    return _news_client


# Tool functions for agent

def get_latest_news(category: str = "crypto", max_results: int = 10) -> dict:
    """
    Get latest news from specific category
    
    Args:
        category: News category (crypto, general, finance, defi, nft)
        max_results: Maximum results (default: 10)
        
    Returns:
        Latest news with metadata
    """
    client = get_news_client()
    results = client.get_latest_news(category, max_results)
    
    if not results:
        return {
            "success": False,
            "error": f"No news found for category: {category}",
            "results": []
        }
    
    return {
        "success": True,
        "category": category,
        "count": len(results),
        "results": results
    }


def search_news_by_keywords(keywords: str, max_results: int = 10) -> dict:
    """
    Search news by keywords with regex support
    
    Args:
        keywords: Keywords (supports regex like "BTC|ETH|TRUMP")
        max_results: Maximum results (default: 10)
        
    Returns:
        News matching keywords
    """
    client = get_news_client()
    use_regex = "|" in keywords or "(" in keywords
    results = client.search_news_by_keywords(keywords, max_results, use_regex)
    
    if not results:
        return {
            "success": False,
            "error": f"No news found for keywords: {keywords}",
            "results": []
        }
    
    return {
        "success": True,
        "keywords": keywords,
        "regex_enabled": use_regex,
        "count": len(results),
        "results": results
    }


def get_trending_news(timeframe: str = "24h", max_results: int = 10) -> dict:
    """
    Get trending crypto news
    
    Args:
        timeframe: Time frame (24h, 7d, 30d)
        max_results: Maximum results (default: 10)
        
    Returns:
        Trending news
    """
    client = get_news_client()
    results = client.get_trending_news(timeframe, max_results)
    
    if not results:
        return {
            "success": False,
            "error": "No trending news found",
            "results": []
        }
    
    return {
        "success": True,
        "timeframe": timeframe,
        "count": len(results),
        "results": results
    }


def search_news_by_symbols(symbols: str, max_results: int = 5) -> dict:
    """
    Search news for multiple symbols
    
    Args:
        symbols: Comma-separated symbols (e.g., "BTC,ETH,SOL")
        max_results: Maximum results per symbol (default: 5)
        
    Returns:
        News grouped by symbol
    """
    client = get_news_client()
    symbol_list = [s.strip().upper() for s in symbols.split(",")]
    results = client.search_news_by_symbols(symbol_list, max_results)
    
    if not results:
        return {
            "success": False,
            "error": f"No news found for symbols: {symbols}",
            "results": {}
        }
    
    return {
        "success": True,
        "symbols": symbol_list,
        "count": sum(len(news) for news in results.values()),
        "results": results
    }



# News monitoring tools

def start_news_monitoring(keywords: str = "BTC|ETH|SOL", poll_interval: int = 300) -> dict:
    """
    Start real-time news monitoring with AI review
    
    Args:
        keywords: Keywords to monitor (supports regex like "BTC|ETH|SOL")
        poll_interval: Polling interval in seconds (default: 300 = 5 minutes)
        
    Returns:
        Monitoring status
    """
    try:
        from ws.news import get_news_monitor
        
        monitor = get_news_monitor()
        
        # Set keywords
        keyword_list = [k.strip() for k in keywords.split(",")]
        monitor.keywords = keyword_list
        monitor.poll_interval = poll_interval
        
        # Start monitoring (async)
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        if not monitor.running:
            asyncio.create_task(monitor.start())
        
        return {
            "success": True,
            "message": "News monitoring started",
            "keywords": keyword_list,
            "poll_interval": poll_interval,
            "auto_review": monitor.auto_review
        }
    
    except Exception as e:
        logger.error(f"Start monitoring error: {e}")
        return {
            "success": False,
            "error": str(e)
        }


def stop_news_monitoring() -> dict:
    """
    Stop news monitoring
    
    Returns:
        Stop status
    """
    try:
        from ws.news import get_news_monitor
        
        monitor = get_news_monitor()
        
        import asyncio
        asyncio.create_task(monitor.stop())
        
        return {
            "success": True,
            "message": "News monitoring stopped",
            "stats": monitor.get_stats()
        }
    
    except Exception as e:
        logger.error(f"Stop monitoring error: {e}")
        return {
            "success": False,
            "error": str(e)
        }


def get_monitoring_status() -> dict:
    """
    Get news monitoring status and statistics
    
    Returns:
        Monitoring status and stats
    """
    try:
        from ws.news import get_news_monitor
        
        monitor = get_news_monitor()
        stats = monitor.get_stats()
        
        return {
            "success": True,
            **stats
        }
    
    except Exception as e:
        logger.error(f"Get status error: {e}")
        return {
            "success": False,
            "error": str(e)
        }
