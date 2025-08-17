from app.settings import settings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.chat_models import ChatOllama

def get_llm():
    if settings.AI_PROVIDER == "gemini":
        if not settings.GEMINI_API_KEY:
            raise RuntimeError("GEMINI_API_KEY is not set")
        return ChatGoogleGenerativeAI(
            model=settings.GEMINI_MODEL,
            api_key=settings.GEMINI_API_KEY,
            temperature=0.2
        )
    elif settings.AI_PROVIDER == "mistral":
        return ChatOllama(
            model=settings.MISTRAL_MODEL,
            base_url=settings.OLLAMA_HOST,
            temperature=0.2
        )
    else:
        raise RuntimeError(f"Unknown AI_PROVIDER '{settings.AI_PROVIDER}'")
