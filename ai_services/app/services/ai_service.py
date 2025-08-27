import google.generativeai as genai
import asyncio
from typing import Dict, Any, Optional, List
from app.core.config import settings
from app.models.schemas import PersonaSettings
import json

class AIService:
    def __init__(self):
        self.gemini = None
        if settings.GEMINI_API_KEY:
            try:
                genai.configure(api_key=settings.GEMINI_API_KEY)
                self.gemini = genai.GenerativeModel('gemini-2.0-flash')
            except Exception as e:
                print(f"Error configuring Gemini: {e}")
                self.gemini = None

    async def generate_response(
        self,
        message: str,
        context: str,
        persona_settings: PersonaSettings,
        emotion_context: Optional[Dict] = None,
        model_preference: str = "gemini"
    ) -> Dict[str, Any]:
        prompt = self._build_intelligent_prompt(
            message, context, persona_settings, emotion_context
        )
        
        try:
            if model_preference == "gemini" and self.gemini:
                response = await self._generate_gemini_response(prompt)
            else:
                # Fallback response
                response = self._generate_fallback_response(message, persona_settings)
            
            return {
                "content": response,
                "model_used": model_preference if self.gemini else "fallback",
                "emotion_adapted": bool(emotion_context),
                "confidence": 0.8 if self.gemini else 0.3,
                "requires_followup": False
            }
        except Exception as e:
            print(f"Error generating response with {model_preference}: {e}")
            return {
                "content": self._generate_fallback_response(message, persona_settings),
                "model_used": "fallback",
                "confidence": 0.3,
                "requires_followup": False,
                "emotion_adapted": False
            }

    async def _generate_gemini_response(self, prompt: str) -> str:
        """Generate response using Gemini"""
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                self.gemini.generate_content, 
                prompt
            )
            return response.text
        except Exception as e:
            print(f"Gemini API error: {e}")
            raise

    def _generate_fallback_response(self, message: str, persona_settings: PersonaSettings) -> str:
        """Generate fallback response when AI services are unavailable"""
        name = persona_settings.ai_name if persona_settings else "Aria"
        
        # Simple rule-based responses
        message_lower = message.lower()
        
        if any(greeting in message_lower for greeting in ['hello', 'hi', 'hey']):
            return f"Hello! I'm {name}. How can I help you today?"
        elif any(question in message_lower for question in ['how are you', 'how do you do']):
            return f"I'm doing well, thank you for asking! I'm here and ready to help. How are you doing?"
        elif 'thank' in message_lower:
            return f"You're very welcome! I'm glad I could help. Is there anything else you'd like to discuss?"
        elif '?' in message:
            return f"That's an interesting question! I'd love to help you explore that further. Could you tell me a bit more about what specifically interests you about this topic?"
        else:
            return f"I appreciate you sharing that with me. I'm here to listen and help in whatever way I can. What would you like to talk about?"

    def _build_intelligent_prompt(
        self,
        message: str,
        context: str,
        persona_settings: PersonaSettings,
        emotion_context: Optional[Dict] = None
    ) -> str:
        """Build intelligent prompt with persona and emotion awareness"""
        name = persona_settings.ai_name if persona_settings else "Aria"
        tone = persona_settings.ai_tone if persona_settings else "warm and intelligent"
        
        # Base system prompt
        system_prompt = f"""You are {name}, an AI assistant with a {tone} personality. 
        
Your key traits:
- Empathetic and understanding
- Genuinely curious about the user
- Helpful and knowledgeable
- Able to adapt your communication style based on the user's emotional state
"""
        
        # Add emotion context if available
        if emotion_context:
            emotion = emotion_context.get('primary_emotion', 'neutral')
            intensity = emotion_context.get('intensity', 0.5)
            
            if emotion != 'neutral':
                system_prompt += f"""
                
The user seems to be feeling {emotion} with intensity {intensity:.1f}. 
Please respond with appropriate empathy and adjust your tone accordingly.
"""
        
        # Add conversation context
        if context:
            system_prompt += f"""

Previous conversation context:
{context}
"""
        
        # Add current message
        full_prompt = f"""{system_prompt}

Current message: {message}

Please respond as {name} in a natural, helpful way."""
        
        return full_prompt

    async def analyze_conversation_intent(self, message: str) -> Dict[str, Any]:
        """Analyze conversation intent - simplified version"""
        analysis_prompt = f"""
        Analyze this message for:
        1. Primary intent (question, request, emotional sharing, casual chat)
        2. Emotional tone (scale 1-10 for: happy, sad, angry, anxious, excited, neutral)
        3. Topics mentioned
        4. Urgency level (low, medium, high)
        5. Follow-up potential (should we follow up on this later?)
        
        Message: "{message}"
        
        Respond in JSON format.
        """
        
        try:
            if self.gemini:
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None, 
                    self.gemini.generate_content, 
                    analysis_prompt
                )
                return json.loads(response.text)
        except Exception as e:
            print(f"Error analyzing intent with Gemini: {e}")
        
        # Fallback analysis
        message_lower = message.lower()
        
        # Simple keyword-based analysis
        intent = "general_chat"
        if '?' in message:
            intent = "question"
        elif any(word in message_lower for word in ['help', 'need', 'can you']):
            intent = "request"
        elif any(word in message_lower for word in ['feel', 'sad', 'happy', 'angry', 'worried']):
            intent = "emotional_sharing"
            
        emotions = {"neutral": 5}
        if any(word in message_lower for word in ['happy', 'great', 'awesome', 'excellent']):
            emotions = {"happy": 8, "neutral": 2}
        elif any(word in message_lower for word in ['sad', 'down', 'upset', 'disappointed']):
            emotions = {"sad": 7, "neutral": 3}
        elif any(word in message_lower for word in ['worried', 'anxious', 'nervous', 'scared']):
            emotions = {"anxious": 7, "neutral": 3}
        
        return {
            "intent": intent,
            "emotions": emotions,
            "topics": [],
            "urgency": "medium" if intent == "request" else "low",
            "follow_up_potential": intent in ["emotional_sharing", "request"]
        }

ai_service = AIService()