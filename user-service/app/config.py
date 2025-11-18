"""
Configuration module using pydantic-settings for environment variable management.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database configuration
    POSTGRES_URL: str = "postgresql+asyncpg://user:password@localhost:5432/user_service_db"

    # JWT configuration
    JWT_SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_SECONDS: int = 3600

    # Application configuration
    APP_NAME: str = "User Service"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
