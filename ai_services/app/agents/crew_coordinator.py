from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.ai_service import ai_service
from app.services.emotion_service import emotion_service
from app.services.memory_service import memory_service
from app.models.schemas import PersonaSettings

class CrewCoordinator:
    """
    Coordinates multiple AI agents to provide intelligent responses
    This is a simplified version that coordinates the existing services
    """
    
    def __init__(self):
        self.agents = {
            "conversation_agent": ai_service,
            "emotion_agent": emotion_service,
            "memory_agent": memory_service
        }
    
    async def process_user_interaction(
        self,
        user_message: str,
        user_id: int,
        conversation_id: int,
        persona_settings: PersonaSettings,
        db_session: AsyncSession
    ) -> Dict[str, Any]:
        """
        Process user interaction through coordinated AI agents
        """
        start_time = datetime.now()
        
        try:
            # Step 1: Emotion Analysis Agent
            emotion_analysis = await emotion_service.analyze_emotion(
                user_message, 
                context={}
            )
            
            # Step 2: Memory Agent - Get conversation context
            memory_context = await memory_service.get_conversation_context(
                db_session,
                user_id,
                conversation_id,
                user_message,
                max_recent_messages=10,
                max_relevant_messages=5
            )
            
            # Step 3: Update user's emotional profile
            await emotion_service.update_emotional_profile(
                db_session, 
                user_id, 
                emotion_analysis
            )
            
            # Step 4: Generate context string for AI
            context_str = self._format_context_for_ai(memory_context)
            
            # Step 5: Conversation Agent - Generate response
            ai_response = await ai_service.generate_response(
                message=user_message,
                context=context_str,
                persona_settings=persona_settings,
                emotion_context=emotion_analysis,
                model_preference="gemini"
            )
            
            # Step 6: Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Step 7: Prepare coordinated response
            coordinated_response = {
                "content": ai_response["content"],
                "agent_coordination": {
                    "primary_agent": "conversation_agent",
                    "emotion_analysis_completed": True,
                    "memory_context_retrieved": True,
                    "model_used": ai_response.get("model_used", "fallback"),
                    "confidence": ai_response.get("confidence", 0.5)
                },
                "emotion_insights": {
                    "detected_emotion": emotion_analysis.get("primary_emotion", "neutral"),
                    "intensity": emotion_analysis.get("intensity", 0.5),
                    "empathy_applied": True,
                    "sentiment": emotion_analysis.get("sentiment", {})
                },
                "memory_utilized": {
                    "recent_messages_count": memory_context.get("conversation_length", 0),
                    "relevant_history_found": bool(memory_context.get("relevant_history", "")),
                    "emotional_context_applied": bool(memory_context.get("emotional_context"))
                },
                "metadata": {
                    "processing_time": processing_time,
                    "timestamp": datetime.now().isoformat(),
                    "agents_involved": ["conversation_agent", "emotion_agent", "memory_agent"],
                    "persona_adapted": True
                }
            }
            
            return coordinated_response
            
        except Exception as e:
            print(f"Error in crew coordination: {e}")
            return {
                "content": "I apologize, but I'm having trouble processing your message right now. Please try again.",
                "agent_coordination": {
                    "primary_agent": "fallback",
                    "error": str(e)
                },
                "emotion_insights": {
                    "detected_emotion": "neutral",
                    "intensity": 0.5,
                    "empathy_applied": False
                },
                "memory_utilized": {
                    "recent_messages_count": 0,
                    "relevant_history_found": False,
                    "emotional_context_applied": False
                },
                "metadata": {
                    "processing_time": (datetime.now() - start_time).total_seconds(),
                    "timestamp": datetime.now().isoformat(),
                    "error_occurred": True
                }
            }
    
    def _format_context_for_ai(self, memory_context: Dict[str, Any]) -> str:
        """Format memory context for AI consumption"""
        context_parts = []
        
        # Recent conversation
        recent = memory_context.get("recent_conversation", "")
        if recent:
            context_parts.append(f"Recent conversation:\n{recent}")
        
        # Relevant history
        history = memory_context.get("relevant_history", "")
        if history:
            context_parts.append(f"Relevant past conversations:\n{history}")
        
        # Emotional context
        emotional_context = memory_context.get("emotional_context", {})
        if emotional_context:
            mood_trend = emotional_context.get("mood_trend", "neutral")
            context_parts.append(f"User's recent emotional trend: {mood_trend}")
        
        return "\n\n".join(context_parts) if context_parts else ""
    
    async def get_agent_status(self) -> Dict[str, Any]:
        """Get status of all agents"""
        return {
            "conversation_agent": {
                "status": "operational" if ai_service.gemini else "fallback_mode",
                "model": "gemini-2.0-flash" if ai_service.gemini else "rule_based"
            },
            "emotion_agent": {
                "status": "operational",
                "capabilities": ["emotion_detection", "sentiment_analysis", "empathy_adaptation"]
            },
            "memory_agent": {
                "status": "operational", 
                "capabilities": ["conversation_memory", "semantic_search", "context_retrieval"]
            }
        }

# Global instance
crew_coordinator = CrewCoordinator()