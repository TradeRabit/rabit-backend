"""
Coin Information Models
Data models untuk informasi coin dari CoinGecko yang disimpan di database
"""
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, Dict, List
from datetime import datetime


class CoinLinks(BaseModel):
    """Links untuk coin (website, social media, etc)"""
    website: Optional[str] = None
    twitter: Optional[str] = None
    telegram: Optional[str] = None
    discord: Optional[str] = None
    github: Optional[str] = None
    whitepaper: Optional[str] = None
    explorer: Optional[str] = None  # Block explorer (etherscan, etc)
    
    
class CoinInfo(BaseModel):
    """
    Informasi dasar coin dari CoinGecko
    Data ini disimpan permanen di database untuk menghindari rate limit
    Hanya untuk data yang jarang berubah (description, links, etc)
    """
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "bitcoin",
                "symbol": "BTC",
                "name": "Bitcoin",
                "description": "Bitcoin is the first decentralized cryptocurrency...",
                "links": {
                    "website": "https://bitcoin.org",
                    "twitter": "https://twitter.com/bitcoin",
                    "explorer": "https://blockchain.info"
                },
                "categories": ["Cryptocurrency", "Layer 1"],
                "last_updated": "2024-01-01T00:00:00Z"
            }
        }
    )

    # Identifiers
    id: str = Field(..., description="CoinGecko ID (e.g., 'bitcoin')")
    symbol: str = Field(..., description="Symbol (e.g., 'BTC')")
    name: str = Field(..., description="Full name (e.g., 'Bitcoin')")
    
    # Description (basic information)
    description: Optional[str] = Field(None, description="Coin description")
    
    # Links (basic information)
    links: Optional[CoinLinks] = Field(default_factory=CoinLinks, description="Social and web links")
    
    # Contract addresses (for tokens)
    contract_address: Optional[Dict[str, str]] = Field(
        default_factory=dict,
        description="Contract addresses by chain (e.g., {'ethereum': '0x...'})"
    )
    
    # Categories
    categories: List[str] = Field(default_factory=list, description="Categories (e.g., ['DeFi', 'Layer 1'])")
    
    # Metadata
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="Last update from CoinGecko")
    
