"""Market data models for WebSocket"""
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import datetime


class PriceUpdate(BaseModel):
    """Real-time price update from Drift (Futures data)"""
    symbol: str
    price: float
    change_24h: Optional[float] = None
    volume_24h: Optional[float] = None
    open_interest: Optional[float] = None
    funding_rate: Optional[float] = None
    
    # Additional market data
    market_cap: Optional[float] = None
    fdv: Optional[float] = None
    high_24h: Optional[float] = None
    low_24h: Optional[float] = None
    
    timestamp: datetime = Field(default_factory=datetime.now)


class OHLCData(BaseModel):
    """OHLC data for charting"""
    symbol: str
    timestamp: int  # Unix timestamp in milliseconds
    open: float
    high: float
    low: float
    close: float
    volume: float
    quote_asset_volume: Optional[float] = None
    number_of_trades: Optional[int] = None
    taker_buy_base_asset_volume: Optional[float] = None
    taker_buy_quote_asset_volume: Optional[float] = None


class MarketData(BaseModel):
    """Combined market data"""
    model_config = ConfigDict(from_attributes=True)

    symbol: str
    
    # Price data
    price: float
    change_24h: Optional[float] = None
    volume_24h: Optional[float] = None
    open_interest: Optional[float] = None
    funding_rate: Optional[float] = None
    
    # OHLC data
    ohlc: Optional[OHLCData] = None
    
    # Metadata
    source: str  # "drift" or "binance"
    timestamp: datetime = Field(default_factory=datetime.now)
