"""
API Response Models
Pydantic models untuk API responses
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class AssetListItem(BaseModel):
    """Asset item in list"""
    symbol: str = Field(..., description="Asset symbol (e.g., 'BTC')")
    name: str = Field(..., description="Asset name (e.g., 'Bitcoin')")
    price: float = Field(..., description="Current price")
    change_24h: Optional[float] = Field(None, description="24h price change percentage")
    categories: List[str] = Field(default_factory=list, description="Asset categories")


class AssetListResponse(BaseModel):
    """Response for GET /api/assets"""
    assets: List[AssetListItem]
    total: int = Field(..., description="Total number of assets")


class AssetLinks(BaseModel):
    """Asset links"""
    website: Optional[str] = None
    twitter: Optional[str] = None
    telegram: Optional[str] = None
    github: Optional[str] = None
    explorer: Optional[str] = None
    contract_address: Optional[str] = None


class AssetDetailResponse(BaseModel):
    """Response for GET /api/assets/{symbol}"""
    # Basic info
    symbol: str
    name: str
    
    # Price data
    price: float
    change_24h: Optional[float] = None
    volume_24h: Optional[float] = None
    high_24h: Optional[float] = None
    low_24h: Optional[float] = None
    
    # Market data (futures)
    market_cap: Optional[float] = None
    fdv: Optional[float] = None
    open_interest: Optional[float] = None
    funding_rate: Optional[float] = None
    
    # Static info
    description: Optional[str] = None
    categories: List[str] = Field(default_factory=list)
    links: AssetLinks
    
    # Metadata
    last_updated: str


class OHLCData(BaseModel):
    """OHLC candle data"""
    timestamp: int = Field(..., description="Unix timestamp in milliseconds")
    open: float
    high: float
    low: float
    close: float
    volume: float


class OHLCResponse(BaseModel):
    """Response for GET /api/assets/{symbol}/ohlc"""
    symbol: str
    interval: str
    data: List[OHLCData]


class ErrorResponse(BaseModel):
    """Error response"""
    detail: str = Field(..., description="Error message")



class ModelInfoResponse(BaseModel):
    """OpenRouter model information"""
    id: str
    name: str
    provider: str
    description: Optional[str] = None
    context_length: int
    input_price: float = Field(..., description="Input price per 1M tokens (USD)")
    output_price: float = Field(..., description="Output price per 1M tokens (USD)")
    supports_tools: bool
    supports_reasoning: bool
    knowledge_cutoff: Optional[str] = None
    created: Optional[int] = None
    modality: Optional[str] = None
    tokenizer: Optional[str] = None
    enabled: bool


class ModelsListResponse(BaseModel):
    """Response for GET /api/models"""
    models: List[ModelInfoResponse]
    total: int
    enabled: int
    disabled: int
    last_updated: Optional[str] = None


class ModelStatsResponse(BaseModel):
    """Model statistics"""
    total_models: int
    enabled_models: int
    disabled_models: int
    models_with_tools: int
    models_with_reasoning: int
    providers: Dict[str, Dict[str, int]] = Field(default_factory=dict, description="Statistics grouped by provider")
    last_updated: Optional[str] = None


class ModelToggleRequest(BaseModel):
    """Request to enable/disable model"""
    model_id: str
    enabled: bool
