"""Main FastAPI application for bonus-service"""
import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.endpoints import bonuses
from app.models.bonus import HealthResponse
from app.services.bonus_service import BonusService
from app.services.rabbitmq_consumer import RabbitMQConsumer
from app.repositories.local_bonus_repo import bonus_repository
from prometheus_fastapi_instrumentator import Instrumentator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Global consumer instance
rabbitmq_consumer: RabbitMQConsumer = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events
    """
    # Startup
    logger.info(f"Starting {settings.SERVICE_NAME} on port {settings.SERVICE_PORT}")
    
    # Initialize RabbitMQ consumer
    global rabbitmq_consumer
    bonus_service = BonusService(repository=bonus_repository)
    rabbitmq_consumer = RabbitMQConsumer(bonus_service=bonus_service)
    
    # Start consuming in background task
    try:
        await rabbitmq_consumer.start()
        logger.info("RabbitMQ consumer started successfully")
    except Exception as e:
        logger.error(f"Failed to start RabbitMQ consumer: {e}", exc_info=True)
        logger.warning("Service will continue without RabbitMQ consumer")
    
    logger.info(f"{settings.SERVICE_NAME} startup complete")
    
    yield
    
    # Shutdown
    logger.info(f"Shutting down {settings.SERVICE_NAME}")
    if rabbitmq_consumer:
        await rabbitmq_consumer.stop()
    logger.info(f"{settings.SERVICE_NAME} shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="Bonus Service API",
    description="Microservice for managing bonuses and promocodes",
    version="1.0.0",
    lifespan=lifespan
)

Instrumentator().instrument(app).expose(app)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(bonuses.router)


@app.get("/health", response_model=HealthResponse, tags=["health"])
async def health_check():
    """
    Health check endpoint
    """
    return HealthResponse(
        status="healthy",
        service=settings.SERVICE_NAME
    )


@app.get("/", tags=["root"])
async def root():
    """
    Root endpoint
    """
    return {
        "service": settings.SERVICE_NAME,
        "version": "1.0.0",
        "status": "running"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.SERVICE_PORT,
        reload=False
    )
