"""
Main FastAPI application for Fines Service
"""
from fastapi import FastAPI
from app.config import settings
from app.endpoints import fines


# Create FastAPI application
app = FastAPI(
    title=settings.service_name,
    description="Microservice for managing traffic fines",
    version="1.0.0"
)

from prometheus_fastapi_instrumentator import Instrumentator
Instrumentator().instrument(app).expose(app)


# Include routers
app.include_router(fines.router)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": settings.service_name,
        "port": settings.service_port
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": settings.service_name,
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "check_fines": "/api/fines/check?license_plate={plate}",
            "pay_fine": "/api/fines/{fine_id}/pay"
        }
    }
