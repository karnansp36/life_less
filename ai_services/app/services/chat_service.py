from typing import Dict, Any, List
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app import models
from app.services.orchestrator import Orchestrator
from app.memory_manager import MemoryManager
import logging

logger = logging.getLogger(__name__)

class ChatService:
    def __init__(self, session, user: models.User):
        self.session = session
        self.user = user
        self.orchestrator = Orchestrator(session, user)
        self.memory_manager = MemoryManager(session, user.id)

    async def process_message(self, message: str, conversation_id: int = None) -> Dict[str, Any]:
        """Process a user message and return response using orchestrator"""
        try:
            # Use orchestrator to route to appropriate agent
            result = await self.orchestrator.route_message(message)
            
            # Create or update conversation
            conversation = await self._update_conversation(
                conversation_id, 
                message, 
                result["response"],
                result["agent_used"]
            )
            
            return {
                "response": result["response"],
                "conversation_id": conversation.id,
                "agent_used": result["agent_used"],
                "memories_used": result.get("memories_used", 0),
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            return {
                "response": "I apologize, but I'm having trouble processing your request right now. Please try again later.",
                "conversation_id": conversation_id,
                "error": str(e),
                "success": False
            }

    async def _update_conversation(self, conversation_id: int, user_message: str, 
                                 assistant_response: str, agent_used: str):
        """Update or create conversation with new messages"""
        if conversation_id:
            # Add to existing conversation
            stmt = select(models.Conversation).where(
                models.Conversation.id == conversation_id,
                models.Conversation.user_id == self.user.id
            )
            result = await self.session.execute(stmt)
            conversation = result.scalar_one_or_none()
        else:
            # Create new conversation
            conversation = models.Conversation(
                user_id=self.user.id,
                title=user_message[:100] + "..." if len(user_message) > 100 else user_message
            )
            self.session.add(conversation)
            await self.session.flush()
        
        # Add user message
        user_msg = models.Message(
            conversation_id=conversation.id,
            user_id=self.user.id,  # ← Make sure this is set!
            role="user",
            content=user_message,
            message_metadata={}
        )
        self.session.add(user_msg)
        
        # Add assistant response with agent metadata
        assistant_msg = models.Message(
            conversation_id=conversation.id,
            user_id=self.user.id,  # ← This should also be set!
            role="assistant", 
            content=assistant_response,
            message_metadata={"agent_used": agent_used}
        )
        self.session.add(assistant_msg)
        
        await self.session.flush()
        return conversation

    async def get_conversation_history(self, conversation_id: int = None, limit: int = 10):
        """Get conversation history"""
        if conversation_id:
            stmt = select(models.Conversation).where(
                models.Conversation.id == conversation_id,  # ← This should be integer
                models.Conversation.user_id == self.user.id
            ).options(selectinload(models.Conversation.messages))
        else:
            stmt = select(models.Conversation).where(
                models.Conversation.user_id == self.user.id
            ).order_by(models.Conversation.updated_at.desc()).limit(1)
        
        result = await self.session.execute(stmt)
        conversation = result.scalar_one_or_none()
        
        if not conversation:
            return None
        
        return {
            "id": conversation.id,
            "title": conversation.title,
            "messages": [
                {
                    "id": msg.id,
                    "role": msg.role,
                    "content": msg.content,
                    "agent_used": msg.metadata.get("agent_used") if msg.metadata else None,
                    "created_at": msg.created_at
                }
                for msg in conversation.messages
            ]
        }