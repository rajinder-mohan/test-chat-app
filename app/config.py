import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # API settings
    API_V1_STR: str = "/api/v1"
    
    # Security settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-for-development-only")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Database settings
    SQLITE_DATABASE_URL: str = "sqlite:///./chat_app.db"
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    MONGODB_DB_NAME: str = os.getenv("MONGODB_DB_NAME", "chat_app")
    
    # Cache settings
    REDIS_URL: Optional[str] = os.getenv("REDIS_URL")
    CACHE_EXPIRE_SECONDS: int = 60 * 5  # 5 minutes
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings() 