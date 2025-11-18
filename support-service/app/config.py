"""Application configuration using pydantic-settings."""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    service_name: str = "support-service"
    port: int = 8008

    # Mock user ID for testing (in production would come from auth token)
    mock_user_id: str = "c3f4e1a1-5b8a-4b0e-8d9b-9d4a6f1e2c3d"

    class Config:
        """Pydantic configuration."""

        env_file = ".env"


settings = Settings()
