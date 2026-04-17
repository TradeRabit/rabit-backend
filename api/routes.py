"""
API Routes
REST API endpoints untuk Rabit Mobile
"""
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Query
from typing import Optional, List
import logging
from datetime import datetime

from config.settings import settings
from ws.services import get_market_service
from ws.handlers import MarketDataHandler
from ws.binance import BinanceHistoryDownloader
from api.models import (
    AssetListResponse,
    AssetDetailResponse,
    OHLCResponse,
    ErrorResponse,
    ModelsListResponse,
    ModelInfoResponse,
    ModelStatsResponse,
    ModelToggleRequest
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")


# ============================================================================
# Assets Endpoints
# ============================================================================

@router.get(
    "/assets",
    response_model=AssetListResponse,
    summary="Get list of assets",
    description="Get list of all available assets with price data",
    tags=["Assets"]
)
async def get_assets(
    category: Optional[str] = Query(None, description="Filter by category (e.g., 'DeFi', 'Stablecoin')"),
    limit: Optional[int] = Query(50, description="Maximum number of assets to return")
):
    """
    Get list of assets with basic price information.
    
    **Parameters:**
    - `category` (optional): Filter by category
    - `limit` (optional): Maximum number of results (default: 50)
    
    **Returns:**
    - List of assets with symbol, name, price, and 24h change
    """
    try:
        from main import market_handler
        
        service = get_market_service()
        
        # Get all symbols from TRADING_ASSETS config
        symbols = settings.TRADING_ASSETS
        
        assets = []
        for symbol in symbols[:limit]:
            try:
                # Get coin info
                coin_info = await service.get_coin_info(symbol)
                
                # Get price data
                price_update = market_handler.get_price(symbol)
                
                if coin_info and price_update:
                    # Filter by category if provided
                    if category:
                        if not coin_info.categories or category not in coin_info.categories:
                            continue
                    
                    assets.append({
                        "symbol": symbol,
                        "name": coin_info.name,
                        "price": price_update.price,
                        "change_24h": price_update.change_24h,
                        "categories": coin_info.categories
                    })
            except Exception as e:
                logger.error(f"Error fetching data for {symbol}: {e}")
                continue
        
        return {"assets": assets, "total": len(assets)}
        
    except Exception as e:
        logger.error(f"Error in get_assets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/assets/{symbol}",
    response_model=AssetDetailResponse,
    summary="Get asset detail",
    description="Get detailed information for a specific asset",
    tags=["Assets"]
)
async def get_asset_detail(symbol: str):
    """
    Get detailed information for a specific asset.
    
    **Parameters:**
    - `symbol`: Asset symbol (e.g., 'BTC', 'ETH', 'SOL')
    
    **Returns:**
    - Complete asset information including price, stats, description, and links
    """
    try:
        from main import market_handler
        
        service = get_market_service()
        
        symbol = symbol.upper()
        
        # Get coin info
        coin_info = await service.get_coin_info(symbol)
        if not coin_info:
            raise HTTPException(
                status_code=404,
                detail=f"Asset '{symbol}' not found"
            )
        
        # Get price data
        price_update = market_handler.get_price(symbol)
        if not price_update:
            raise HTTPException(
                status_code=404,
                detail=f"Price data for '{symbol}' not available"
            )
        
        # Get contract address (first one if multiple chains)
        contract_address = None
        if coin_info.contract_address:
            contract_address = list(coin_info.contract_address.values())[0]
        
        return {
            "symbol": symbol,
            "name": coin_info.name,
            "price": price_update.price,
            "change_24h": price_update.change_24h,
            "volume_24h": price_update.volume_24h,
            "high_24h": price_update.high_24h,
            "low_24h": price_update.low_24h,
            "market_cap": price_update.market_cap,
            "fdv": price_update.fdv,
            "open_interest": price_update.open_interest,
            "funding_rate": price_update.funding_rate,
            "description": coin_info.description,
            "categories": coin_info.categories,
            "links": {
                "website": coin_info.links.website if coin_info.links else None,
                "twitter": coin_info.links.twitter if coin_info.links else None,
                "telegram": coin_info.links.telegram if coin_info.links else None,
                "github": coin_info.links.github if coin_info.links else None,
                "explorer": coin_info.links.explorer if coin_info.links else None,
                "contract_address": contract_address
            },
            "last_updated": price_update.timestamp.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_asset_detail: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# OHLC Data Endpoint
# ============================================================================

@router.get(
    "/assets/{symbol}/ohlc",
    response_model=OHLCResponse,
    summary="Get OHLC data",
    description="Get OHLC (candlestick) data for charting",
    tags=["Chart Data"]
)
async def get_ohlc_data(
    symbol: str,
    interval: str = Query("1h", description="Interval (1m, 5m, 15m, 1h, 4h, 1d)"),
    limit: int = Query(100, description="Number of candles to return"),
    source: str = Query("auto", description="Data source: 'backpack', 'binance', or 'auto'")
):
    """
    Get OHLC data for TradingView chart.
    
    **Parameters:**
    - `symbol`: Asset symbol (e.g., 'BTC', 'ETH')
    - `interval`: Candle interval (1m, 5m, 15m, 1h, 4h, 1d)
    - `limit`: Number of candles (default: 100, max: 1000)
    - `source`: Data source ('backpack', 'binance', or 'auto')
    
    **Returns:**
    - OHLC data array for charting
    """
    try:
        # Validate interval
        valid_intervals = ["1m", "5m", "15m", "1h", "4h", "1d"]
        if interval not in valid_intervals:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid interval. Must be one of: {', '.join(valid_intervals)}"
            )
        
        # Validate limit
        if limit > 1000:
            limit = 1000
        
        symbol = symbol.upper()
        ohlc_data = []
        
        # Determine source
        if source == "auto":
            source = "backpack" if settings.uses_price_source("backpack") else "binance"

        # Try to get from WebSocket handler first (real-time data)
        if source in {"backpack", "both"} and settings.uses_price_source("backpack"):
            from main import market_handler
            ohlc_data = market_handler.get_ohlc(symbol, interval=interval, limit=limit)
            
            # If not enough data from WebSocket, fallback to Binance
            if len(ohlc_data) < limit:
                logger.info(f"Not enough OHLC data from Backpack, falling back to Binance")
                source = "binance"
        
        # Get from Binance if needed
        if not ohlc_data or source == "binance":
            downloader = BinanceHistoryDownloader()
            binance_data = await downloader.download_history(
                symbol=symbol,
                interval=interval,
                limit=limit
            )
            
            if not binance_data:
                raise HTTPException(
                    status_code=404,
                    detail=f"OHLC data for '{symbol}' not available"
                )
            
            ohlc_data = binance_data
        
        return {
            "symbol": symbol,
            "interval": interval,
            "data": ohlc_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_ohlc_data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# WebSocket Endpoint
# ============================================================================

class ConnectionManager:
    """Manage WebSocket connections"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to client: {e}")


manager = ConnectionManager()


@router.websocket("/ws/prices")
async def websocket_prices(websocket: WebSocket):
    """
    WebSocket endpoint for real-time price updates.
    
    **Usage:**
    ```javascript
    const ws = new WebSocket('ws://localhost:8000/api/ws/prices');
    
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log(data);
    };
    ```
    
    **Message Format:**
    ```json
    {
        "symbol": "BTC",
        "price": 65230.12,
        "change_24h": 2.45,
        "timestamp": "2024-01-01T00:00:00Z"
    }
    ```
    """
    await manager.connect(websocket)
    
    from main import market_handler
    
    # Subscribe to all price updates
    async def on_price_update(price_update):
        """Callback for price updates"""
        try:
            await manager.broadcast({
                "symbol": price_update.symbol,
                "price": price_update.price,
                "change_24h": price_update.change_24h,
                "volume_24h": price_update.volume_24h,
                "timestamp": price_update.timestamp.isoformat()
            })
        except Exception as e:
            logger.error(f"Error in price update callback: {e}")
    
    # Subscribe to price updates
    market_handler.subscribe("price:*", on_price_update)
    
    try:
        while True:
            # Keep connection alive and handle client messages
            data = await websocket.receive_text()
            
            # Handle ping/pong
            if data == "ping":
                await websocket.send_text("pong")
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("Client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


# ============================================================================
# Health Check
# ============================================================================

@router.get(
    "/health",
    summary="Health check",
    description="Check API health status",
    tags=["System"]
)
async def health_check():
    """
    Health check endpoint.
    
    **Returns:**
    - API status and version
    """
    return {
        "status": "healthy",
        "version": "1.0.0",
        "service": "Rabit Backend API"
    }



# ============================================
# OpenRouter Models Endpoints
# ============================================

@router.get("/models", response_model=ModelsListResponse, tags=["Models"])
async def list_models(
    require_tools: bool = False,
    require_reasoning: bool = False,
    min_context: Optional[int] = None,
    max_input_price: Optional[float] = None,
    max_output_price: Optional[float] = None,
    provider: Optional[str] = None,
    enabled_only: bool = True,
    refresh: bool = False
):
    """
    List available OpenRouter models with filtering
    
    Query Parameters:
    - require_tools: Only models that support tool calling
    - require_reasoning: Only models that support reasoning
    - min_context: Minimum context length
    - max_input_price: Maximum input price per 1M tokens (USD)
    - max_output_price: Maximum output price per 1M tokens (USD)
    - provider: Filter by provider (e.g., 'anthropic', 'openai', 'google')
    - enabled_only: Only return enabled models (default: true)
    - refresh: Force refresh from OpenRouter API (default: false)
    """
    try:
        from agents.openrouter import get_openrouter_models
        
        models_manager = get_openrouter_models()
        
        # Fetch models (with cache)
        await models_manager.fetch_models(force_refresh=refresh)
        
        # Filter models
        filtered_models = models_manager.filter_models(
            require_tools=require_tools,
            require_reasoning=require_reasoning,
            min_context=min_context,
            max_input_price=max_input_price,
            max_output_price=max_output_price,
            provider=provider,
            enabled_only=enabled_only
        )
        
        # Get stats
        stats = models_manager.get_stats()
        
        return ModelsListResponse(
            models=[ModelInfoResponse(**m.model_dump()) for m in filtered_models],
            total=len(filtered_models),
            enabled=len([m for m in filtered_models if m.enabled]),
            disabled=len([m for m in filtered_models if not m.enabled]),
            last_updated=stats.get("last_updated")
        )
    
    except Exception as e:
        logger.error(f"Error listing models: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models/stats", response_model=ModelStatsResponse, tags=["Models"])
async def get_models_stats():
    """Get statistics about available models"""
    try:
        from agents.openrouter import get_openrouter_models
        
        models_manager = get_openrouter_models()
        
        # Fetch models (uses cache automatically)
        await models_manager.fetch_models()
        
        stats = models_manager.get_stats()
        
        return ModelStatsResponse(**stats)
    
    except Exception as e:
        logger.error(f"Error getting model stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models/{model_id:path}", response_model=ModelInfoResponse, tags=["Models"])
async def get_model_info(model_id: str):
    """Get information about a specific model"""
    try:
        from agents.openrouter import get_openrouter_models
        
        models_manager = get_openrouter_models()
        
        # Fetch models (uses cache automatically)
        await models_manager.fetch_models()
        
        model = models_manager.get_model(model_id)
        
        if not model:
            raise HTTPException(status_code=404, detail=f"Model '{model_id}' not found")
        
        return ModelInfoResponse(**model.model_dump())
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting model info: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/models/toggle", tags=["Models"])
async def toggle_model(request: ModelToggleRequest):
    """Enable or disable a model"""
    try:
        from agents.openrouter import get_openrouter_models
        
        models_manager = get_openrouter_models()
        
        # Fetch models (uses cache automatically)
        await models_manager.fetch_models()
        
        model = models_manager.get_model(request.model_id)
        
        if not model:
            raise HTTPException(status_code=404, detail=f"Model '{request.model_id}' not found")
        
        if request.enabled:
            models_manager.enable_model(request.model_id)
        else:
            models_manager.disable_model(request.model_id)
        
        return {
            "success": True,
            "model_id": request.model_id,
            "enabled": request.enabled,
            "message": f"Model {'enabled' if request.enabled else 'disabled'} successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error toggling model: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))



@router.get("/models/providers", tags=["Models"])
async def list_providers():
    """Get list of all providers"""
    try:
        from agents.openrouter import get_openrouter_models
        
        models_manager = get_openrouter_models()
        
        # Fetch models (uses cache automatically)
        await models_manager.fetch_models()
        
        providers = models_manager.get_providers()
        
        return {
            "providers": providers,
            "total": len(providers)
        }
    
    except Exception as e:
        logger.error(f"Error listing providers: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models/grouped", tags=["Models"])
async def get_models_grouped(
    enabled_only: bool = True,
    require_tools: bool = False,
    require_reasoning: bool = False
):
    """
    Get models grouped by provider
    
    Query Parameters:
    - enabled_only: Only include enabled models (default: true)
    - require_tools: Only models with tool calling support
    - require_reasoning: Only models with reasoning support
    """
    try:
        from agents.openrouter import get_openrouter_models
        
        models_manager = get_openrouter_models()
        
        # Fetch models (uses cache automatically)
        await models_manager.fetch_models()
        
        # Filter first if needed
        if require_tools or require_reasoning:
            filtered = models_manager.filter_models(
                require_tools=require_tools,
                require_reasoning=require_reasoning,
                enabled_only=enabled_only
            )
            # Manually group filtered models
            grouped = {}
            for model in filtered:
                provider = model.provider
                if provider not in grouped:
                    grouped[provider] = []
                grouped[provider].append(ModelInfoResponse(**model.model_dump()))
            grouped = dict(sorted(grouped.items()))
        else:
            # Use built-in grouping
            grouped_models = models_manager.get_models_by_provider(enabled_only=enabled_only)
            grouped = {
                provider: [ModelInfoResponse(**m.model_dump()) for m in models]
                for provider, models in grouped_models.items()
            }
        
        # Calculate stats per provider
        provider_stats = {}
        for provider, models in grouped.items():
            provider_stats[provider] = {
                "total": len(models),
                "with_tools": len([m for m in models if m.supports_tools]),
                "with_reasoning": len([m for m in models if m.supports_reasoning])
            }
        
        return {
            "grouped": grouped,
            "provider_stats": provider_stats,
            "total_providers": len(grouped)
        }
    
    except Exception as e:
        logger.error(f"Error grouping models: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))



@router.get("/models/database/stats", tags=["Models"])
async def get_database_stats():
    """Get database statistics"""
    try:
        from agents.openrouter import get_models_database
        
        db = get_models_database()
        stats = db.get_stats()
        
        return stats
    
    except Exception as e:
        logger.error(f"Error getting database stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/models/database/refresh", tags=["Models"])
async def refresh_database():
    """Force refresh database from OpenRouter API"""
    try:
        from agents.openrouter import get_openrouter_models
        
        models_manager = get_openrouter_models()
        
        # Force refresh from API
        models = await models_manager.fetch_models(force_refresh=True)
        
        return {
            "success": True,
            "message": "Database refreshed successfully",
            "total_models": len(models),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error refreshing database: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/models/database/clear", tags=["Models"])
async def clear_database():
    """Clear all models from database (will be refetched on next request)"""
    try:
        from agents.openrouter import get_models_database
        
        db = get_models_database()
        db.clear()
        
        return {
            "success": True,
            "message": "Database cleared successfully"
        }
    
    except Exception as e:
        logger.error(f"Error clearing database: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
