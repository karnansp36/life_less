import ollama
from app.settings import settings

def generate_with_mistral_raw(prompt: str) -> str:
    resp = ollama.chat(
        model=settings.MISTRAL_MODEL,
        messages=[{"role": "user", "content": prompt}],
        # If running across WSL/Windows boundary, set OLLAMA_HOST env
    )
    return resp["message"]["content"]
