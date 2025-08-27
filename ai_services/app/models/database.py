from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, ForeignKey, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime

# Remove pgvector import for now - we'll store embeddings in Redis instead
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_seen = Column(DateTime(timezone=True))
    
    # Relationships
    conversations = relationship("Conversation", back_populates="user")
    persona_settings = relationship("PersonaSettings", back_populates="user")
    emotional_profile = relationship("EmotionalProfile", back_populates="user")

class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_id = Column(String, index=True, nullable=False)
    title = Column(String)
    is_active = Column(Boolean, default=True)
    emotion_summary = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation")

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    role = Column(String, nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    emotion_score = Column(JSON)
    message_metadata = Column(JSON)
    # Store embedding ID/hash instead of the actual vector
    embedding_id = Column(String)  # Reference to Redis-stored embedding
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")

class PersonaSettings(Base):
    __tablename__ = "persona_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    ai_name = Column(String, default="Aria")
    ai_gender = Column(String, default="female")
    ai_tone = Column(String, default="warm and intelligent")
    ai_interests = Column(JSON, default=list)
    personality_traits = Column(JSON, default=dict)
    communication_style = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="persona_settings")

class EmotionalProfile(Base):
    __tablename__ = "emotional_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    current_mood = Column(String)
    mood_history = Column(JSON, default=list)
    emotional_patterns = Column(JSON, default=dict)
    empathy_level = Column(Float, default=0.5)
    last_updated = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="emotional_profile")

class ProactiveEvent(Base):
    __tablename__ = "proactive_events"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    event_type = Column(String, nullable=False)  # 'check_in', 'follow_up', 'interest_based'
    trigger_data = Column(JSON)
    scheduled_time = Column(DateTime(timezone=True))
    executed_at = Column(DateTime(timezone=True))
    is_executed = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())