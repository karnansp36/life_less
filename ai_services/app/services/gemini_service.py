import google.generativeai as genai
from core.config import settings
from typing import Dict, Any

class GeminiService:
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(settings.GEMINI_MODEL)
    
    async def generate_response(
        self, message: str, context: str, persona_settings: Dict[str, Any]
    ) -> str:
        # Build the prompt with persona and context
        prompt = self._build_prompt(message, context, persona_settings)
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"I'm sorry, I encountered an error: {str(e)}"
    
    def _build_prompt(
        self, message: str, context: str, persona_settings: Dict[str, Any]
    ) -> str:
        name = persona_settings.get("ai_name", settings.DEFAULT_AI_NAME)
        gender = persona_settings.get("ai_gender", settings.DEFAULT_AI_GENDER)
        tone = persona_settings.get("ai_tone", settings.DEFAULT_AI_TONE)
        
        prompt = f"""You are {name}, a {gender} AI assistant with a {tone} tone.
        
        Context from previous conversations:
        {context}
        
        Current conversation:
        User: {message}
        
        Respond naturally and helpfully as {name}:"""
        
        return prompt