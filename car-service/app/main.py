"""Main application module for car-service."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.config import settings
from app.endpoints import cars

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for application startup and shutdown.

    Args:
        app: FastAPI application instance
    """
    # Startup
    logger.info(f"Starting {settings.service_name} on port {settings.service_port}")
    logger.info("In-memory storage initialized")
    yield
    # Shutdown
    logger.info(f"Shutting down {settings.service_name}")


# Create FastAPI application
app = FastAPI(
    title="Car Service API",
    description="Microservice for managing car information and documents",
    version="1.0.0",
    lifespan=lifespan
)

from prometheus_fastapi_instrumentator import Instrumentator
Instrumentator().instrument(app).expose(app)

# Include routers
app.include_router(cars.router, prefix=settings.api_prefix)


@app.get("/health", tags=["health"])
async def health_check():
    """
    Health check endpoint.

    Returns:
        JSON response with service status
    """
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "service": settings.service_name,
            "version": "1.0.0"
        }
    )


@app.get("/", tags=["root"])
async def root():
    """
    Root endpoint.

    Returns:
        JSON response with service information
    """
    return JSONResponse(
        status_code=200,
        content={
            "service": settings.service_name,
            "version": "1.0.0",
            "api_prefix": settings.api_prefix,
            "docs": "/docs"
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.service_port,
        reload=True
    )
