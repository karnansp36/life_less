from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List, Optional, Set
import asyncio
import json
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class SocketManager:
    def __init__(self):
        # Structure: {user_id: {session_id: websocket}}
        self.active_connections: Dict[int, Dict[str, WebSocket]] = {}
        # Track user online status
        self.online_users: Set[int] = set()
        # Message queue for offline users
        self.offline_message_queue: Dict[int, List[Dict]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: int, session_id: str):
        """Handle new WebSocket connection"""
        await websocket.accept()
        
        # Add to connections
        if user_id not in self.active_connections:
            self.active_connections[user_id] = {}
        
        self.active_connections[user_id][session_id] = websocket
        self.online_users.add(user_id)
        
        # Send queued messages if any
        await self._send_queued_messages(user_id, websocket)
        
        logger.info(f"User {user_id} connected with session {session_id}")
    
    def disconnect(self, websocket: WebSocket, user_id: int, session_id: str):
        """Handle WebSocket disconnection"""
        if user_id in self.active_connections:
            if session_id in self.active_connections[user_id]:
                del self.active_connections[user_id][session_id]
            
            # If no more sessions, mark user offline
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
                self.online_users.discard(user_id)
        
        logger.info(f"User {user_id} disconnected from session {session_id}")
    
    async def send_personal_message(
        self, 
        message: str, 
        websocket: WebSocket,
        message_type: str = "chat",
        metadata: Optional[Dict] = None
    ):
        """Send message to specific WebSocket"""
        try:
            message_data = {
                "type": message_type,
                "content": message,
                "timestamp": datetime.now().isoformat(),
                "metadata": metadata or {}
            }
            
            await websocket.send_text(json.dumps(message_data))
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
    
    async def broadcast_to_user(
        self, 
        user_id: int, 
        message: str,
        message_type: str = "chat",
        metadata: Optional[Dict] = None
    ):
        """Send message to all sessions of a user"""
        if user_id in self.active_connections:
            for websocket in self.active_connections[user_id].values():
                await self.send_personal_message(message, websocket, message_type, metadata)
        else:
            # Queue message for when user comes online
            self._queue_offline_message(user_id, message, message_type, metadata)
    
    async def send_proactive_message(
        self, 
        user_id: int, 
        message: str,
        context: Optional[Dict] = None
    ):
        """Send proactive message with special handling"""
        metadata = {
            "proactive": True,
            "context": context or {},
            "can_dismiss": True
        }
        
        await self.broadcast_to_user(
            user_id, 
            message, 
            message_type="proactive", 
            metadata=metadata
        )
    
    def is_user_online(self, user_id: int) -> bool:
        """Check if user is currently online"""
        return user_id in self.online_users
    
    def get_online_users(self) -> List[int]:
        """Get list of currently online users"""
        return list(self.online_users)
    
    def get_user_session_count(self, user_id: int) -> int:
        """Get number of active sessions for a user"""
        return len(self.active_connections.get(user_id, {}))
    
    def _queue_offline_message(
        self, 
        user_id: int, 
        message: str, 
        message_type: str,
        metadata: Optional[Dict]
    ):
        """Queue message for offline user"""
        if user_id not in self.offline_message_queue:
            self.offline_message_queue[user_id] = []
        
        self.offline_message_queue[user_id].append({
            "content": message,
            "type": message_type,
            "metadata": metadata or {},
            "queued_at": datetime.now().isoformat()
        })
        
        # Keep only last 10 messages per user
        self.offline_message_queue[user_id] = self.offline_message_queue[user_id][-10:]
    
    async def _send_queued_messages(self, user_id: int, websocket: WebSocket):
        """Send queued messages when user comes online"""
        if user_id in self.offline_message_queue:
            queued_messages = self.offline_message_queue[user_id]
            
            for msg_data in queued_messages:
                await self.send_personal_message(
                    msg_data["content"],
                    websocket,
                    msg_data["type"],
                    {**msg_data["metadata"], "was_queued": True}
                )
            
            # Clear queue after sending
            del self.offline_message_queue[user_id]
    
    async def send_typing_indicator(self, user_id: int, is_typing: bool = True):
        """Send typing indicator to user"""
        await self.broadcast_to_user(
            user_id,
            "",
            message_type="typing",
            metadata={"is_typing": is_typing}
        )

# Global socket manager instance
socket_manager = SocketManager()