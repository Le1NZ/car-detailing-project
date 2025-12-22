"""Точка входа FastAPI приложения."""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.endpoints import router as payments_router
from app.services import rabbitmq_publisher

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

# Создание FastAPI приложения
app = FastAPI(
    title=settings.service_name,
    description="Микросервис обработки платежей с RabbitMQ Publisher",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

from prometheus_fastapi_instrumentator import Instrumentator
Instrumentator().instrument(app).expose(app)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение роутеров
app.include_router(payments_router)


@app.get("/health", tags=["health"])
async def health_check():
    """
    Health check endpoint.

    Returns:
        Статус сервиса
    """
    return {
        "status": "healthy",
        "service": settings.service_name,
        "rabbitmq_connected": rabbitmq_publisher.connection is not None
    }


@app.on_event("startup")
async def startup_event():
    """
    Выполняется при запуске приложения.

    Устанавливает соединение с RabbitMQ.
    """
    logger.info(f"Starting {settings.service_name}...")

    try:
        await rabbitmq_publisher.connect()
        logger.info("RabbitMQ connection established")
    except Exception as e:
        logger.error(f"Failed to connect to RabbitMQ: {e}")
        # В продакшене здесь можно решить, завершать ли приложение
        # raise

    logger.info(f"{settings.service_name} started successfully on port {settings.port}")


@app.on_event("shutdown")
async def shutdown_event():
    """
    Выполняется при остановке приложения.

    Закрывает соединение с RabbitMQ.
    """
    logger.info(f"Shutting down {settings.service_name}...")

    try:
        await rabbitmq_publisher.close()
        logger.info("RabbitMQ connection closed")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

    logger.info(f"{settings.service_name} stopped")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=True
    )
