from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, desc
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json
import hashlib
from redis.asyncio import Redis as AsyncRedis

from app.models.database import Conversation, Message
from app.services.embedding_service import embedding_service
from app.core.database import get_redis

class MemoryService:
    def __init__(self):
        self.redis_client: Optional[AsyncRedis] = None
    
    async def get_redis(self) -> AsyncRedis:
        if not self.redis_client:
            self.redis_client = get_redis()
        return self.redis_client
    
    async def get_or_create_conversation(
        self, db: AsyncSession, user_id: int, session_id: str
    ) -> Conversation:
        """Get existing conversation or create new one"""
        result = await db.execute(
            select(Conversation).filter(
                Conversation.user_id == user_id,
                Conversation.session_id == session_id,
                Conversation.is_active == True
            )
        )
        conversation = result.scalars().first()
        
        if not conversation:
            conversation = Conversation(
                user_id=user_id,
                session_id=session_id,
                title=f"Chat {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            )
            db.add(conversation)
            await db.commit()
            await db.refresh(conversation)
        
        return conversation
    
    async def store_message(
        self, 
        db: AsyncSession, 
        conversation_id: int, 
        role: str, 
        content: str,
        emotion_score: Optional[Dict] = None,
        metadata: Optional[Dict] = None
    ) -> Message:
        """Store message with embedding and emotion data"""
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            emotion_score=emotion_score or {},
            message_metadata=metadata or {}
        )
        db.add(message)
        await db.commit()
        await db.refresh(message)
        
        # Store embedding asynchronously (non-blocking)
        try:
            await self._store_message_embedding(message)
        except Exception as e:
            print(f"Warning: Failed to store embedding for message {message.id}: {e}")
        
        return message
    
    async def _store_message_embedding(self, message: Message):
        """Store message embedding in Redis"""
        try:
            # Generate embedding
            embedding = await embedding_service.encode_text(message.content)
            
            if embedding is not None:
                # Create embedding ID
                embedding_id = f"emb_{message.id}_{hashlib.md5(message.content.encode()).hexdigest()[:8]}"
                
                # Store in Redis with expiration (30 days)
                redis_client = await self.get_redis()
                
                # Convert numpy array to list for JSON serialization
                embedding_data = {
                    "embedding": embedding.tolist() if hasattr(embedding, 'tolist') else list(embedding),
                    "message_id": message.id,
                    "content_hash": hashlib.md5(message.content.encode()).hexdigest(),
                    "created_at": datetime.now().isoformat()
                }
                
                await redis_client.setex(
                    f"embedding:{embedding_id}", 
                    int(timedelta(days=30).total_seconds()),
                    json.dumps(embedding_data)
                )
                
                # Update message with embedding ID
                message.embedding_id = embedding_id
                
                # Don't commit here as this might be called within another transaction
                
        except Exception as e:
            print(f"Failed to store embedding for message {message.id}: {e}")
 
    async def get_conversation_context(
        self, 
        db: AsyncSession, 
        user_id: int, 
        conversation_id: int, 
        current_message: str,
        max_recent_messages: int = 10,
        max_relevant_messages: int = 5
    ) -> Dict[str, Any]:
        """Get comprehensive conversation context"""
        
        # Get recent messages from current conversation
        result = await db.execute(
            select(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(desc(Message.created_at))
            .limit(max_recent_messages)
        )
        recent_messages = result.scalars().all()
        
        # Get semantically similar messages from past conversations (simplified)
        relevant_messages = await self._get_relevant_historical_messages(
            db, user_id, current_message, max_relevant_messages, conversation_id
        )
        
        # Get user's emotional pattern
        emotional_context = await self._get_emotional_context(db, user_id)
        
        # Format context
        recent_context = self._format_messages_for_context(recent_messages[::-1])
        historical_context = self._format_messages_for_context(relevant_messages)
        
        return {
            "recent_conversation": recent_context,
            "relevant_history": historical_context,
            "emotional_context": emotional_context,
            "conversation_length": len(recent_messages),
            "user_id": user_id
        }
    
    async def _get_relevant_historical_messages(
        self, 
        db: AsyncSession, 
        user_id: int, 
        query_message: str, 
        limit: int,
        exclude_conversation_id: int
    ) -> List[Message]:
        """Find semantically similar messages from user's history (simplified version)"""
        try:
            # For now, just get recent messages from past conversations
            # In a full implementation, we'd use semantic search
            result = await db.execute(
                select(Message)
                .join(Conversation)
                .filter(
                    and_(
                        Conversation.user_id == user_id,
                        Conversation.id != exclude_conversation_id,
                        Message.created_at > datetime.now() - timedelta(days=7),
                        Message.role == "user"  # Focus on user messages
                    )
                )
                .order_by(desc(Message.created_at))
                .limit(limit * 2)  # Get more to filter
            )
            past_messages = result.scalars().all()
            
            # Simple keyword matching as fallback
            query_words = set(query_message.lower().split())
            scored_messages = []
            
            for message in past_messages:
                message_words = set(message.content.lower().split())
                # Simple word overlap score
                overlap = len(query_words.intersection(message_words))
                if overlap > 0:
                    scored_messages.append((message, overlap))
            
            # Sort by score and return top matches
            scored_messages.sort(key=lambda x: x[1], reverse=True)
            return [msg for msg, score in scored_messages[:limit]]
        
        except Exception as e:
            print(f"Error finding relevant messages: {e}")
            return []
    
    async def _get_emotional_context(self, db: AsyncSession, user_id: int) -> Dict[str, Any]:
        """Get user's emotional patterns and current mood"""
        result = await db.execute(
            select(Message)
            .join(Conversation)
            .filter(
                and_(
                    Conversation.user_id == user_id,
                    Message.role == "user",
                    Message.created_at > datetime.now() - timedelta(hours=24)
                )
            )
            .order_by(desc(Message.created_at))
            .limit(10)
        )
        recent_messages = result.scalars().all()
        
        # Analyze emotional patterns from recent messages
        emotions = []
        for msg in recent_messages:
            if msg.emotion_score:
                emotions.append(msg.emotion_score)
        
        return {
            "recent_emotions": emotions,
            "mood_trend": self._analyze_mood_trend(emotions),
            "last_interaction": recent_messages[0].created_at if recent_messages else None
        }
    
    def _format_messages_for_context(self, messages: List[Message]) -> str:
        """Format messages for AI context"""
        if not messages:
            return ""
        
        formatted = []
        for msg in messages:
            timestamp = msg.created_at.strftime("%H:%M")
            formatted.append(f"[{timestamp}] {msg.role}: {msg.content}")
        
        return "\n".join(formatted)
    
    def _analyze_mood_trend(self, emotions: List[Dict]) -> str:
        """Analyze overall mood trend from emotion scores"""
        if not emotions:
            return "neutral"
        
        positive_count = 0
        negative_count = 0
        
        for emotion in emotions:
            if isinstance(emotion, dict):
                sentiment = emotion.get('sentiment', {})
                if isinstance(sentiment, dict):
                    pos = sentiment.get('positive', 0)
                    neg = sentiment.get('negative', 0)
                    if pos > neg:
                        positive_count += 1
                    elif neg > pos:
                        negative_count += 1
        
        if positive_count > negative_count * 1.5:
            return "positive"
        elif negative_count > positive_count * 1.5:
            return "negative"
        else:
            return "neutral"
    
    async def update_conversation_summary(
        self, db: AsyncSession, conversation_id: int, summary_data: Dict
    ):
        """Update conversation with emotion summary and other metadata"""
        result = await db.execute(
            select(Conversation).filter(Conversation.id == conversation_id)
        )
        conversation = result.scalars().first()
        
        if conversation:
            conversation.emotion_summary = summary_data
            conversation.updated_at = datetime.now()
            await db.commit()

# Global instance
memory_service = MemoryService()