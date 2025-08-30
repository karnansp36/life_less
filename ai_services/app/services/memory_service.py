from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, desc
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json
import hashlib
from redis.asyncio import Redis as AsyncRedis

from app.models.database import Conversation, Message, User
from app.services.embedding_service import embedding_service
from app.core.database import get_redis

class MemoryService:
    def __init__(self):
        self.redis_client: Optional[AsyncRedis] = None

    async def get_redis(self) -> AsyncRedis:
        if not self.redis_client:
            self.redis_client = get_redis()
        return self.redis_client

    # ✅ Ensure user exists by ID
    async def get_or_create_user_by_id(self, db: AsyncSession, user_id: int) -> User:
        result = await db.execute(select(User).filter(User.id == user_id))
        user = result.scalars().first()
        if not user:
            user = User(
                id=user_id,
                username=f"user_{user_id}",
                email=f"user_{user_id}@example.com"
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
        return user

    async def get_or_create_conversation(
        self, db: AsyncSession, user_id: int, session_id: str
    ) -> Conversation:
        await self.get_or_create_user_by_id(db, user_id)

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
                title=f"Chat {datetime.now().strftime('%Y-%m-%d %H:%M')}",
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
        metadata: Optional[Dict] = None,
    ) -> Message:
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            emotion_score=emotion_score or {},
            message_metadata=metadata or {},
        )
        db.add(message)
        await db.commit()
        await db.refresh(message)

        try:
            await self._store_message_embedding(message, db)
        except Exception as e:
            print(f"⚠️ Failed to store embedding: {e}")

        return message

    async def _store_message_embedding(self, message: Message, db: AsyncSession):
        embedding = await embedding_service.encode_text(message.content)
        if embedding:
            embedding_id = f"emb_{message.id}_{hashlib.md5(message.content.encode()).hexdigest()[:8]}"
            redis_client = await self.get_redis()
            embedding_data = {
                "embedding": embedding.tolist() if hasattr(embedding, "tolist") else list(embedding),
                "message_id": message.id,
                "content_hash": hashlib.md5(message.content.encode()).hexdigest(),
                "created_at": datetime.now().isoformat(),
            }
            await redis_client.setex(
                f"embedding:{embedding_id}",
                int(timedelta(days=30).total_seconds()),
                json.dumps(embedding_data),
            )
            message.embedding_id = embedding_id
            db.add(message)
            await db.commit()

    async def get_conversation_context(
        self, db: AsyncSession, user_id: int, conversation_id: int, current_message: str,
        max_recent_messages: int = 10, max_relevant_messages: int = 5
    ) -> Dict[str, Any]:
        result = await db.execute(
            select(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(desc(Message.created_at))
            .limit(max_recent_messages)
        )
        recent_messages = result.scalars().all()
        relevant_messages = await self._get_relevant_historical_messages(
            db, user_id, current_message, max_relevant_messages, conversation_id
        )
        emotional_context = await self._get_emotional_context(db, user_id)

        return {
            "recent_conversation": self._format_messages_for_context(recent_messages[::-1]),
            "relevant_history": self._format_messages_for_context(relevant_messages),
            "emotional_context": emotional_context,
            "conversation_length": len(recent_messages),
            "user_id": user_id,
        }

    async def _get_relevant_historical_messages(
        self, db: AsyncSession, user_id: int, query_message: str, limit: int, exclude_conversation_id: int
    ) -> List[Message]:
        result = await db.execute(
            select(Message)
            .join(Conversation)
            .filter(
                and_(
                    Conversation.user_id == user_id,
                    Conversation.id != exclude_conversation_id,
                    Message.created_at > datetime.now() - timedelta(days=7),
                    Message.role == "user",
                )
            )
            .order_by(desc(Message.created_at))
            .limit(limit * 2)
        )
        past_messages = result.scalars().all()
        query_words = set(query_message.lower().split())
        scored_messages = []
        for msg in past_messages:
            overlap = len(query_words.intersection(set(msg.content.lower().split())))
            if overlap > 0:
                scored_messages.append((msg, overlap))
        scored_messages.sort(key=lambda x: x[1], reverse=True)
        return [msg for msg, _ in scored_messages[:limit]]

    async def _get_emotional_context(self, db: AsyncSession, user_id: int) -> Dict[str, Any]:
        result = await db.execute(
            select(Message)
            .join(Conversation)
            .filter(
                and_(
                    Conversation.user_id == user_id,
                    Message.role == "user",
                    Message.created_at > datetime.now() - timedelta(hours=24),
                )
            )
            .order_by(desc(Message.created_at))
            .limit(10)
        )
        recent_messages = result.scalars().all()
        emotions = [msg.emotion_score for msg in recent_messages if msg.emotion_score]
        return {
            "recent_emotions": emotions,
            "mood_trend": self._analyze_mood_trend(emotions),
            "last_interaction": recent_messages[0].created_at if recent_messages else None,
        }

    def _format_messages_for_context(self, messages: List[Message]) -> str:
        return "\n".join(f"[{msg.created_at.strftime('%H:%M')}] {msg.role}: {msg.content}" for msg in messages)

    def _analyze_mood_trend(self, emotions: List[Dict]) -> str:
        if not emotions:
            return "neutral"
        pos, neg = 0, 0
        for e in emotions:
            s = e.get("sentiment", {})
            if s.get("positive", 0) > s.get("negative", 0):
                pos += 1
            elif s.get("negative", 0) > s.get("positive", 0):
                neg += 1
        if pos > neg * 1.5:
            return "positive"
        elif neg > pos * 1.5:
            return "negative"
        return "neutral"

# Singleton instance
memory_service = MemoryService()
