"""
Configuration settings for Fines Service
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    service_name: str = "fines-service"
    service_port: int = 8007
    
    class Config:
        env_file = ".env"


settings = Settings()
