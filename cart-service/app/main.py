"""
Main FastAPI application for Cart Service
"""
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer
import logging

from app.endpoints import cart
from app.config import SERVICE_NAME, SERVICE_PORT


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Security scheme for Swagger UI
security = HTTPBearer()

# Create FastAPI application
app = FastAPI(
    title="Cart Service",
    description="Shopping cart management microservice for automotive services and products",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    swagger_ui_parameters={
        "persistAuthorization": True  # Сохраняет токен между обновлениями страницы
    }
)

from prometheus_fastapi_instrumentator import Instrumentator
Instrumentator().instrument(app).expose(app)


# Include routers
app.include_router(cart.router)


@app.on_event("startup")
async def startup_event():
    """
    Application startup event handler
    """
    logger.info(f"{SERVICE_NAME} starting on port {SERVICE_PORT}")
    logger.info("In-memory cart storage initialized")


@app.on_event("shutdown")
async def shutdown_event():
    """
    Application shutdown event handler
    """
    logger.info(f"{SERVICE_NAME} shutting down")


@app.get("/health", tags=["health"])
async def health_check():
    """
    Health check endpoint

    Returns:
        Health status of the service
    """
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "service": SERVICE_NAME,
            "version": "1.0.0"
        }
    )


@app.get("/", tags=["root"])
async def root():
    """
    Root endpoint

    Returns:
        Service information
    """
    return {
        "service": SERVICE_NAME,
        "version": "1.0.0",
        "description": "Shopping cart management microservice",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "cart": "/api/cart"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=SERVICE_PORT,
        reload=True,
        log_level="info"
    )
