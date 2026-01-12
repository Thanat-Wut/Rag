"""
WUT Backend - Main FastAPI Application
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from config import settings, validate_config
from models import HelpdeskRequest, HelpdeskResponse, HealthStatus, ErrorResponse
from brain.coordinator import Coordinator, get_coordinator
from connectors.way_api import close_way_client

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    # Startup
    validate_config()
    logger.info("✅ WUT Orchestrator Started")
    yield
    # Shutdown
    await close_way_client()
    logger.info("👋 WUT Orchestrator Stopped")


# Create FastAPI app
app = FastAPI(
    title="WUT Backend - Internal Helpdesk Orchestrator",
    description="Orchestrates queries between frontend and WAY RAG engine",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# Health Check Endpoints
# =============================================================================

@app.get("/health", response_model=HealthStatus, tags=["Health"])
async def health_check():
    """Check service health and WAY connection"""
    coordinator = get_coordinator()
    way_status = await coordinator.way_client.health_check()
    
    return HealthStatus(
        status="healthy" if way_status.get("status") == "connected" else "degraded",
        version="1.0.0",
        way_connection=way_status
    )


@app.get("/", tags=["Health"])
async def root():
    """Root endpoint"""
    return {
        "service": "WUT Backend",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


# =============================================================================
# Query Endpoints
# =============================================================================

@app.post("/api/query", response_model=HelpdeskResponse, tags=["Query"])
async def process_query(request: HelpdeskRequest):
    """
    Process a helpdesk query.
    
    Flow:
    1. Classify the query (department, signals)
    2. Call WAY API for RAG response
    3. Apply decision engine rules
    4. Return final response
    """
    try:
        coordinator = get_coordinator()
        response = await coordinator.process_query(request)
        return response
    except Exception as e:
        logger.error(f"Error processing query: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "ProcessingError",
                "message": str(e),
                "trace_id": request.trace_id
            }
        )


@app.post("/api/internal-helpdesk/query", response_model=HelpdeskResponse, tags=["Query"])
async def process_query_legacy(request: HelpdeskRequest):
    """Legacy endpoint for backward compatibility"""
    return await process_query(request)


# =============================================================================
# Debug Endpoints (only in debug mode)
# =============================================================================

if settings.DEBUG:
    @app.get("/debug/config", tags=["Debug"])
    async def debug_config():
        """Show current configuration (debug only)"""
        return {
            "WAY_API_URL": settings.WAY_API_URL,
            "WAY_TIMEOUT": settings.WAY_TIMEOUT,
            "USE_MOCK": settings.USE_MOCK,
            "CONFIDENCE_THRESHOLD": settings.CONFIDENCE_THRESHOLD,
            "LOG_LEVEL": settings.LOG_LEVEL
        }
