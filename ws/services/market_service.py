"""
Market Data Service
Service untuk mengelola coin basic information dari CoinGecko
Price data di-handle oleh Drift WS
"""
import asyncio
from typing import Optional, Dict, List
from datetime import datetime
import logging

from ws.models.coin_info import CoinInfo
from ws.coingecko.client import get_coingecko_client
from ws.coingecko.database import get_coin_database

logger = logging.getLogger(__name__)


class MarketDataService:
    """
    Service untuk mengelola coin basic information
    - CoinGecko: Description, links, categories (jarang berubah)
    - Drift WS: Price, volume, OI, funding (real-time)
    """
    
    def __init__(self):
        self.coingecko = get_coingecko_client()
        self.db = get_coin_database()
        
        # Mapping symbol to CoinGecko ID
        self.symbol_to_id: Dict[str, str] = {
            "BTC": "bitcoin",
            "ETH": "ethereum",
            "SOL": "solana",
            "USDT": "tether",
            "USDC": "usd-coin",
            "BNB": "binancecoin",
            "XRP": "ripple",
            "ADA": "cardano",
            "AVAX": "avalanche-2",
            "DOT": "polkadot",
            "MATIC": "matic-network",
            "LINK": "chainlink",
            "UNI": "uniswap",
            "ATOM": "cosmos",
            "LTC": "litecoin",
            "NEAR": "near",
            "APT": "aptos",
            "ARB": "arbitrum",
            "OP": "optimism",
            "SUI": "sui",
        }
    
    async def get_coin_info(self, symbol: str) -> Optional[CoinInfo]:
        """
        Get coin basic information
        Check database first, fetch from CoinGecko if needed
        
        Args:
            symbol: Coin symbol (e.g., 'BTC')
            
        Returns:
            CoinInfo or None if failed
        """
        symbol = symbol.upper()
        
        # Check database first
        coin_info = self.db.get_coin_info(symbol)
        
        # If found in database and not stale, return it
        if coin_info and not self.db.is_stale(symbol, max_age_days=30):
            logger.debug(f"Using cached coin info for {symbol}")
            return coin_info
        
        # Not in database or stale, fetch from CoinGecko
        logger.info(f"Fetching coin info for {symbol} from CoinGecko")
        
        # Get CoinGecko ID
        coin_id = self.symbol_to_id.get(symbol)
        if not coin_id:
            # Try to search
            coin_id = await self.coingecko.search_coin_by_symbol(symbol)
            if coin_id:
                self.symbol_to_id[symbol] = coin_id
        
        if not coin_id:
            logger.warning(f"Could not find CoinGecko ID for {symbol}")
            return None
        
        # Fetch coin info
        coin_info = await self.coingecko.get_coin_info(coin_id)
        
        if coin_info:
            # Save to database
            self.db.save_coin_info(coin_info)
            return coin_info
        
        return None
    
    async def get_multiple_coins_info(self, symbols: List[str]) -> Dict[str, CoinInfo]:
        """
        Get basic information for multiple coins
        
        Args:
            symbols: List of coin symbols
            
        Returns:
            Dict mapping symbol to CoinInfo
        """
        result = {}
        
        # Fetch all coins concurrently
        tasks = [self.get_coin_info(symbol) for symbol in symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for symbol, data in zip(symbols, results):
            if isinstance(data, Exception):
                logger.error(f"Error fetching info for {symbol}: {data}")
                continue
            
            if data:
                result[symbol.upper()] = data
        
        return result
    
    async def initialize_coins(self, symbols: List[str]):
        """
        Initialize coin info for all symbols
        Only fetch from CoinGecko if not in database.
        Retries until all requested symbols are covered.
        
        Args:
            symbols: List of coin symbols to initialize
        """
        logger.info(f"Initializing coin info for {len(symbols)} symbols")
        
        # Check which coins need to be fetched
        coins_to_fetch = []
        for symbol in symbols:
            symbol = symbol.upper()
            coin_info = self.db.get_coin_info(symbol)
            
            # Only fetch if not in database or stale
            if not coin_info or self.db.is_stale(symbol, max_age_days=30):
                coins_to_fetch.append(symbol)
            else:
                logger.debug(f"Coin {symbol} already in database")
        
        if not coins_to_fetch:
            logger.info("All coins already in database")
            return
        
        remaining_symbols = coins_to_fetch[:]
        attempt_counts = {symbol: 0 for symbol in remaining_symbols}
        round_number = 0

        while remaining_symbols:
            round_number += 1
            logger.info(
                f"Fetching {len(remaining_symbols)} coins from CoinGecko "
                f"(round {round_number}): {', '.join(remaining_symbols)}"
            )

            failed_symbols = []

            for symbol in remaining_symbols:
                attempt_counts[symbol] += 1

                try:
                    coin_info = await self.get_coin_info(symbol)

                    if coin_info:
                        logger.info(
                            f"Initialized coin info for {symbol} "
                            f"on attempt {attempt_counts[symbol]}"
                        )
                    else:
                        failed_symbols.append(symbol)
                        logger.warning(
                            f"Coin info for {symbol} unavailable on attempt "
                            f"{attempt_counts[symbol]}; scheduling retry"
                        )

                    # Small delay to respect rate limits
                    await asyncio.sleep(0.5)

                except Exception as e:
                    failed_symbols.append(symbol)
                    logger.error(f"Error fetching {symbol} on attempt {attempt_counts[symbol]}: {e}")

            if not failed_symbols:
                break

            retry_delay = min(60, max(5, 5 * round_number))
            logger.warning(
                f"Retrying {len(failed_symbols)} unresolved coins after {retry_delay} seconds: "
                f"{', '.join(failed_symbols)}"
            )
            await asyncio.sleep(retry_delay)
            remaining_symbols = failed_symbols
        
        logger.info("Coin info initialization complete")
    
    def get_database_stats(self) -> Dict:
        """Get database statistics"""
        return self.db.get_stats()


# Singleton instance
_market_service: Optional[MarketDataService] = None


def get_market_service() -> MarketDataService:
    """Get or create MarketDataService singleton"""
    global _market_service
    if _market_service is None:
        _market_service = MarketDataService()
    return _market_service
