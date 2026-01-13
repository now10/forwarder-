from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl, validator, Field
import os


class Settings(BaseSettings):
    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Telegram Forwarder SaaS"
    VERSION: str = "1.0.0"
    
    # Security
    SECRET_KEY: str = Field(default="changemeinproduction", min_length=32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    ALGORITHM: str = "HS256"
    
    # Render provides PORT environment variable
    PORT: int = Field(default=8000)
    
    # CORS - Allow Render and localhost
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "https://*.onrender.com",
        "https://telegram-forwarder-saas.onrender.com",
    ]
    
    # Database - Render provides DATABASE_URL
    DATABASE_URL: Optional[str] = None
    
    @validator("DATABASE_URL", pre=True)
    def fix_postgres_url(cls, v: Optional[str]) -> Optional[str]:
        if v and v.startswith("postgres://"):
            # SQLAlchemy needs postgresql://
            return v.replace("postgres://", "postgresql://", 1)
        return v
    
    # Redis - Render provides REDIS_URL for Redis service
    REDIS_URL: Optional[str] = "redis://localhost:6379"
    
    # In Render free tier, services might sleep. Adjust accordingly
    REDIS_CONNECTION_TIMEOUT: int = 10
    REDIS_RETRY_ON_TIMEOUT: bool = True
    
    # Email - Optional for free tier
    SMTP_ENABLED: bool = False  # Disable email in free tier by default
    SMTP_TLS: bool = True
    SMTP_PORT: Optional[int] = None
    SMTP_HOST: Optional[str] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: Optional[str] = None
    EMAILS_FROM_NAME: Optional[str] = None
    
    # Frontend URL
    FRONTEND_URL: str = "https://telegram-forwarder-saas.onrender.com"
    
    # Telegram API (users provide their own)
    TELEGRAM_API_ID: Optional[str] = None
    TELEGRAM_API_HASH: Optional[str] = None
    
    # Rate limiting - conservative for free tier
    RATE_LIMIT_PER_MINUTE: int = 30
    RATE_LIMIT_PER_HOUR: int = 500
    
    # File uploads - use Render's ephemeral storage
    MAX_UPLOAD_SIZE: int = 5 * 1024 * 1024  # 5MB for free tier
    UPLOAD_DIR: str = "/tmp/uploads"  # Use tmp for ephemeral storage
    
    # Logging
    LOG_LEVEL: str = "INFO"
    DEBUG: bool = False
    
    # Render-specific
    RENDER: bool = Field(default=False)
    
    @validator("RENDER", pre=True)
    def detect_render(cls, v: Optional[bool]) -> bool:
        return os.getenv("RENDER", "").lower() == "true"
    
    class Config:
        case_sensitive = True
        env_file = ".env"


# Detect if we're on Render
if os.getenv("RENDER"):
    print("🚀 Running on Render.com")
    settings = Settings(RENDER=True)
else:
    settings = Settings()