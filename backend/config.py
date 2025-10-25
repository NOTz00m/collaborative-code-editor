"""
Configuration settings for the collaborative code editor application.
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    
    secret_key: str = "dev-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    # WebSocket settings
    heartbeat_interval: int = 30  # seconds
    max_message_size: int = 1024 * 1024  # 1MB
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
