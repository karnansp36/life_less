import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    ALLOWED_ORIGINS = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")]

    AI_PROVIDER = os.getenv("AI_PROVIDER", "gemini").lower()

    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "google/gemini-pro")  # Add provider prefix

    OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    MISTRAL_MODEL = os.getenv("MISTRAL_MODEL", "mistral:latest")

    DATABASE_URL = os.getenv("DATABASE_URL")

    EMBEDDINGS_MODEL = os.getenv("EMBEDDINGS_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    RAG_TOP_K = int(os.getenv("RAG_TOP_K", "4"))
    SHORT_MEMORY_MAXLEN = int(os.getenv("SHORT_MEMORY_MAXLEN", "30"))

settings = Settings()
