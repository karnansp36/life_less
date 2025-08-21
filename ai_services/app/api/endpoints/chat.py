from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Header
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Dict, Any
import json
import logging
import asyncio
from datetime import datetime

from app.database import get_db_session
from app.models import User
from app.services.chat_service import ChatService
from app.utils.security import validate_token
from app.ollama_client import ollama_client

router = APIRouter()
logger = logging.getLogger(__name__)

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    user_id: str  # Provided by main app
    metadata: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    response: str
    conversation_id: Optional[int] = None  # ← Change to int
    agent_used: str
    success: bool
    metadata: Optional[Dict[str, Any]] = None

class ConversationHistoryRequest(BaseModel):
    user_id: str  # Added user_id field
    conversation_id: Optional[str] = None
    limit: Optional[int] = 10

class ConversationHistoryResponse(BaseModel):
    conversation_id: str
    messages: list
    title: str

@router.post("", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """Main chat endpoint for microservice - expects user_id from main app"""
    try:
        # Validate input
        if not request.message or not request.message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        if not request.user_id:
            raise HTTPException(status_code=400, detail="User ID is required")
        
        # Get or create user in our system (linked to main app user)
        user = await get_or_create_user(db, request.user_id)
        
        chat_service = ChatService(db, user)
        result = await chat_service.process_message(
            request.message.strip(), 
            request.conversation_id
        )
        
        return ChatResponse(
            response=result["response"],
            conversation_id=result["conversation_id"],
            agent_used=result["agent_used"],
            success=result["success"],
            metadata={
                "memories_used": result.get("memories_used", 0),
                "processing_time": result.get("processing_time", 0)
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat processing error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.websocket("/ws")
async def websocket_chat(websocket: WebSocket):
    """WebSocket endpoint for real-time chat"""
    await websocket.accept()
    
    try:
        # Authenticate via query parameter
        token = websocket.query_params.get("token")
        if not token:
            await websocket.close(code=1008, reason="Authentication required")
            return
        
        # Validate token and get user ID
        user_payload = validate_token(token)
        user_id = user_payload.get("sub", "unknown")
        
        async with get_db_session() as db:
            user = await get_or_create_user(db, user_id)
            chat_service = ChatService(db, user)
            
            # Send connection established message
            await websocket.send_json({
                "type": "connection_established",
                "message": "WebSocket connection established successfully",
                "timestamp": datetime.utcnow().isoformat()
            })
            
            while True:
                try:
                    # Receive message with timeout
                    data = await asyncio.wait_for(websocket.receive_json(), timeout=300)
                    
                    if data.get("type") == "ping":
                        # Handle ping requests
                        await websocket.send_json({
                            "type": "pong",
                            "timestamp": datetime.utcnow().isoformat()
                        })
                        continue
                    
                    message = data.get("message", "").strip()
                    conversation_id = data.get("conversation_id")
                    
                    if not message:
                        await websocket.send_json({
                            "type": "error",
                            "message": "Empty message received"
                        })
                        continue
                    
                    # Process the message
                    result = await chat_service.process_message(message, conversation_id)
                    
                    # Send response
                    await websocket.send_json({
                        "type": "response",
                        "response": result["response"],
                        "conversation_id": result["conversation_id"],
                        "agent_used": result["agent_used"],
                        "success": result["success"],
                        "timestamp": datetime.utcnow().isoformat(),
                        "metadata": {
                            "memories_used": result.get("memories_used", 0)
                        }
                    })
                    
                except asyncio.TimeoutError:
                    # Send keep-alive ping
                    await websocket.send_json({
                        "type": "ping",
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    
                except Exception as e:
                    logger.error(f"WebSocket message processing error: {e}")
                    await websocket.send_json({
                        "type": "error",
                        "message": "Failed to process message",
                        "error": str(e)
                    })
                    
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
        try:
            await websocket.close(code=1011, reason="Internal server error")
        except:
            pass

@router.post("/conversations")
async def get_conversation_history(
    request: ConversationHistoryRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """Get conversation history for a user"""
    try:
        # Validate input
        if not request.user_id:
            raise HTTPException(status_code=400, detail="User ID is required")
        
        user = await get_or_create_user(db, request.user_id)
        chat_service = ChatService(db, user)
        
        history = await chat_service.get_conversation_history(
            request.conversation_id, 
            request.limit
        )
        
        return ConversationHistoryResponse(**history)
        
    except Exception as e:
        logger.error(f"Error fetching conversation history: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch conversation history")

@router.get("/agents")
async def get_available_agents():
    """Get information about available AI agents"""
    return {
        "agents": [
            {
                "name": "personal_manager",
                "description": "General personal management and emotional support",
                "capabilities": ["daily check-ins", "emotional support", "general advice"]
            },
            {
                "name": "habit",
                "description": "Habit tracking and routine building",
                "capabilities": ["habit formation", "streak tracking", "routine optimization"]
            },
            {
                "name": "finance", 
                "description": "Expense tracking and financial management",
                "capabilities": ["budgeting", "expense analysis", "financial advice"]
            },
            {
                "name": "email",
                "description": "Email management and correspondence",
                "capabilities": ["email triage", "response drafting", "priority sorting"]
            },
            {
                "name": "content",
                "description": "Content creation and writing assistance", 
                "capabilities": ["blog writing", "SEO optimization", "content improvement"]
            },
            {
                "name": "admin",
                "description": "Scheduling and administrative tasks",
                "capabilities": ["calendar management", "task organization", "scheduling"]
            },
            {
                "name": "research",
                "description": "Information gathering and analysis",
                "capabilities": ["research", "summarization", "fact-finding"]
            }
        ],
        "total_agents": 7,
        "default_agent": "personal_manager"
    }

async def get_or_create_user(db: AsyncSession, main_app_user_id: str):
    """Get or create user in our system based on main app user ID"""
    from sqlalchemy import select
    from app.models import User
    
    try:
        # Try to use the ID field instead of main_app_user_id
        user_id = int(main_app_user_id)
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if user:
            return user
        
        # Create new user with the provided ID
        user = User(
            id=user_id,
            email=f"user_{main_app_user_id}@example.com",
            username=f"user_{main_app_user_id}",
            hashed_password="temp_password_placeholder",  # You should hash this properly
            full_name=f"User {main_app_user_id}"
        )
        
    except ValueError:
        # If main_app_user_id is not a valid integer, try using email
        stmt = select(User).where(User.email == main_app_user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if user:
            return user
        
        # Create new user with email as identifier
        user = User(
            email=main_app_user_id,
            username=main_app_user_id.split('@')[0],
            hashed_password="temp_password_placeholder",
            full_name=main_app_user_id.split('@')[0]
        )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    return user