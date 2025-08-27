from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, Optional
import asyncio
import json
import logging

from app.core.dependencies import get_current_user, get_async_db
from app.models.schemas import ChatRequest, ChatResponse
from app.services.socket_manager import socket_manager
from app.services.persona_service import persona_service
from app.services.memory_service import memory_service
from app.services.emotion_service import emotion_service
from app.services.proactive_service import proactive_service
from app.agents.crew_coordinator import crew_coordinator

logger = logging.getLogger(__name__)
router = APIRouter()

@router.websocket("/ws/chat/{user_id}/{session_id}")
async def websocket_endpoint(
    websocket: WebSocket, 
    user_id: int, 
    session_id: str
):
    """Enhanced WebSocket endpoint with full AI crew coordination"""
    
    await socket_manager.connect(websocket, user_id, session_id)
    
    # Start proactive monitoring for this user
    await proactive_service.start_proactive_monitoring(user_id)
    
    try:
        # Create a new async database session for this WebSocket connection
        from app.core.database import AsyncSessionLocal
        
        async with AsyncSessionLocal() as async_db:
            try:
                # Get or create conversation using async session
                conversation = await memory_service.get_or_create_conversation(
                    async_db, user_id, session_id
                )
                
                # Get persona settings
                persona_settings = await persona_service.get_persona_settings(async_db, user_id)
                
                # Send welcome message if new conversation
                if len(conversation.messages) == 0:
                    welcome_msg = persona_service.generate_welcome_message(persona_settings)
                    await socket_manager.send_personal_message(
                        welcome_msg, websocket, "welcome",
                        {"persona": persona_settings.ai_name}
                    )
                
                while True:
                    try:
                        # Receive message from client
                        data = await websocket.receive_text()
                        
                        # Parse message data
                        try:
                            message_data = json.loads(data)
                            user_message = message_data.get('message', data)
                            message_type = message_data.get('type', 'chat')
                        except json.JSONDecodeError:
                            user_message = data
                            message_type = 'chat'
                        
                        # Handle different message types
                        if message_type == 'typing':
                            continue
                        elif message_type == 'heartbeat':
                            await websocket.send_text(json.dumps({"type": "heartbeat_ack"}))
                            continue
                        
                        # Send typing indicator
                        await socket_manager.send_typing_indicator(user_id, True)
                        
                        # Store user message
                        user_msg_record = await memory_service.store_message(
                            async_db, conversation.id, "user", user_message
                        )
                        
                        # Process with AI crew using async session
                        crew_response = await crew_coordinator.process_user_interaction(
                            user_message=user_message,
                            user_id=user_id,
                            conversation_id=conversation.id,
                            persona_settings=persona_settings,
                            db_session=async_db
                        )
                        
                        # Store AI response
                        ai_msg_record = await memory_service.store_message(
                            async_db, 
                            conversation.id, 
                            "assistant", 
                            crew_response['content'],
                            emotion_score=crew_response.get('emotion_insights'),
                            metadata=crew_response.get('metadata', {})
                        )
                        
                        # Commit the transaction
                        await async_db.commit()
                        
                        # Stop typing indicator
                        await socket_manager.send_typing_indicator(user_id, False)
                        
                        # Send response back to client
                        response_metadata = {
                            "message_id": ai_msg_record.id,
                            "agent_coordination": crew_response.get('agent_coordination', {}),
                            "emotion_adapted": crew_response.get('emotion_insights', {}).get('empathy_applied', False),
                            "processing_time": crew_response.get('metadata', {}).get('processing_time', 0)
                        }
                        
                        await socket_manager.send_personal_message(
                            crew_response['content'], 
                            websocket, 
                            "chat_response",
                            response_metadata
                        )
                        
                        # Trigger proactive analysis
                        await proactive_service.handle_user_activity(
                            user_id, 
                            "message_sent", 
                            {
                                "message": user_message,
                                "response": crew_response['content'],
                                "emotion": crew_response.get('emotion_insights', {}).get('detected_emotion', 'neutral')
                            }
                        )
                        
                    except WebSocketDisconnect:
                        break
                    except Exception as e:
                        logger.error(f"Error processing message: {e}")
                        await async_db.rollback()
                        await socket_manager.send_personal_message(
                            "I apologize, but I encountered an error processing your message. Please try again.",
                            websocket,
                            "error",
                            {"error": str(e)}
                        )
            except Exception as e:
                logger.error(f"Error in WebSocket processing: {e}")
                await async_db.rollback()
                    
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
    finally:
        socket_manager.disconnect(websocket, user_id, session_id)
        await proactive_service.stop_proactive_monitoring(user_id)

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    current_user: Optional[Dict] = Depends(get_current_user)
):
    """HTTP chat endpoint for non-WebSocket clients - fully async"""
    
    try:
        logger.info(f"Received chat request for user {request.user_id}")
        
        # Use async database session
        from app.core.database import AsyncSessionLocal
        
        async with AsyncSessionLocal() as db:
            # Get or create conversation
            conversation = await memory_service.get_or_create_conversation(
                db, request.user_id, request.session_id
            )
            
            # Get persona settings
            try:
                persona_settings = await persona_service.get_persona_settings(db, request.user_id)
            except Exception as e:
                logger.error(f"Error getting persona settings: {e}")
                # Create default persona settings if none exist
                persona_settings = await persona_service.create_default_persona_settings(db, request.user_id)
            
            # Store user message
            user_msg_record = await memory_service.store_message(
                db, conversation.id, "user", request.message
            )
            
            # Process with AI crew
            crew_response = await crew_coordinator.process_user_interaction(
                user_message=request.message,
                user_id=request.user_id,
                conversation_id=conversation.id,
                persona_settings=persona_settings,
                db_session=db
            )
            
            # Store AI response
            ai_msg_record = await memory_service.store_message(
                db, 
                conversation.id, 
                "assistant", 
                crew_response['content'],
                emotion_score=crew_response.get('emotion_insights'),
                metadata=crew_response.get('metadata', {})
            )
            
            # Commit transaction
            await db.commit()
            
            # Return proper ChatResponse object
            return ChatResponse(
                response=crew_response['content'],
                conversation_id=conversation.id,
                message_id=ai_msg_record.id,
                metadata=crew_response.get('metadata', {}),
                agent_insights=crew_response.get('agent_coordination', {})
            )
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/chat/status")
async def get_chat_status():
    """Get system status and metrics"""
    
    try:
        # Get agent status safely
        try:
            agent_status = await crew_coordinator.get_agent_status()
        except Exception as e:
            logger.error(f"Error getting agent status: {e}")
            agent_status = {"error": "Agent status unavailable"}
        
        # Get socket manager stats safely
        try:
            online_users = len(socket_manager.get_online_users())
            active_connections = sum(
                socket_manager.get_user_session_count(user_id) 
                for user_id in socket_manager.get_online_users()
            )
        except Exception as e:
            logger.error(f"Error getting socket stats: {e}")
            online_users = 0
            active_connections = 0
        
        return JSONResponse({
            "status": "operational",
            "online_users": online_users,
            "active_connections": active_connections,
            "agents": agent_status,
            "features": {
                "proactive_chat": True,
                "emotion_intelligence": True,
                "multi_agent_coordination": True,
                "vector_memory": True
            }
        })
        
    except Exception as e:
        logger.error(f"Error in chat status endpoint: {e}")
        return JSONResponse(
            {"status": "error", "message": str(e)}, 
            status_code=500
        )