"""Market data models for WebSocket"""
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import datetime


class PriceUpdate(BaseModel):
    """Real-time price update from the active market feed."""
    symbol: str
    price: float
    change_24h: Optional[float] = None
    volume_24h: Optional[float] = None
    notional_volume_24h: Optional[float] = None
    base_volume_24h: Optional[float] = None
    open_interest: Optional[float] = None
    funding_rate: Optional[float] = None
    oracle_price: Optional[float] = None
    premium: Optional[float] = None
    
    # Additional market data
    market_cap: Optional[float] = None
    fdv: Optional[float] = None
    high_24h: Optional[float] = None
    low_24h: Optional[float] = None
    circulating_supply: Optional[float] = None
    total_supply: Optional[float] = None
    max_leverage: Optional[float] = None
    only_isolated: Optional[bool] = None
    market_pair: Optional[str] = None
    full_name: Optional[str] = None
    token_index: Optional[int] = None
    is_canonical: Optional[bool] = None
    source_exchange: Optional[str] = None
    
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
    notional_volume_24h: Optional[float] = None
    base_volume_24h: Optional[float] = None
    open_interest: Optional[float] = None
    funding_rate: Optional[float] = None
    oracle_price: Optional[float] = None
    premium: Optional[float] = None
    market_cap: Optional[float] = None
    fdv: Optional[float] = None
    circulating_supply: Optional[float] = None
    total_supply: Optional[float] = None
    max_leverage: Optional[float] = None
    only_isolated: Optional[bool] = None
    market_pair: Optional[str] = None
    full_name: Optional[str] = None
    token_index: Optional[int] = None
    is_canonical: Optional[bool] = None
    
    # OHLC data
    ohlc: Optional[OHLCData] = None
    
    # Metadata
    source: str  # e.g. "phantom_futures" or "phantom_spot"
    timestamp: datetime = Field(default_factory=datetime.now)
