"""
Main FastAPI application entry point.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.endpoints import users
from app.database import engine, Base

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    """
    # Startup
    logger.info("Starting User Service...")
    logger.info(f"Service: {settings.APP_NAME} v{settings.APP_VERSION}")

    # Note: Alembic will handle migrations, so we don't create tables here
    # But we log the connection info
    logger.info("Database connection configured")

    yield

    # Shutdown
    logger.info("Shutting down User Service...")
    await engine.dispose()
    logger.info("Database connections closed")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="Microservice for user registration and authentication in the car detailing system",
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(users.router)


@app.get("/health", tags=["health"])
async def health_check():
    """
    Health check endpoint.

    Returns:
        Health status
    """
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION
    }


@app.get("/", tags=["root"])
async def root():
    """
    Root endpoint.

    Returns:
        Welcome message with service information
    """
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "endpoints": {
            "register": "/api/users/register",
            "login": "/api/users/login",
            "docs": "/docs",
            "health": "/health"
        }
    }
