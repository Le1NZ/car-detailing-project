"""Configuration settings for bonus-service"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings"""

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True
    )

    # Service configuration
    SERVICE_NAME: str = "bonus-service"
    SERVICE_PORT: int = 8006

    # RabbitMQ configuration
    AMQP_URL: str = "amqp://guest:guest@rabbitmq:5672/"
    PAYMENT_QUEUE: str = "payment_succeeded_queue"

    # Bonus accrual rate (1% of payment amount)
    BONUS_ACCRUAL_RATE: float = 0.01


settings = Settings()
