"""
CoinGecko API Client
Client untuk mengambil data dari CoinGecko Free API
Hanya untuk basic information (description, links, categories)
"""
import aiohttp
import asyncio
from typing import Optional, List, Dict
from datetime import datetime, timedelta
import logging

from ws.models.coin_info import CoinInfo, CoinLinks
from ws.utils.categories import normalize_categories
from config.settings import settings

logger = logging.getLogger(__name__)


class CoinGeckoClient:
    """
    CoinGecko API Client untuk free tier
    Rate limit: 10-50 calls/minute (free tier)
    Hanya untuk mengambil basic information
    """
    
    BASE_URL = "https://api.coingecko.com/api/v3"
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.rate_limit_delay = 2.0  # 2 detik delay antar request untuk free tier
        self.last_request_time = datetime.utcnow()
        
    async def _ensure_session(self):
        """Ensure aiohttp session exists"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
    
    async def _rate_limit(self):
        """Apply rate limiting untuk free tier"""
        now = datetime.utcnow()
        time_since_last = (now - self.last_request_time).total_seconds()
        
        if time_since_last < self.rate_limit_delay:
            await asyncio.sleep(self.rate_limit_delay - time_since_last)
        
        self.last_request_time = datetime.utcnow()
    
    async def _get(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """Make GET request with rate limiting"""
        await self._ensure_session()
        await self._rate_limit()
        
        url = f"{self.BASE_URL}{endpoint}"
        
        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 429:
                    logger.warning("Rate limit exceeded, waiting 60 seconds...")
                    await asyncio.sleep(60)
                    return await self._get(endpoint, params)
                else:
                    logger.error(f"CoinGecko API error: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error fetching from CoinGecko: {e}")
            return None
    
    async def get_coin_info(self, coin_id: str) -> Optional[CoinInfo]:
        """
        Get detailed coin information (basic info only)
        
        Args:
            coin_id: CoinGecko coin ID (e.g., 'bitcoin', 'ethereum')
            
        Returns:
            CoinInfo object or None if failed
        """
        endpoint = f"/coins/{coin_id}"
        params = {
            "localization": "false",
            "tickers": "false",
            "market_data": "false",
            "community_data": "false",
            "developer_data": "false"
        }
        
        data = await self._get(endpoint, params)
        
        if not data:
            return None
        
        try:
            # Parse links
            links_data = data.get("links", {})
            links = CoinLinks(
                website=links_data.get("homepage", [None])[0],
                twitter=f"https://twitter.com/{links_data.get('twitter_screen_name')}" if links_data.get('twitter_screen_name') else None,
                telegram=links_data.get("telegram_channel_identifier"),
                github=links_data.get("repos_url", {}).get("github", [None])[0],
                whitepaper=links_data.get("whitepaper"),
                explorer=links_data.get("blockchain_site", [None])[0]
            )
            
            # Parse contract addresses
            platforms = data.get("platforms", {})
            contract_address = {k: v for k, v in platforms.items() if v}
            
            # Parse description (ambil English)
            description = data.get("description", {}).get("en", "")
            # Limit description length
            if len(description) > 500:
                description = description[:497] + "..."
            
            coin_info = CoinInfo(
                id=data.get("id"),
                symbol=data.get("symbol", "").upper(),
                name=data.get("name"),
                description=description,
                links=links,
                contract_address=contract_address,
                categories=normalize_categories(data.get("categories", [])),  # Normalize categories
                last_updated=datetime.utcnow()
            )
            
            logger.info(f"Fetched coin info for {coin_id}")
            return coin_info
            
        except Exception as e:
            logger.error(f"Error parsing coin info for {coin_id}: {e}")
            return None
    
    async def search_coin_by_symbol(self, symbol: str) -> Optional[str]:
        """
        Search for coin ID by symbol
        
        Args:
            symbol: Coin symbol (e.g., 'BTC', 'ETH')
            
        Returns:
            CoinGecko coin ID or None
        """
        endpoint = "/search"
        params = {"query": symbol}
        
        data = await self._get(endpoint, params)
        
        if not data or "coins" not in data:
            return None
        
        # Find exact symbol match
        for coin in data["coins"]:
            if coin.get("symbol", "").upper() == symbol.upper():
                return coin.get("id")
        
        return None
    
    async def close(self):
        """Close aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()
            logger.info("CoinGecko client session closed")


# Singleton instance
_coingecko_client: Optional[CoinGeckoClient] = None


def get_coingecko_client() -> CoinGeckoClient:
    """Get or create CoinGecko client singleton"""
    global _coingecko_client
    if _coingecko_client is None:
        _coingecko_client = CoinGeckoClient()
    return _coingecko_client


