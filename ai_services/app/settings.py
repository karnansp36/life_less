# settings.py
import os
from dotenv import load_dotenv
from typing import List

load_dotenv()

class Settings:
    # App Configuration
    APP_NAME = os.getenv("APP_NAME", "PersonalManagerAI")
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    
    # AI Configuration
    AI_PROVIDER = os.getenv("AI_PROVIDER", "ollama").lower()
    OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
    OLLAMA_EMBEDDINGS_MODEL = os.getenv("OLLAMA_EMBEDDINGS_MODEL", "nomic-embed-text")
    
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:password@localhost/personal_manager")
    
    # Memory & RAG
    SHORT_MEMORY_MAXLEN = int(os.getenv("SHORT_MEMORY_MAXLEN", "20"))
    RAG_TOP_K = int(os.getenv("RAG_TOP_K", "5"))
    EMBEDDING_DIMENSIONS = int(os.getenv("EMBEDDING_DIMENSIONS", "768"))
    
    # Security & API
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    ALLOWED_ORIGINS: List[str] = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8000").split(",")
    
    # External Services
    EMAIL_SERVICE_ENABLED = os.getenv("EMAIL_SERVICE_ENABLED", "False").lower() == "true"
    CALENDAR_SERVICE_ENABLED = os.getenv("CALENDAR_SERVICE_ENABLED", "False").lower() == "true"
    
    # User Preferences Defaults
    DEFAULT_TIMEZONE = os.getenv("DEFAULT_TIMEZONE", "UTC")
    DEFAULT_WAKE_TIME = os.getenv("DEFAULT_WAKE_TIME", "07:00")
    DEFAULT_SLEEP_TIME = os.getenv("DEFAULT_SLEEP_TIME", "23:00")
    DEFAULT_WORK_HOURS_START = os.getenv("DEFAULT_WORK_HOURS_START", "09:00")
    DEFAULT_WORK_HOURS_END = os.getenv("DEFAULT_WORK_HOURS_END", "17:00")

settings = Settings()