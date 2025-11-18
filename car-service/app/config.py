"""Configuration settings for car-service."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    service_name: str = "car-service"
    service_port: int = 8002
    api_prefix: str = "/api"

    # Validation constraints
    min_car_year: int = 1900
    max_car_year: int = 2025

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields from .env


settings = Settings()
