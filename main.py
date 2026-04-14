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

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


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
    
    # Start Drift WS (optional - uncomment when ready)
    # logger.info("Starting Drift WebSocket...")
    # handler = MarketDataHandler()
    # drift_client = DriftWSClient(handler)
    # asyncio.create_task(drift_client.connect())
    
    logger.info("Rabit Backend started successfully!")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Rabit Backend...")
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
