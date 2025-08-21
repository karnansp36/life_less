# memory_manager.py
from typing import List, Dict, Any
from sqlalchemy import select, text
from app import models
from app.ollama_client import ollama_client
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class MemoryManager:
    def __init__(self, session, user_id: int):
        self.session = session
        self.user_id = user_id

    async def store_memory(self, content: str, memory_type: str, importance: float = 0.5, tags: List[str] = None):
        """Store a new memory with embedding"""
        try:
            # Generate embedding
            embedding = await ollama_client.generate_embeddings(content)
            
            memory = models.Memory(
                user_id=self.user_id,
                memory_type=memory_type,
                content=content,
                importance=importance,
                embedding=embedding,
                tags=tags or [],
                last_accessed=datetime.now()
            )
            
            self.session.add(memory)
            await self.session.flush()
            return memory
            
        except Exception as e:
            logger.error(f"Error storing memory: {str(e)}")
            raise

    async def retrieve_relevant_memories(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Retrieve memories relevant to the query using semantic search"""
        try:
            # Generate query embedding
            query_embedding = await ollama_client.generate_embeddings(query)
            
            # Convert to PostgreSQL vector format
            vec_str = "[" + ",".join(map(str, query_embedding)) + "]"
            
            # Semantic search using pgvector
            sql = text("""
                SELECT id, content, memory_type, importance, 
                       embedding <-> (:embedding)::vector as similarity
                FROM memories 
                WHERE user_id = :user_id 
                ORDER BY similarity
                LIMIT :limit
            """)
            
            result = await self.session.execute(sql, {
                "embedding": vec_str,
                "user_id": self.user_id,
                "limit": limit
            })
            
            memories = []
            for row in result:
                memories.append({
                    "id": row[0],
                    "content": row[1],
                    "type": row[2],
                    "importance": row[3],
                    "similarity": row[4]
                })
            
            return memories
            
        except Exception as e:
            logger.error(f"Error retrieving memories: {str(e)}")
            return []

    async def update_memory_access(self, memory_id: int):
        """Update last accessed time for a memory"""
        stmt = select(models.Memory).where(
            models.Memory.id == memory_id,
            models.Memory.user_id == self.user_id
        )
        
        result = await self.session.execute(stmt)
        memory = result.scalar_one_or_none()
        
        if memory:
            memory.last_accessed = datetime.now()
            await self.session.flush()

    async def get_recent_memories(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most recently accessed memories"""
        stmt = select(models.Memory).where(
            models.Memory.user_id == self.user_id
        ).order_by(models.Memory.last_accessed.desc()).limit(limit)
        
        result = await self.session.execute(stmt)
        memories = result.scalars().all()
        
        return [{
            "id": m.id,
            "content": m.content,
            "type": m.memory_type,
            "importance": m.importance,
            "last_accessed": m.last_accessed
        } for m in memories]