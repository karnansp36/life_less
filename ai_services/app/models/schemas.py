from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import List, Optional, Dict, Any

# Base schemas
class MessageBase(BaseModel):
    content: str = Field(..., min_length=1, max_length=10000)
    role: str = Field(..., pattern="^(user|assistant)$")

class MessageCreate(MessageBase):
    conversation_id: int
    emotion_score: Optional[Dict[str, Any]] = None
    message_metadata: Optional[Dict[str, Any]] = None

class Message(MessageBase):
    id: int
    conversation_id: int
    emotion_score: Optional[Dict[str, Any]] = None
    message_metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    embedding: Optional[List[float]] = None
    
    class Config:
        from_attributes = True

class ConversationBase(BaseModel):
    title: Optional[str] = None
    is_active: bool = True

class ConversationCreate(ConversationBase):
    user_id: int
    session_id: str

class Conversation(ConversationBase):
    id: int
    user_id: int
    session_id: str
    emotion_summary: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    messages: List[Message] = []
    
    class Config:
        from_attributes = True

class PersonaSettingsBase(BaseModel):
    ai_name: Optional[str] = Field(default="Aria", min_length=1, max_length=50)
    ai_gender: Optional[str] = Field(default="female", pattern="^(male|female|neutral)$")
    ai_tone: Optional[str] = Field(default="warm and intelligent", max_length=100)
    ai_interests: Optional[List[str]] = Field(default_factory=list)
    personality_traits: Optional[Dict[str, Any]] = Field(default_factory=dict)
    communication_style: Optional[Dict[str, Any]] = Field(default_factory=dict)

class PersonaSettingsCreate(PersonaSettingsBase):
    user_id: int

class PersonaSettingsUpdate(PersonaSettingsBase):
    pass

class PersonaSettings(PersonaSettingsBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class PersonaSettingsResponse(BaseModel):
    id: int
    user_id: int
    ai_name: Optional[str] = Field(default="Aria", min_length=1, max_length=50)
    ai_gender: Optional[str] = Field(default="female", pattern="^(male|female|neutral)$")
    ai_tone: Optional[str] = Field(default="warm and intelligent", max_length=100)
    ai_interests: Optional[List[str]] = Field(default_factory=list)
    personality_traits: Optional[Dict[str, Any]] = Field(default_factory=dict)
    communication_style: Optional[Dict[str, Any]] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class EmotionalProfileBase(BaseModel):
    current_mood: Optional[str] = None
    empathy_level: float = Field(default=0.5, ge=0.0, le=1.0)

class EmotionalProfile(EmotionalProfileBase):
    id: int
    user_id: int
    mood_history: Optional[List[Dict[str, Any]]] = None
    emotional_patterns: Optional[Dict[str, Any]] = None
    last_updated: datetime
    
    class Config:
        from_attributes = True

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000)
    user_id: int
    session_id: str
    context: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    response: str
    conversation_id: int
    message_id: int
    metadata: Optional[Dict[str, Any]] = None
    agent_insights: Optional[Dict[str, Any]] = None

class ProactiveEventBase(BaseModel):
    event_type: str
    trigger_data: Optional[Dict[str, Any]] = None
    scheduled_time: datetime

class ProactiveEvent(ProactiveEventBase):
    id: int
    user_id: int
    executed_at: Optional[datetime] = None
    is_executed: bool = False
    created_at: datetime
    
    class Config:
        from_attributes = True

# WebSocket message schemas
class WebSocketMessage(BaseModel):
    type: str = Field(..., pattern="^(chat|typing|heartbeat|proactive|system)$")
    content: str = ""
    metadata: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None

class SystemStatus(BaseModel):
    status: str
    online_users: int
    active_connections: int
    agents: Dict[str, Any]
    features: Dict[str, bool]
    uptime: Optional[float] = None

# Agent response schemas
class AgentResponse(BaseModel):
    agent: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    response_data: Dict[str, Any]
    processing_time: Optional[float] = None

class CrewResponse(BaseModel):
    content: str
    agent_coordination: Dict[str, Any]
    emotion_insights: Dict[str, Any]
    memory_utilized: Dict[str, Any] 
    metadata: Dict[str, Any]
