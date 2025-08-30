from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List, Optional
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # App Config
    PROJECT_NAME: str = "Intelligent AI Chat"
    VERSION: str = "2.0.0"
    API_V1_STR: str = "/api/v1"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True  # Set to True for development
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # AI Models
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = "gemini-2.0-flash"
    
    # Embedding
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"  # More reliable model
    EMBEDDING_DIMENSION: int = 384  # Correct dimension for all-MiniLM-L6-v2
    
    # Vector Store (for future use)
    QDRANT_HOST: str = os.getenv("QDRANT_HOST", "localhost")
    QDRANT_PORT: int = int(os.getenv("QDRANT_PORT", "6333"))
    
    # AI Defaults
    DEFAULT_AI_NAME: str = "Aria"
    DEFAULT_AI_GENDER: str = "female"
    DEFAULT_AI_TONE: str = "warm and intelligent"
    
    # Proactive Features
    ENABLE_PROACTIVE_CHAT: bool = True
    PROACTIVE_CHECK_INTERVAL: int = 3600  # 1 hour
    
    # CORS
    ALLOWED_ORIGINS: List[str] = ["*"]  # Restrict in production
    
    # Security (add these for production)
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    API_SECRET_KEY: str

    class Config:
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()