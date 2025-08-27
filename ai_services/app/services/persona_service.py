from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.database import PersonaSettings
from app.models.schemas import PersonaSettingsUpdate
from typing import Dict, Any, Optional
import random


class PersonaService:
    async def get_persona_settings(
        self, db: AsyncSession, user_id: int
    ) -> PersonaSettings:
        """Get or create persona settings for user"""
        result = await db.execute(
            select(PersonaSettings).where(PersonaSettings.user_id == user_id)
        )
        settings = result.scalars().first()

        if not settings:
            settings = await self.create_default_persona_settings(db, user_id)

        return settings

    async def create_default_persona_settings(
        self, db: AsyncSession, user_id: int
    ) -> PersonaSettings:
        """Create default persona settings if none exist"""
        settings = PersonaSettings(
            user_id=user_id,
            ai_name="Aria",
            ai_gender="female",
            ai_tone="warm and intelligent",
            ai_interests=["technology", "learning", "creativity"],
            personality_traits={
                "empathy": "high",
                "humor": "subtle",
                "knowledge_sharing": "educational",
                "curiosity": "high",
            },
            communication_style={
                "style": "engaging",
                "formality": "casual",
                "response_length": "balanced",
            },
        )
        db.add(settings)
        await db.commit()
        await db.refresh(settings)
        return settings

    async def update_persona_settings(
        self, db: AsyncSession, user_id: int, updates: PersonaSettingsUpdate
    ) -> PersonaSettings:
        """Update persona settings"""
        settings = await self.get_persona_settings(db, user_id)

        update_data = updates.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(settings, field, value)

        await db.commit()
        await db.refresh(settings)
        return settings

    def generate_welcome_message(self, persona: PersonaSettings) -> str:
        """Generate contextual welcome message"""
        name = persona.ai_name
        tone_style = persona.ai_tone
        personality = persona.personality_traits or {}

        # Base welcome templates by tone
        templates = {
            "warm and intelligent": [
                f"Hello! I'm {name}, and I'm genuinely excited to get to know you. What's on your mind today?",
                f"Hi there! {name} here - I love meaningful conversations. What would you like to explore together?",
                f"Welcome! I'm {name}, your thoughtful companion. How can I brighten your day?",
            ],
            "friendly and helpful": [
                f"Hey! I'm {name}, and I'm here to help with whatever you need. What's going on?",
                f"Hi! {name} at your service - ready to tackle any questions or just have a great chat!",
                f"Hello! I'm {name}, your friendly AI assistant. How can I make your day better?",
            ],
            "professional": [
                f"Good day. I'm {name}, your intelligent assistant. How may I assist you today?",
                f"Hello, I am {name}. I'm here to provide thoughtful assistance. What can I help you with?",
                f"Welcome. I'm {name}, ready to help you accomplish your goals. What shall we work on?",
            ],
            "casual and fun": [
                f"Hey! {name} here - ready for some great conversation! What's up?",
                f"Hi! I'm {name}, your AI buddy. What interesting thing should we talk about today?",
                f"Hello! {name} here, and I'm excited to chat with you. What's happening in your world?",
            ],
        }

        # Get templates for the tone, fallback to friendly
        tone_templates = templates.get(tone_style, templates["friendly and helpful"])

        # Select based on personality traits
        empathy_level = personality.get("empathy", "medium")
        if empathy_level == "high":
            return f"Hello! I'm {name}, and I can sense that every conversation is unique. I'm here to really listen and understand. What's in your heart today?"

        # Use standard template
        return random.choice(tone_templates)

    def adapt_response_style(
        self, persona: PersonaSettings, emotion_context: Optional[Dict] = None
    ) -> Dict[str, str]:
        """Adapt response style based on persona and context"""
        comm_style = persona.communication_style or {}
        base_style = {
            "tone": persona.ai_tone,
            "name": persona.ai_name,
            "formality": comm_style.get("formality", "casual"),
            "length": comm_style.get("response_length", "balanced"),
        }

        # Adapt based on user emotion if provided
        if emotion_context:
            user_emotion = emotion_context.get("primary_emotion", "neutral")
            intensity = emotion_context.get("intensity", 0.5)

            if user_emotion == "sad" and intensity > 0.6:
                base_style.update(
                    {
                        "tone": "gentle and supportive",
                        "pace": "slower",
                        "empathy": "maximum",
                    }
                )
            elif user_emotion == "excited" and intensity > 0.7:
                base_style.update(
                    {
                        "tone": "enthusiastic",
                        "energy": "high",
                    }
                )
            elif user_emotion == "anxious":
                base_style.update(
                    {
                        "tone": "calm and reassuring",
                        "pace": "steady",
                        "clarity": "high",
                    }
                )

        return base_style


# Global instance
persona_service = PersonaService()