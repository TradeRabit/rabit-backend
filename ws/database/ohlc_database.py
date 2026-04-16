"""
OHLC Database for storing historical candlestick data
Stores OHLC data from multiple exchanges (Binance, Backpack, Drift)
"""
import json
import os
from typing import Optional, List, Dict
from datetime import datetime
from pathlib import Path
import logging

from ws.models import OHLCData

logger = logging.getLogger(__name__)


class OHLCDatabase:
    """
    JSON-based database for OHLC data persistence
    Stores candlestick data per symbol, exchange, and interval
    
    Structure:
    {
        "BTC": {
            "binance": {
                "1h": [OHLCData, ...],
                "4h": [OHLCData, ...],
                "1d": [OHLCData, ...]
            },
            "backpack": {
                "1h": [OHLCData, ...]
            },
            "drift": {
                "1h": [OHLCData, ...]
            }
        }
    }
    """
    
    def __init__(self, db_path: str = "data/ohlc_history.json"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.data: Dict[str, Dict[str, Dict[str, List[dict]]]] = {}
        self.max_candles_per_interval = 10000  # Limit storage per interval
        self.load()
        
    def load(self):
        """Load database from file"""
        if self.db_path.exists():
            try:
                with open(self.db_path, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
                
                # Count total candles
                total_candles = sum(
                    len(candles)
                    for symbol_data in self.data.values()
                    for exchange_data in symbol_data.values()
                    for candles in exchange_data.values()
                )
                
                logger.info(f"Loaded OHLC database: {len(self.data)} symbols, {total_candles} candles")
            except Exception as e:
                logger.error(f"Error loading OHLC database: {e}")
                self.data = {}
        else:
            logger.info("OHLC database file not found, starting fresh")
            self.data = {}
    
    def save(self):
        """Save database to file"""
        try:
            with open(self.db_path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False, default=str)
            logger.debug("Saved OHLC database")
        except Exception as e:
            logger.error(f"Error saving OHLC database: {e}")
    
    def save_candles(
        self,
        symbol: str,
        exchange: str,
        interval: str,
        candles: List[OHLCData],
        merge: bool = True
    ):
        """
        Save OHLC candles to database
        
        Args:
            symbol: Trading symbol (e.g., 'BTC', 'SOL')
            exchange: Exchange name ('binance', 'backpack', 'drift')
            interval: Candle interval (e.g., '1m', '5m', '1h', '1d')
            candles: List of OHLCData objects
            merge: If True, merge with existing data and remove duplicates
        """
        try:
            symbol = symbol.upper()
            exchange = exchange.lower()
            
            # Initialize nested structure if needed
            if symbol not in self.data:
                self.data[symbol] = {}
            if exchange not in self.data[symbol]:
                self.data[symbol][exchange] = {}
            if interval not in self.data[symbol][exchange]:
                self.data[symbol][exchange][interval] = []
            
            # Convert OHLCData to dict
            new_candles = [candle.model_dump(mode='json') for candle in candles]
            
            if merge:
                # Merge with existing data
                existing = self.data[symbol][exchange][interval]
                
                # Create a dict with timestamp as key to remove duplicates
                candle_dict = {c['timestamp']: c for c in existing}
                candle_dict.update({c['timestamp']: c for c in new_candles})
                
                # Sort by timestamp
                merged = sorted(candle_dict.values(), key=lambda x: x['timestamp'])
                
                # Limit to max candles
                if len(merged) > self.max_candles_per_interval:
                    merged = merged[-self.max_candles_per_interval:]
                
                self.data[symbol][exchange][interval] = merged
                logger.info(f"Merged {len(new_candles)} candles for {symbol} ({exchange}/{interval}), total: {len(merged)}")
            else:
                # Replace existing data
                self.data[symbol][exchange][interval] = new_candles
                logger.info(f"Saved {len(new_candles)} candles for {symbol} ({exchange}/{interval})")
            
            self.save()
            
        except Exception as e:
            logger.error(f"Error saving candles for {symbol} ({exchange}/{interval}): {e}")
    
    def get_candles(
        self,
        symbol: str,
        exchange: str,
        interval: str,
        limit: Optional[int] = None,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None
    ) -> List[OHLCData]:
        """
        Get OHLC candles from database
        
        Args:
            symbol: Trading symbol
            exchange: Exchange name
            interval: Candle interval
            limit: Maximum number of candles to return (most recent)
            start_time: Filter by start timestamp (milliseconds)
            end_time: Filter by end timestamp (milliseconds)
            
        Returns:
            List of OHLCData objects
        """
        try:
            symbol = symbol.upper()
            exchange = exchange.lower()
            
            if symbol not in self.data:
                return []
            if exchange not in self.data[symbol]:
                return []
            if interval not in self.data[symbol][exchange]:
                return []
            
            candles_data = self.data[symbol][exchange][interval]
            
            # Filter by time range
            if start_time or end_time:
                filtered = []
                for c in candles_data:
                    ts = c['timestamp']
                    if start_time and ts < start_time:
                        continue
                    if end_time and ts > end_time:
                        continue
                    filtered.append(c)
                candles_data = filtered
            
            # Apply limit (most recent)
            if limit and len(candles_data) > limit:
                candles_data = candles_data[-limit:]
            
            # Convert to OHLCData objects
            return [OHLCData(**c) for c in candles_data]
            
        except Exception as e:
            logger.error(f"Error getting candles for {symbol} ({exchange}/{interval}): {e}")
            return []
    
    def get_latest_candle(
        self,
        symbol: str,
        exchange: str,
        interval: str
    ) -> Optional[OHLCData]:
        """
        Get the most recent candle
        
        Args:
            symbol: Trading symbol
            exchange: Exchange name
            interval: Candle interval
            
        Returns:
            Latest OHLCData or None
        """
        candles = self.get_candles(symbol, exchange, interval, limit=1)
        return candles[0] if candles else None
    
    def get_available_symbols(self, exchange: Optional[str] = None) -> List[str]:
        """
        Get list of available symbols
        
        Args:
            exchange: Filter by exchange (optional)
            
        Returns:
            List of symbol names
        """
        if exchange:
            exchange = exchange.lower()
            return [
                symbol for symbol, exchanges in self.data.items()
                if exchange in exchanges
            ]
        return list(self.data.keys())
    
    def get_available_intervals(self, symbol: str, exchange: str) -> List[str]:
        """
        Get available intervals for a symbol/exchange
        
        Args:
            symbol: Trading symbol
            exchange: Exchange name
            
        Returns:
            List of interval strings
        """
        symbol = symbol.upper()
        exchange = exchange.lower()
        
        if symbol not in self.data:
            return []
        if exchange not in self.data[symbol]:
            return []
        
        return list(self.data[symbol][exchange].keys())
    
    def delete_candles(self, symbol: str, exchange: str, interval: str):
        """Delete candles for a specific symbol/exchange/interval"""
        try:
            symbol = symbol.upper()
            exchange = exchange.lower()
            
            if symbol in self.data:
                if exchange in self.data[symbol]:
                    if interval in self.data[symbol][exchange]:
                        del self.data[symbol][exchange][interval]
                        
                        # Clean up empty structures
                        if not self.data[symbol][exchange]:
                            del self.data[symbol][exchange]
                        if not self.data[symbol]:
                            del self.data[symbol]
                        
                        self.save()
                        logger.info(f"Deleted candles for {symbol} ({exchange}/{interval})")
        except Exception as e:
            logger.error(f"Error deleting candles: {e}")
    
    def clear_exchange(self, exchange: str):
        """Clear all data for a specific exchange"""
        exchange = exchange.lower()
        
        for symbol in list(self.data.keys()):
            if exchange in self.data[symbol]:
                del self.data[symbol][exchange]
                
                # Clean up empty symbols
                if not self.data[symbol]:
                    del self.data[symbol]
        
        self.save()
        logger.info(f"Cleared all data for exchange: {exchange}")
    
    def clear_all(self):
        """Clear all OHLC data"""
        self.data = {}
        self.save()
        logger.info("Cleared all OHLC data")
    
    def get_stats(self) -> Dict:
        """Get database statistics"""
        stats = {
            "total_symbols": len(self.data),
            "exchanges": {},
            "total_candles": 0,
            "database_path": str(self.db_path),
            "database_size_bytes": self.db_path.stat().st_size if self.db_path.exists() else 0
        }
        
        for symbol, exchanges in self.data.items():
            for exchange, intervals in exchanges.items():
                if exchange not in stats["exchanges"]:
                    stats["exchanges"][exchange] = {
                        "symbols": 0,
                        "intervals": {},
                        "total_candles": 0
                    }
                
                stats["exchanges"][exchange]["symbols"] += 1
                
                for interval, candles in intervals.items():
                    candle_count = len(candles)
                    
                    if interval not in stats["exchanges"][exchange]["intervals"]:
                        stats["exchanges"][exchange]["intervals"][interval] = 0
                    
                    stats["exchanges"][exchange]["intervals"][interval] += candle_count
                    stats["exchanges"][exchange]["total_candles"] += candle_count
                    stats["total_candles"] += candle_count
        
        return stats


# Singleton instance
_ohlc_database: Optional[OHLCDatabase] = None


def get_ohlc_database(db_path: str = "data/ohlc_history.json") -> OHLCDatabase:
    """Get or create OHLCDatabase singleton"""
    global _ohlc_database
    if _ohlc_database is None:
        _ohlc_database = OHLCDatabase(db_path)
    return _ohlc_database
