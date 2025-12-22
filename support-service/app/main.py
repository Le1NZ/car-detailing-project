"""FastAPI application entry point."""
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.config import settings
from app.endpoints import support_router


# Create FastAPI application
app = FastAPI(
    title=settings.service_name,
    description="Support ticket management microservice",
    version="1.0.0",
)

from prometheus_fastapi_instrumentator import Instrumentator
Instrumentator().instrument(app).expose(app)


# Register routers
app.include_router(support_router)


@app.get("/", include_in_schema=False)
async def root() -> JSONResponse:
    """Root endpoint with service information."""
    return JSONResponse({
        "service": settings.service_name,
        "version": "1.0.0",
        "status": "running"
    })


@app.on_event("startup")
async def startup_event():
    """Execute on application startup."""
    print(f"{settings.service_name} started on port {settings.port}")


@app.on_event("shutdown")
async def shutdown_event():
    """Execute on application shutdown."""
    print(f"{settings.service_name} shutting down")
