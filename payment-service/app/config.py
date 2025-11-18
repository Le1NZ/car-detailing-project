"""Конфигурация приложения."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Настройки приложения."""

    service_name: str = "payment-service"
    port: int = 8005
    amqp_url: str = "amqp://guest:guest@rabbitmq:5672/"

    class Config:
        """Конфигурация настроек."""

        env_file = ".env"


settings = Settings()
