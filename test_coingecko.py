"""
Test CoinGecko Integration
Test untuk memastikan CoinGecko client dan database bekerja dengan baik
Hanya untuk basic information (description, links, categories)
"""
import asyncio
import logging
from ws.services import get_market_service
from ws.coingecko import get_coin_database

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_coingecko_integration():
    """Test CoinGecko integration for basic information"""
    logger.info("\n" + "="*60)
    logger.info("Testing CoinGecko Integration (Basic Info Only)")
    logger.info("="*60)
    
    # Get service
    service = get_market_service()
    db = get_coin_database()
    
    # Test symbols
    test_symbols = ["BTC", "ETH", "SOL"]
    
    # Test 1: Get coin info (fetch from CoinGecko)
    logger.info("\n" + "="*60)
    logger.info("TEST 1: Get Coin Basic Info from CoinGecko")
    logger.info("="*60)
    
    for symbol in test_symbols:
        logger.info(f"\nFetching info for {symbol}...")
        coin_info = await service.get_coin_info(symbol)
        
        if coin_info:
            logger.info(f"✅ {symbol} - {coin_info.name}")
            logger.info(f"   Description: {coin_info.description[:100]}...")
            logger.info(f"   Website: {coin_info.links.website if coin_info.links else 'N/A'}")
            logger.info(f"   Twitter: {coin_info.links.twitter if coin_info.links else 'N/A'}")
            logger.info(f"   Explorer: {coin_info.links.explorer if coin_info.links else 'N/A'}")
            logger.info(f"   Categories: {', '.join(coin_info.categories[:3])}")
        else:
            logger.error(f"❌ Failed to fetch {symbol}")
    
    # Test 2: Check database
    logger.info("\n" + "="*60)
    logger.info("TEST 2: Check Database")
    logger.info("="*60)
    
    stats = db.get_stats()
    logger.info(f"Total coins in database: {stats['total_coins']}")
    logger.info(f"Oldest update: {stats['oldest_update']}")
    logger.info(f"Newest update: {stats['newest_update']}")
    
    # Test 3: Get from cache (should be instant)
    logger.info("\n" + "="*60)
    logger.info("TEST 3: Get from Cache (No API Call)")
    logger.info("="*60)
    
    for symbol in test_symbols:
        logger.info(f"\nGetting cached info for {symbol}...")
        coin_info = await service.get_coin_info(symbol)
        
        if coin_info:
            logger.info(f"✅ {symbol} - {coin_info.name} (from cache)")
        else:
            logger.error(f"❌ Failed to get cached data for {symbol}")
    
    # Test 4: Get multiple coins at once
    logger.info("\n" + "="*60)
    logger.info("TEST 4: Get Multiple Coins")
    logger.info("="*60)
    
    all_info = await service.get_multiple_coins_info(test_symbols)
    logger.info(f"✅ Fetched info for {len(all_info)} coins")
    
    for symbol, info in all_info.items():
        logger.info(f"\n{symbol}:")
        logger.info(f"  Name: {info.name}")
        logger.info(f"  Description: {info.description[:80]}...")
        logger.info(f"  Website: {info.links.website if info.links else 'N/A'}")
        logger.info(f"  Categories: {', '.join(info.categories[:2])}")
    
    # Test 5: Database stats
    logger.info("\n" + "="*60)
    logger.info("TEST 5: Database Statistics")
    logger.info("="*60)
    
    stats = service.get_database_stats()
    logger.info(f"Total coins: {stats['total_coins']}")
    logger.info(f"All symbols: {', '.join(db.get_all_symbols())}")
    
    logger.info("\n" + "="*60)
    logger.info("✅ All tests completed!")
    logger.info("="*60)
    logger.info("\nNote: Price data should come from Drift WS, not CoinGecko")


if __name__ == "__main__":
    asyncio.run(test_coingecko_integration())
