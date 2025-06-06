from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl
from typing import List, Optional
import os

class Settings(BaseSettings):
    # API settings
    API_V1_STR: str = "/api/v1"
    
    # Security settings
    SECRET_KEY: str = "your-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # SQLite database URL
    SQLALCHEMY_DATABASE_URL: str = "sqlite:///./database.db"
    
    # CORS settings
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []
    
    # Redis settings (if needed)
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Groq API settings
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "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")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings() 