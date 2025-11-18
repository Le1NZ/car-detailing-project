"""Configuration settings for Order Service"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""

    APP_NAME: str = "Order Service"
    APP_VERSION: str = "1.0.0"
    HOST: str = "0.0.0.0"
    PORT: int = 8003

    # External service URLs
    CAR_SERVICE_URL: str = "http://car-service:8002"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
