# app/llm.py
from app.settings import settings
import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI

def configure_gemini():
    """Configure the Gemini API with your API key"""
    genai.configure(api_key=settings.GEMINI_API_KEY)

def get_llm():
    if settings.AI_PROVIDER == "gemini":
        if not settings.GEMINI_API_KEY:
            raise RuntimeError("GEMINI_API_KEY is not set")
        configure_gemini()
        return ChatGoogleGenerativeAI(
            model=settings.GEMINI_MODEL,  # e.g. "gemini-pro"
            google_api_key=settings.GEMINI_API_KEY,
            temperature=0.7
        )
    elif settings.AI_PROVIDER == "mistral":
        from langchain_community.chat_models import ChatOllama
        return ChatOllama(
            model=settings.MISTRAL_MODEL,
            base_url=settings.OLLAMA_HOST,
            temperature=0.2
        )
    else:
        raise RuntimeError(f"Unknown AI_PROVIDER '{settings.AI_PROVIDER}'")