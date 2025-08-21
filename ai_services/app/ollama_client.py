# ollama_client.py
import aiohttp
import json
from typing import Optional, Dict, Any, List
from app.settings import settings
import logging

logger = logging.getLogger(__name__)

class OllamaClient:
    def __init__(self):
        self.base_url = settings.OLLAMA_HOST
        self.model = settings.OLLAMA_MODEL
        self.embeddings_model = settings.OLLAMA_EMBEDDINGS_MODEL
        self.session = None

    async def ensure_session(self):
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()

    async def close(self):
        if self.session:
            await self.session.close()

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        top_p: float = 0.9,
        max_tokens: int = 2000
    ) -> str:
        await self.ensure_session()
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "options": {
                "temperature": temperature,
                "top_p": top_p,
                "num_predict": max_tokens
            },
            "stream": False
        }
        
        if system_prompt:
            payload["system"] = system_prompt

        try:
            async with self.session.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=120)
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Ollama API error: {error_text}")
                    raise Exception(f"Ollama API error: {response.status} - {error_text}")
                
                result = await response.json()
                return result.get("response", "").strip()
                
        except Exception as e:
            logger.error(f"Error generating with Ollama: {str(e)}")
            raise

    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        top_p: float = 0.9,
        max_tokens: int = 2000
    ) -> str:
        await self.ensure_session()
        
        payload = {
            "model": self.model,
            "messages": messages,
            "options": {
                "temperature": temperature,
                "top_p": top_p,
                "num_predict": max_tokens
            },
            "stream": False
        }

        try:
            async with self.session.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=120)
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Ollama chat API error: {error_text}")
                    raise Exception(f"Ollama chat API error: {response.status} - {error_text}")
                
                result = await response.json()
                return result["message"]["content"].strip()
                
        except Exception as e:
            logger.error(f"Error chatting with Ollama: {str(e)}")
            raise

    async def generate_embeddings(self, text: str) -> List[float]:
        await self.ensure_session()
        
        payload = {
            "model": self.embeddings_model,
            "prompt": text
        }

        try:
            async with self.session.post(
                f"{self.base_url}/api/embeddings",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Ollama embeddings API error: {error_text}")
                    raise Exception(f"Ollama embeddings API error: {response.status} - {error_text}")
                
                result = await response.json()
                return result.get("embedding", [])
                
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            raise

# Global Ollama client instance
ollama_client = OllamaClient()