"""
Rabit Backend - Main Application
FastAPI application dengan WebSocket support
"""
import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config.settings import settings
from api.routes import router
from ws.services import get_market_service
from ws.handlers import MarketDataHandler

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Global handler instance
market_handler = MarketDataHandler()


# ============================================================================
# Lifespan Events
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan events for startup and shutdown
    """
    # Startup
    logger.info("Starting Rabit Backend...")
    
    # Initialize coin info database
    logger.info("Initializing coin info database...")
    service = get_market_service()
    
    # Initialize coins (fetch from CoinGecko if needed)
    # Use TRADING_ASSETS from config
    symbols = settings.TRADING_ASSETS
    
    try:
        await service.initialize_coins(symbols)
        logger.info(f"Initialized {len(symbols)} coins")
    except Exception as e:
        logger.error(f"Error initializing coins: {e}")
    
    # Start WebSocket service based on PRICE_SOURCE setting
    price_source = settings.PRICE_SOURCE.lower()
    logger.info(f"Price source: {price_source}")
    
    if price_source == "backpack" and settings.BACKPACK_ENABLED:
        logger.info("Starting Backpack WebSocket service...")
        try:
            from ws.backpack import get_backpack_service
            backpack_service = get_backpack_service()
            await backpack_service.start(market_handler)
            logger.info("Backpack WebSocket service started")
        except Exception as e:
            logger.error(f"Failed to start Backpack service: {e}")
    
    elif price_source == "drift":
        logger.info("Starting Drift WebSocket service...")
        try:
            from ws.drift import DriftWSClient
            drift_client = DriftWSClient()
            await drift_client.connect()
            
            # Subscribe to assets
            for symbol in settings.DRIFT_ASSETS[:settings.DRIFT_SUBSCRIBE_ASSETS]:
                await drift_client.subscribe(symbol, market_handler.on_price_update)
            
            logger.info("Drift WebSocket service started")
        except Exception as e:
            logger.error(f"Failed to start Drift service: {e}")
    
    else:
        logger.warning(f"Unknown price source: {price_source}")
    
    logger.info("Rabit Backend started successfully!")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Rabit Backend...")
    
    # Stop WebSocket services
    if price_source == "backpack":
        try:
            from ws.backpack import get_backpack_service
            backpack_service = get_backpack_service()
            await backpack_service.stop()
        except Exception as e:
            logger.error(f"Error stopping Backpack service: {e}")
    
    logger.info("Rabit Backend stopped")


# ============================================================================
# FastAPI App
# ============================================================================

app = FastAPI(
    title="Rabit Backend API",
    description="Backend API untuk Rabit Mobile App dengan real-time price updates",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update with specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router)


# ============================================================================
# Root Endpoint
# ============================================================================

@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint - API information
    """
    return {
        "name": "Rabit Backend API",
        "version": "1.0.0",
        "description": "Backend API untuk Rabit Mobile App",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/api/health"
    }


# ============================================================================
# Error Handlers
# ============================================================================

@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"detail": "Endpoint not found"}
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


# ============================================================================
# Run Application
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
