from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict
import json
import logging
from datetime import datetime
from sqlalchemy import select, func
from app.models import Message

from app.core.dependencies import verify_api_key
from app.services.memory_service import memory_service
from app.services.persona_service import persona_service
from app.services.proactive_service import proactive_service
from app.services.socket_manager import socket_manager
from app.agents.crew_coordinator import crew_coordinator
from app.models.schemas import ChatRequest, ChatResponse
from app.core.database import AsyncSessionLocal

logger = logging.getLogger(__name__)
router = APIRouter()

# ======================
# WebSocket endpoint (with API Key auth)
# ======================
@router.websocket("/ws/chat/{user_id}/{session_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int, session_id: str):
    from app.core.dependencies import API_SECRET

    # 🔹 API key validation BEFORE connect()
    api_key = websocket.query_params.get("api_key") or websocket.headers.get("x-api-key")
    if not api_key or api_key != API_SECRET:
        await websocket.accept()   # must accept before sending/closing
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": "Invalid or missing API key"
        }))
        await websocket.close(code=1008)
        return

    # 🔹 SocketManager.connect() will accept the connection
    await socket_manager.connect(websocket, user_id, session_id)
    await proactive_service.start_proactive_monitoring(user_id)

    try:
        async with AsyncSessionLocal() as async_db:
            conversation = await memory_service.get_or_create_conversation(
                async_db, user_id, session_id
            )
            persona_settings = await persona_service.get_persona_settings(async_db, user_id)

            count = await async_db.execute(
                        select(func.count(Message.id)).where(Message.conversation_id == conversation.id)
                        )
            message_count = count.scalar_one()

            if message_count == 0:
                welcome_msg = persona_service.generate_welcome_message(persona_settings)
                await socket_manager.send_personal_message(
                        welcome_msg, websocket, "welcome", {"persona": persona_settings.ai_name}
                        )

            # Main loop
            while True:
                try:
                    data = await websocket.receive_text()
                    try:
                        msg_data = json.loads(data)
                        user_message = msg_data.get("message", data)
                        message_type = msg_data.get("type", "chat")
                    except:
                        user_message = data
                        message_type = "chat"

                    if message_type in ["typing", "heartbeat"]:
                        if message_type == "heartbeat":
                            await websocket.send_text(json.dumps({"type": "heartbeat_ack"}))
                        continue

                    await socket_manager.send_typing_indicator(user_id, True)

                    await memory_service.store_message(async_db, conversation.id, "user", user_message)
                    crew_response = await crew_coordinator.process_user_interaction(
                        user_message, user_id, conversation.id, persona_settings, async_db
                    )
                    await memory_service.store_message(
                        async_db, conversation.id, "assistant", crew_response["content"],
                        emotion_score=crew_response.get("emotion_insights"),
                        metadata=crew_response.get("metadata", {})
                    )
                    await async_db.commit()
                    await socket_manager.send_typing_indicator(user_id, False)

                    await socket_manager.send_personal_message(
                        crew_response["content"], websocket, "chat_response",
                        {"agent_coordination": crew_response.get("agent_coordination", {})}
                    )
                except WebSocketDisconnect:
                    break
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    await async_db.rollback()
                    await socket_manager.send_personal_message(
                        "Error processing message.", websocket, "error", {"error": str(e)}
                    )
    finally:
        socket_manager.disconnect(websocket, user_id, session_id)
        await proactive_service.stop_proactive_monitoring(user_id)



# ======================
# REST endpoint
# ======================
@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest, _: Dict = Depends(verify_api_key)):
    try:
        async with AsyncSessionLocal() as db:
            conversation = await memory_service.get_or_create_conversation(
                db, request.user_id, request.session_id
            )
            persona_settings = await persona_service.get_persona_settings(db, request.user_id)
            await memory_service.store_message(db, conversation.id, "user", request.message)

            crew_response = await crew_coordinator.process_user_interaction(
                request.message, request.user_id, conversation.id, persona_settings, db
            )

            ai_msg_record = await memory_service.store_message(
                db, conversation.id, "assistant", crew_response['content'],
                emotion_score=crew_response.get('emotion_insights'),
                metadata=crew_response.get('metadata', {})
            )
            await db.commit()

            return ChatResponse(
                response=crew_response['content'],
                conversation_id=conversation.id,
                message_id=ai_msg_record.id,
                metadata=crew_response.get('metadata', {}),
                agent_insights=crew_response.get('agent_coordination', {})
            )
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# 🔹 Status Endpoint (secured via API key)
# ============================================================
@router.get("/chat/status")
async def get_chat_status(_: Dict = Depends(verify_api_key)):
    """Get system status and metrics - secured with API key"""
    
    try:
        try:
            agent_status = await crew_coordinator.get_agent_status()
        except Exception as e:
            logger.error(f"Error getting agent status: {e}")
            agent_status = {"error": "Agent status unavailable"}
        
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
