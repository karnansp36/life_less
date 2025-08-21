# agents/base_agent.py
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from app.ollama_client import ollama_client
from app.database import AsyncSession
from app import models
import logging

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    def __init__(self, session: AsyncSession, user: models.User):
        self.session = session
        self.user = user
        self.agent_type = self.__class__.__name__

    @abstractmethod
    async def generate_system_prompt(self) -> str:
        """Generate the system prompt for this agent"""
        pass

    @abstractmethod
    async def process_query(self, query: str, context: Dict[str, Any] = None) -> str:
        """Process a user query and return a response"""
        pass

    async def generate_response(self, prompt: str, system_prompt: str = None) -> str:
        """Generate a response using Ollama"""
        try:
            if system_prompt:
                return await ollama_client.generate(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    temperature=0.7
                )
            else:
                return await ollama_client.generate(prompt=prompt, temperature=0.7)
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return "I apologize, but I'm having trouble processing your request right now. Please try again later."

    async def chat_with_messages(self, messages: List[Dict[str, str]]) -> str:
        """Chat using message history"""
        try:
            return await ollama_client.chat(messages=messages, temperature=0.7)
        except Exception as e:
            logger.error(f"Error in chat: {str(e)}")
            return "I apologize, but I'm having trouble processing your request right now. Please try again later."

    async def detect_emotion(self, text: str) -> str:
        """Detect emotion in text"""
        prompt = f"""
        Analyze the following text and identify the primary emotion being expressed.
        Choose from: happy, sad, angry, anxious, stressed, excited, neutral, tired, motivated, frustrated.
        
        Text: {text}
        
        Respond with only the emotion word.
        """
        
        try:
            emotion = await ollama_client.generate(prompt=prompt, temperature=0.1)
            return emotion.strip().lower()
        except:
            return "neutral"

    async def generate_empathetic_response(self, query: str, detected_emotion: str) -> str:
        """Generate an empathetic response based on detected emotion"""
        empathy_map = {
            "happy": "That's wonderful to hear! I'm really happy for you.",
            "sad": "I'm sorry to hear that. I'm here to support you through this.",
            "angry": "I understand you're feeling frustrated. Let's work through this together.",
            "anxious": "It sounds like you're feeling anxious. Take a deep breath - we'll handle this step by step.",
            "stressed": "I can see you're under pressure. Let's prioritize and tackle things one at a time.",
            "excited": "That's exciting! I'm thrilled to see you so motivated!",
            "tired": "It sounds like you could use some rest. Remember to take care of yourself.",
            "motivated": "Great energy! Let's channel that motivation into action.",
            "frustrated": "I understand this is frustrating. Let's find a way to overcome this challenge.",
            "neutral": "Thanks for sharing that with me."
        }
        
        return empathy_map.get(detected_emotion, "I appreciate you sharing that with me.")