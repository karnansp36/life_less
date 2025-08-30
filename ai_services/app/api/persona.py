from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.core.dependencies import get_db, verify_api_key
from app.models.schemas import PersonaSettingsUpdate, PersonaSettingsResponse
from app.services.persona_service import persona_service
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/settings/{user_id}", response_model=PersonaSettingsResponse)
async def get_persona_settings(
    user_id: int,
    db: Session = Depends(get_db),
    _: Dict = Depends(verify_api_key),   # ✅ replaced get_current_user
):
    """Get persona settings for a user"""
    try:
        settings = await persona_service.get_persona_settings(db, user_id)
        return PersonaSettingsResponse(
            id=settings.id,
            user_id=settings.user_id,
            ai_name=settings.ai_name,
            ai_gender=settings.ai_gender,
            ai_tone=settings.ai_tone,
            ai_interests=settings.ai_interests,
            personality_traits=settings.personality_traits,
            communication_style=settings.communication_style,
            created_at=settings.created_at,
            updated_at=settings.updated_at
        )
    except Exception as e:
        logger.error(f"Error getting persona settings for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/settings/{user_id}", response_model=PersonaSettingsResponse)
async def update_persona_settings(
    user_id: int,
    updates: PersonaSettingsUpdate,
    db: Session = Depends(get_db),
    _: Dict = Depends(verify_api_key),   # ✅ API key auth
):
    """Update persona settings for a user"""
    try:
        settings = await persona_service.update_persona_settings(db, user_id, updates)
        return PersonaSettingsResponse(
            id=settings.id,
            user_id=settings.user_id,
            ai_name=settings.ai_name,
            ai_gender=settings.ai_gender,
            ai_tone=settings.ai_tone,
            ai_interests=settings.ai_interests,
            personality_traits=settings.personality_traits,
            communication_style=settings.communication_style,
            created_at=settings.created_at,
            updated_at=settings.updated_at
        )
    except Exception as e:
        logger.error(f"Error updating persona settings for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/presets")
async def get_persona_presets(_: Dict = Depends(verify_api_key)):
    """Get available persona presets"""
    presets = {
        "professional": {
            "ai_name": "Alexandra",
            "ai_gender": "female",
            "ai_tone": "professional",
            "ai_interests": ["business", "productivity", "technology"],
            "personality_traits": {
                "empathy": "medium",
                "humor": "minimal",
                "knowledge_sharing": "detailed",
                "curiosity": "high"
            },
            "communication_style": {
                "style": "formal",
                "formality": "professional",
                "response_length": "detailed"
            }
        },
        "friendly": {
            "ai_name": "Aria",
            "ai_gender": "female",
            "ai_tone": "warm and intelligent",
            "ai_interests": ["technology", "learning", "creativity", "wellness"],
            "personality_traits": {
                "empathy": "high",
                "humor": "subtle",
                "knowledge_sharing": "educational",
                "curiosity": "high"
            },
            "communication_style": {
                "style": "engaging",
                "formality": "casual",
                "response_length": "balanced"
            }
        },
        "casual": {
            "ai_name": "Alex",
            "ai_gender": "neutral",
            "ai_tone": "casual and fun",
            "ai_interests": ["entertainment", "games", "movies", "music"],
            "personality_traits": {
                "empathy": "medium",
                "humor": "playful",
                "knowledge_sharing": "conversational",
                "curiosity": "medium"
            },
            "communication_style": {
                "style": "casual",
                "formality": "informal",
                "response_length": "concise"
            }
        },
        "supportive": {
            "ai_name": "Sophie",
            "ai_gender": "female",
            "ai_tone": "gentle and supportive",
            "ai_interests": ["wellness", "mindfulness", "relationships", "personal_growth"],
            "personality_traits": {
                "empathy": "very_high",
                "humor": "gentle",
                "knowledge_sharing": "supportive",
                "curiosity": "caring"
            },
            "communication_style": {
                "style": "empathetic",
                "formality": "warm",
                "response_length": "thoughtful"
            }
        }
    }
    
    return {
        "presets": presets,
        "default": "friendly"
    }


@router.post("/settings/{user_id}/apply-preset")
async def apply_persona_preset(
    user_id: int,
    preset_data: Dict[str, Any],
    db: Session = Depends(get_db),
    _: Dict = Depends(verify_api_key),
):
    """Apply a persona preset to user settings"""
    try:
        preset_name = preset_data.get("preset_name")
        if not preset_name:
            raise HTTPException(status_code=400, detail="preset_name is required")
        
        presets_response = await get_persona_presets()
        presets = presets_response["presets"]
        
        if preset_name not in presets:
            raise HTTPException(status_code=404, detail=f"Preset '{preset_name}' not found")
        
        preset = presets[preset_name]
        updates = PersonaSettingsUpdate(**preset)
        
        settings = await persona_service.update_persona_settings(db, user_id, updates)
        
        return {
            "message": f"Applied '{preset_name}' preset successfully",
            "settings": PersonaSettingsResponse(
                id=settings.id,
                user_id=settings.user_id,
                ai_name=settings.ai_name,
                ai_gender=settings.ai_gender,
                ai_tone=settings.ai_tone,
                ai_interests=settings.ai_interests,
                personality_traits=settings.personality_traits,
                communication_style=settings.communication_style,
                created_at=settings.created_at,
                updated_at=settings.updated_at
            )
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error applying preset for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/welcome-message/{user_id}")
async def get_welcome_message(
    user_id: int,
    db: Session = Depends(get_db),
    _: Dict = Depends(verify_api_key),
):
    """Generate a welcome message based on user's persona"""
    try:
        persona = await persona_service.get_persona_settings(db, user_id)
        welcome_msg = persona_service.generate_welcome_message(persona)
        
        return {
            "message": welcome_msg,
            "persona_name": persona.ai_name,
            "tone": persona.ai_tone
        }
    except Exception as e:
        logger.error(f"Error generating welcome message for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/personality-insights/{user_id}")
async def get_personality_insights(
    user_id: int,
    db: Session = Depends(get_db),
    _: Dict = Depends(verify_api_key),
):
    """Get insights about the current persona configuration"""
    try:
        persona = await persona_service.get_persona_settings(db, user_id)
        
        insights = {
            "persona_summary": f"{persona.ai_name} is a {persona.ai_gender} AI with a {persona.ai_tone} personality",
            "key_traits": {
                "empathy_level": persona.personality_traits.get("empathy", "medium"),
                "humor_style": persona.personality_traits.get("humor", "subtle"),
                "communication_approach": persona.communication_style.get("style", "balanced")
            },
            "interests": persona.ai_interests or [],
            "conversation_style": {
                "formality": persona.communication_style.get("formality", "casual"),
                "response_length": persona.communication_style.get("response_length", "balanced")
            },
            "recommendations": []
        }
        
        if persona.personality_traits.get("empathy") == "high":
            insights["recommendations"].append(
                "Your AI is configured for high emotional intelligence - great for personal conversations"
            )
        
        if "technology" in (persona.ai_interests or []):
            insights["recommendations"].append(
                "Your AI enjoys discussing technology and innovation"
            )
        
        if persona.communication_style.get("formality") == "professional":
            insights["recommendations"].append(
                "Your AI uses professional communication - perfect for work-related discussions"
            )
        
        return insights
        
    except Exception as e:
        logger.error(f"Error getting personality insights for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
