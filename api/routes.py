"""
API Routes
REST API endpoints untuk Rabit Mobile
"""
from fastapi import APIRouter, File, HTTPException, Query, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from typing import Optional, List
import logging
import asyncio
import json
from datetime import datetime

from agents.core import TradingAgent
from agents.conversation_style import normalize_conversation_style
from agents.memory import Mem0DisabledError, Mem0RequestError, get_mem0_client
from agents.trading_style import normalize_trading_style
from agents.tools_registry import register_trading_tools
from agents.uploads import UploadValidationError, get_upload_manager
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
    ModelToggleRequest,
    AgentUploadResponse,
    AgentUploadDeleteResponse,
    AgentChatRequest,
    AgentChatResponse,
    MemoryCreateRequest,
    MemoryCreateResponse,
    MemoryDeleteResponse,
    MemoryHealthResponse,
    MemoryListResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")
_agent_tools_registered = False


def get_agent(scope_id: Optional[str] = None, user_id: Optional[str] = None) -> TradingAgent:
    """Create a trading agent with tools registered once."""
    global _agent_tools_registered
    if not _agent_tools_registered:
        register_trading_tools()
        _agent_tools_registered = True
    return TradingAgent(scope_id=scope_id, user_id=user_id)


def _raise_mem0_http_error(exc: Exception) -> None:
    """Translate Mem0 client errors into HTTP responses."""
    if isinstance(exc, Mem0DisabledError):
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    if isinstance(exc, Mem0RequestError):
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    raise HTTPException(status_code=500, detail=str(exc)) from exc


def _format_sse(event_name: str, payload: dict) -> str:
    """Format an SSE event payload."""
    return f"event: {event_name}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"


def _serialize_agent_intent(agent) -> Optional[dict]:
    """Safely serialize the agent's last routed intent for API responses."""
    intent = getattr(agent, "last_intent", None)
    if intent is None:
        return None
    if hasattr(intent, "model_dump"):
        return intent.model_dump()
    if isinstance(intent, dict):
        return intent
    return None


def _serialize_conversation_style(style: Optional[str]) -> str:
    """Normalize style values before returning them to clients."""
    return normalize_conversation_style(style)


def _serialize_trading_style(style: Optional[str]) -> str:
    """Normalize trading style values before returning them to clients."""
    return normalize_trading_style(style)


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
# Agent Endpoints
# ============================================================================

@router.get(
    "/memory/health",
    response_model=MemoryHealthResponse,
    summary="Check Mem0 health",
    tags=["Memory"],
)
async def get_memory_health():
    """Return whether Mem0 is enabled and reachable."""
    client = get_mem0_client()

    if not client.enabled:
        return MemoryHealthResponse(
            enabled=False,
            healthy=False,
            base_url=client.base_url,
            detail="Mem0 is disabled",
        )

    try:
        await client.health_check()
        return MemoryHealthResponse(
            enabled=True,
            healthy=True,
            base_url=client.base_url,
            detail=None,
        )
    except Exception as exc:
        return MemoryHealthResponse(
            enabled=True,
            healthy=False,
            base_url=client.base_url,
            detail=str(exc),
        )


@router.get(
    "/memory/search",
    response_model=MemoryListResponse,
    summary="Search user memories",
    tags=["Memory"],
)
async def search_memory(
    user_id: str = Query(..., description="User ID"),
    query: str = Query(..., description="Semantic search query"),
    limit: int = Query(5, description="Maximum number of memories"),
):
    """Search Mem0 memories for one user."""
    try:
        memories = await get_mem0_client().search_memories(user_id=user_id, query=query, limit=limit)
        return MemoryListResponse(user_id=user_id, memories=memories, total=len(memories), query=query)
    except Exception as exc:
        _raise_mem0_http_error(exc)


@router.get(
    "/memory",
    response_model=MemoryListResponse,
    summary="List user memories",
    tags=["Memory"],
)
async def list_memory(user_id: str = Query(..., description="User ID")):
    """List all stored memories for one user."""
    try:
        memories = await get_mem0_client().get_all_memories(user_id=user_id)
        return MemoryListResponse(user_id=user_id, memories=memories, total=len(memories))
    except Exception as exc:
        _raise_mem0_http_error(exc)


@router.post(
    "/memory",
    response_model=MemoryCreateResponse,
    summary="Create a user memory",
    tags=["Memory"],
)
async def create_memory(request: MemoryCreateRequest):
    """Create a Mem0 memory through the backend API."""
    try:
        data = await get_mem0_client().add_memory(
            user_id=request.user_id,
            text=request.text,
            metadata=request.metadata,
        )
        return MemoryCreateResponse(success=True, user_id=request.user_id, data=data)
    except Exception as exc:
        _raise_mem0_http_error(exc)


@router.delete(
    "/memory/{memory_id}",
    response_model=MemoryDeleteResponse,
    summary="Delete one user memory",
    tags=["Memory"],
)
async def delete_memory(
    memory_id: str,
    user_id: str = Query(..., description="User ID"),
):
    """Delete one Mem0 memory by ID."""
    try:
        await get_mem0_client().delete_memory(user_id=user_id, memory_id=memory_id)
        return MemoryDeleteResponse(success=True, user_id=user_id, memory_id=memory_id)
    except Exception as exc:
        _raise_mem0_http_error(exc)


@router.delete(
    "/memory",
    response_model=MemoryDeleteResponse,
    summary="Delete all user memories",
    tags=["Memory"],
)
async def delete_all_memory(user_id: str = Query(..., description="User ID")):
    """Delete all Mem0 memories for one user."""
    try:
        await get_mem0_client().delete_all_memories(user_id=user_id)
        return MemoryDeleteResponse(success=True, user_id=user_id, deleted_all=True)
    except Exception as exc:
        _raise_mem0_http_error(exc)


@router.post(
    "/agent/uploads",
    response_model=AgentUploadResponse,
    summary="Upload temporary agent attachment",
    tags=["Agent"],
)
async def upload_agent_attachment(file: UploadFile = File(...)):
    """Upload a temporary image or PDF for agent multimodal input."""
    manager = get_upload_manager()

    try:
        record = await manager.save_upload(file)
        return AgentUploadResponse(
            file_id=record.file_id,
            filename=record.original_filename,
            content_type=record.content_type,
            kind=record.kind,
            size_bytes=record.size_bytes,
            expires_at=record.expires_at,
        )
    except UploadValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.error(f"Error uploading agent attachment: {exc}")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.delete(
    "/agent/uploads/{file_id}",
    response_model=AgentUploadDeleteResponse,
    summary="Delete temporary agent attachment",
    tags=["Agent"],
)
async def delete_agent_attachment(file_id: str):
    """Delete a temporary uploaded attachment."""
    deleted = get_upload_manager().delete(file_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Attachment '{file_id}' not found")

    return AgentUploadDeleteResponse(success=True, file_id=file_id)


@router.post(
    "/agent/chat",
    response_model=AgentChatResponse,
    summary="Chat with Rabit agent using temporary multimodal uploads",
    tags=["Agent"],
)
async def chat_with_agent(request: AgentChatRequest):
    """Chat with the Rabit agent using optional uploaded image/PDF attachments."""
    upload_manager = get_upload_manager()

    try:
        attachments = upload_manager.resolve_attachments(request.attachment_ids)
        agent = get_agent(scope_id=request.scope_id, user_id=request.user_id)
        response = await agent.process_trading_query(
            request.message,
            attachments=attachments,
            conversation_style=request.conversation_style,
            trading_style=request.trading_style,
        )

        return AgentChatResponse(
            response=response,
            scope_id=request.scope_id,
            user_id=request.user_id,
            conversation_style=_serialize_conversation_style(agent.last_conversation_style),
            trading_style=_serialize_trading_style(agent.last_trading_style),
            attachment_ids=request.attachment_ids,
            intent=_serialize_agent_intent(agent),
        )
    except UploadValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.error(f"Error in agent chat endpoint: {exc}")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post(
    "/agent/chat/stream",
    summary="Stream Rabit agent chat events over SSE",
    tags=["Agent"],
)
async def stream_chat_with_agent(request: AgentChatRequest):
    """Stream agent output, thinking summary, plan, hint, and error events over SSE."""

    async def event_generator():
        queue: asyncio.Queue[Optional[str]] = asyncio.Queue()

        async def emit(event_name: str, payload: dict):
            await queue.put(_format_sse(event_name, payload))

        async def run_agent():
            agent = None
            try:
                upload_manager = get_upload_manager()
                attachments = upload_manager.resolve_attachments(request.attachment_ids)
                agent = get_agent(scope_id=request.scope_id, user_id=request.user_id)

                response = await agent.process_stream(
                    request.message,
                    event_emitter=emit,
                    use_tools=True,
                    attachments=attachments,
                    conversation_style=request.conversation_style,
                    trading_style=request.trading_style,
                )

                await emit(
                    "done",
                    {
                        "type": "done",
                        "status": "completed",
                        "response": response,
                        "scope_id": request.scope_id,
                        "user_id": request.user_id,
                        "conversation_style": _serialize_conversation_style(
                            getattr(agent, "last_conversation_style", request.conversation_style)
                        ),
                        "trading_style": _serialize_trading_style(
                            getattr(agent, "last_trading_style", request.trading_style)
                        ),
                        "attachment_ids": request.attachment_ids,
                        "intent": _serialize_agent_intent(agent),
                    },
                )
            except UploadValidationError as exc:
                await emit(
                    "error",
                    {
                        "type": "error",
                        "source": "request",
                        "message": str(exc),
                        "details": {},
                    },
                )
                await emit(
                    "done",
                    {
                        "type": "done",
                        "status": "failed",
                        "conversation_style": _serialize_conversation_style(
                            getattr(agent, "last_conversation_style", request.conversation_style)
                        ),
                        "trading_style": _serialize_trading_style(
                            getattr(agent, "last_trading_style", request.trading_style)
                        ),
                        "intent": _serialize_agent_intent(agent),
                    },
                )
            except Exception as exc:
                logger.error(f"Error in streaming agent chat endpoint: {exc}")
                await emit(
                    "error",
                    {
                        "type": "error",
                        "source": "agent",
                        "message": str(exc),
                        "details": {
                            "error_type": type(exc).__name__,
                        },
                    },
                )
                await emit(
                    "done",
                    {
                        "type": "done",
                        "status": "failed",
                        "conversation_style": _serialize_conversation_style(
                            getattr(agent, "last_conversation_style", request.conversation_style)
                        ),
                        "trading_style": _serialize_trading_style(
                            getattr(agent, "last_trading_style", request.trading_style)
                        ),
                        "intent": _serialize_agent_intent(agent),
                    },
                )
            finally:
                await queue.put(None)

        task = asyncio.create_task(run_agent())
        try:
            while True:
                item = await queue.get()
                if item is None:
                    break
                yield item
        finally:
            if not task.done():
                task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await task

    import contextlib

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


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
