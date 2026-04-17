"""
Web Search Tool using DuckDuckGo (100% FREE, No API Key, No Docker)
Provides free web search using ddgs library
"""

import logging
from typing import List, Dict, Optional

from config.settings import settings

logger = logging.getLogger(__name__)

# Try to import ddgs
try:
    from ddgs import DDGS
    DDGS_AVAILABLE = True
except ImportError:
    DDGS_AVAILABLE = False
    logger.warning("ddgs not installed. Run: pip install ddgs")


class WebSearchClient:
    """
    DuckDuckGo web search client (100% FREE)
    Returns minimal, efficient JSON responses
    """
    
    def __init__(self):
        """Initialize web search client"""
        self.enabled = DDGS_AVAILABLE and settings.WEB_SEARCH_ENABLED
        
        if self.enabled:
            logger.info("Web search enabled: DuckDuckGo")
        elif not settings.WEB_SEARCH_ENABLED:
            logger.info("Web search disabled by WEB_SEARCH_ENABLED=false")
        else:
            logger.warning("Web search disabled: duckduckgo-search not installed")
    
    def search(
        self, 
        query: str, 
        max_results: int = 5,
        region: str = "wt-wt"
    ) -> List[Dict[str, str]]:
        """
        Search web using DuckDuckGo
        
        Args:
            query: Search query
            max_results: Maximum number of results (default: 5)
            region: Region code (default: "wt-wt" for worldwide)
            
        Returns:
            Minimal list of search results:
            [
                {
                    "title": "Result title",
                    "url": "https://example.com",
                    "snippet": "Brief description..."
                }
            ]
        """
        if not self.enabled:
            logger.warning("Web search is disabled")
            return []
        
        try:
            # Use DuckDuckGo search
            with DDGS() as ddgs:
                results = []
                
                # Search and get results
                for result in ddgs.text(query, region=region, max_results=max_results):
                    # Extract minimal data
                    minimal_result = {
                        "title": result.get("title", "")[:100],  # Max 100 chars
                        "url": result.get("href", ""),
                        "snippet": result.get("body", "")[:200]  # Max 200 chars
                    }
                    
                    # Skip if missing essential data
                    if minimal_result["title"] and minimal_result["url"]:
                        results.append(minimal_result)
                
                logger.info(f"Found {len(results)} results for: {query}")
                return results
        
        except Exception as e:
            logger.error(f"Search error: {e}")
            return []
    
    def search_news(self, query: str, max_results: int = 5) -> List[Dict[str, str]]:
        """
        Search news using DuckDuckGo News
        
        Args:
            query: Search query
            max_results: Maximum results
            
        Returns:
            Minimal news results
        """
        if not self.enabled:
            logger.warning("Web search is disabled")
            return []
        
        try:
            with DDGS() as ddgs:
                results = []
                
                # Search news
                for result in ddgs.news(query, max_results=max_results):
                    minimal_result = {
                        "title": result.get("title", "")[:100],
                        "url": result.get("url", ""),
                        "snippet": result.get("body", "")[:200],
                        "date": result.get("date", "")
                    }
                    
                    if minimal_result["title"] and minimal_result["url"]:
                        results.append(minimal_result)
                
                logger.info(f"Found {len(results)} news results for: {query}")
                return results
        
        except Exception as e:
            logger.error(f"News search error: {e}")
            return []
    
    def search_crypto(self, query: str, max_results: int = 5) -> List[Dict[str, str]]:
        """
        Search crypto-related content
        
        Args:
            query: Search query (e.g., "Bitcoin price analysis")
            max_results: Maximum results
            
        Returns:
            Minimal crypto results
        """
        # Add crypto context to query
        crypto_query = f"{query} cryptocurrency crypto"
        return self.search(crypto_query, max_results)


# Singleton instance
_web_search_client: Optional[WebSearchClient] = None


def get_web_search_client() -> WebSearchClient:
    """Get or create WebSearchClient singleton"""
    global _web_search_client
    if _web_search_client is None:
        _web_search_client = WebSearchClient()
    return _web_search_client


# Tool function for agent
def web_search(query: str, max_results: int = 5) -> dict:
    """
    Web search tool for agent
    
    Args:
        query: Search query
        max_results: Maximum results (default: 5)
        
    Returns:
        Search results in minimal format
    """
    client = get_web_search_client()
    
    if not client.enabled:
        return {
            "success": False,
            "error": (
                "Web search is disabled by configuration"
                if not settings.WEB_SEARCH_ENABLED
                else "Web search is disabled. Install: pip install ddgs"
            ),
            "results": []
        }
    
    results = client.search(query, max_results)
    
    if not results:
        return {
            "success": False,
            "error": f"No results found for: {query}",
            "results": []
        }
    
    return {
        "success": True,
        "query": query,
        "count": len(results),
        "results": results
    }
