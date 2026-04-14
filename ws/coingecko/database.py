"""
Simple JSON Database for CoinGecko Data
Menyimpan data coin info secara permanen untuk menghindari rate limit
"""
import json
import os
from typing import Optional, Dict, List
from datetime import datetime, timedelta
import logging
from pathlib import Path

from ws.models.coin_info import CoinInfo

logger = logging.getLogger(__name__)


class CoinDatabase:
    """
    Simple JSON-based database untuk menyimpan coin info
    Data disimpan di file JSON untuk persistence
    """
    
    def __init__(self, db_path: str = "data/coins.json"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.data: Dict[str, dict] = {}
        self.load()
        
    def load(self):
        """Load database from file"""
        if self.db_path.exists():
            try:
                with open(self.db_path, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
                logger.info(f"Loaded {len(self.data)} coins from database")
            except Exception as e:
                logger.error(f"Error loading database: {e}")
                self.data = {}
        else:
            logger.info("Database file not found, starting fresh")
            self.data = {}
    
    def save(self):
        """Save database to file"""
        try:
            with open(self.db_path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False, default=str)
            logger.debug(f"Saved {len(self.data)} coins to database")
        except Exception as e:
            logger.error(f"Error saving database: {e}")
    
    def get_coin_info(self, symbol: str) -> Optional[CoinInfo]:
        """
        Get coin info from database
        
        Args:
            symbol: Coin symbol (e.g., 'BTC')
            
        Returns:
            CoinInfo or None if not found
        """
        symbol = symbol.upper()
        
        if symbol not in self.data:
            return None
        
        try:
            coin_data = self.data[symbol]
            return CoinInfo(**coin_data)
        except Exception as e:
            logger.error(f"Error parsing coin info for {symbol}: {e}")
            return None
    
    def save_coin_info(self, coin_info: CoinInfo):
        """
        Save coin info to database
        
        Args:
            coin_info: CoinInfo object to save
        """
        symbol = coin_info.symbol.upper()
        
        try:
            self.data[symbol] = coin_info.model_dump(mode='json')
            self.save()
            logger.info(f"Saved coin info for {symbol}")
        except Exception as e:
            logger.error(f"Error saving coin info for {symbol}: {e}")
    
    def is_stale(self, symbol: str, max_age_days: int = 30) -> bool:
        """
        Check if coin info is stale and needs refresh
        
        Args:
            symbol: Coin symbol
            max_age_days: Maximum age in days before considering stale
            
        Returns:
            True if stale or not found, False if fresh
        """
        coin_info = self.get_coin_info(symbol)
        
        if not coin_info:
            return True
        
        age = datetime.utcnow() - coin_info.last_updated
        return age > timedelta(days=max_age_days)
    
    def get_all_symbols(self) -> List[str]:
        """Get all coin symbols in database"""
        return list(self.data.keys())
    
    def delete_coin(self, symbol: str):
        """Delete coin from database"""
        symbol = symbol.upper()
        if symbol in self.data:
            del self.data[symbol]
            self.save()
            logger.info(f"Deleted coin {symbol} from database")
    
    def clear(self):
        """Clear all data from database"""
        self.data = {}
        self.save()
        logger.info("Cleared database")
    
    def get_stats(self) -> Dict:
        """Get database statistics"""
        if not self.data:
            return {
                "total_coins": 0,
                "oldest_update": None,
                "newest_update": None
            }
        
        updates = []
        for coin_data in self.data.values():
            try:
                last_updated = datetime.fromisoformat(coin_data.get("last_updated", ""))
                updates.append(last_updated)
            except:
                pass
        
        return {
            "total_coins": len(self.data),
            "oldest_update": min(updates) if updates else None,
            "newest_update": max(updates) if updates else None
        }


# Singleton instance
_coin_database: Optional[CoinDatabase] = None


def get_coin_database(db_path: str = "data/coins.json") -> CoinDatabase:
    """Get or create CoinDatabase singleton"""
    global _coin_database
    if _coin_database is None:
        _coin_database = CoinDatabase(db_path)
    return _coin_database
