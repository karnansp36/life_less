from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.database import ProactiveEvent, User, Conversation, Message
from app.core.database import get_db
from app.services.ai_service import ai_service
from app.services.socket_manager import socket_manager
import random

class ProactiveService:
    def __init__(self):
        self.active_tasks: Dict[int, asyncio.Task] = {}
        self.check_intervals = {
            'morning_greeting': timedelta(hours=24),
            'follow_up': timedelta(hours=6),
            'check_in': timedelta(hours=4),
            'interest_share': timedelta(hours=12)
        }
    
    async def start_proactive_monitoring(self, user_id: int):
        """Start proactive monitoring for a user"""
        if user_id in self.active_tasks:
            return
        
        task = asyncio.create_task(self._monitor_user_proactively(user_id))
        self.active_tasks[user_id] = task
    
    async def stop_proactive_monitoring(self, user_id: int):
        """Stop proactive monitoring for a user"""
        if user_id in self.active_tasks:
            self.active_tasks[user_id].cancel()
            del self.active_tasks[user_id]
    
    async def _monitor_user_proactively(self, user_id: int):
        """Main proactive monitoring loop for a user"""
        while True:
            try:
                async with get_db() as db:
                    # Check for scheduled events
                    await self._process_scheduled_events(db, user_id)
                    
                    # Check for opportunity to create new proactive events
                    await self._create_proactive_opportunities(db, user_id)
                
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in proactive monitoring for user {user_id}: {e}")
                await asyncio.sleep(60)
    
    async def _process_scheduled_events(self, db: AsyncSession, user_id: int):
        """Process due proactive events"""
        result = await db.execute(
            select(ProactiveEvent).filter(
                ProactiveEvent.user_id == user_id,
                ProactiveEvent.is_executed == False,
                ProactiveEvent.scheduled_time <= datetime.now()
            )
        )
        due_events = result.scalars().all()
        
        for event in due_events:
            await self._execute_proactive_event(db, event)
    
    async def _execute_proactive_event(self, db: AsyncSession, event: ProactiveEvent):
        """Execute a proactive event"""
        try:
            # Check if user is currently online
            if not socket_manager.is_user_online(event.user_id):
                # Reschedule for later if user is offline
                event.scheduled_time = datetime.now() + timedelta(hours=1)
                await db.commit()
                return
            
            # Generate proactive message based on event type
            message = await self._generate_proactive_message(db, event)
            
            if message:
                # Send message through WebSocket
                await socket_manager.send_proactive_message(event.user_id, message)
                
                # Mark as executed
                event.is_executed = True
                event.executed_at = datetime.now()
                await db.commit()
                
        except Exception as e:
            print(f"Failed to execute proactive event {event.id}: {e}")
    
    async def _generate_proactive_message(
        self, db: AsyncSession, event: ProactiveEvent
    ) -> Optional[str]:
        """Generate contextual proactive message"""
        result = await db.execute(select(User).filter(User.id == event.user_id))
        user = result.scalars().first()
        if not user:
            return None
        
        trigger_data = event.trigger_data or {}
        
        messages = {
            'morning_greeting': [
                "Good morning! How are you feeling today?",
                "Morning! I hope you're having a great start to your day!",
                "Hello! Ready to tackle whatever today brings?"
            ],
            'check_in': [
                "Hey, just wanted to check in. How are things going?",
                "Thinking of you! How has your day been?",
                "Hi there! Anything interesting happening today?"
            ],
            'follow_up': self._generate_follow_up_message(trigger_data),
            'interest_based': await self._generate_interest_message(db, event.user_id, trigger_data)
        }
        
        message_options = messages.get(event.event_type, ["Hi! How are you doing?"])
        
        if isinstance(message_options, list):
            return random.choice(message_options)
        return message_options
    
    def _generate_follow_up_message(self, trigger_data: Dict) -> str:
        """Generate follow-up message based on previous conversation"""
        topic = trigger_data.get('topic', 'our conversation')
        return f"I've been thinking about {topic} we discussed. How did that work out for you?"
    
    async def _generate_interest_message(
        self, db: AsyncSession, user_id: int, trigger_data: Dict
    ) -> str:
        """Generate interest-based proactive message"""
        interests = trigger_data.get('interests', [])
        if interests:
            interest = random.choice(interests)
            return f"I came across something interesting about {interest}. Would you like to hear about it?"
        
        return "I found something that might interest you. Want to chat about it?"
    
    async def _create_proactive_opportunities(self, db: AsyncSession, user_id: int):
        """Identify opportunities for proactive engagement"""
        result = await db.execute(select(User).filter(User.id == user_id))
        user = result.scalars().first()
        if not user:
            return
        
        # Check when user was last seen
        if user.last_seen:
            time_since_last = datetime.now() - user.last_seen
            
            # Morning greeting opportunity
            if (time_since_last > timedelta(hours=12) and 
                datetime.now().hour >= 7 and datetime.now().hour <= 10):
                await self._schedule_event(db, user_id, 'morning_greeting', 
                                         datetime.now() + timedelta(minutes=5))
            
            # Check-in opportunity (if user hasn't chatted in a while)
            if time_since_last > timedelta(hours=6):
                await self._schedule_event(db, user_id, 'check_in',
                                         datetime.now() + timedelta(minutes=10))
        
        # Look for follow-up opportunities from recent conversations
        await self._identify_follow_up_opportunities(db, user_id)
    
    async def _identify_follow_up_opportunities(self, db: AsyncSession, user_id: int):
        """Identify conversations that might benefit from follow-up"""
        result = await db.execute(
            select(Conversation).filter(
                Conversation.user_id == user_id,
                Conversation.created_at > datetime.now() - timedelta(days=2)
            )
        )
        recent_conversations = result.scalars().all()
        
        for conv in recent_conversations:
            # Analyze if conversation had important topics
            result = await db.execute(
                select(Message).filter(
                    Message.conversation_id == conv.id,
                    Message.role == 'user'
                )
            )
            important_messages = result.scalars().all()
            
            # Simple keyword analysis for follow-up worthy topics
            follow_up_keywords = ['problem', 'issue', 'worried', 'planning', 'decision', 'interview', 'test', 'exam']
            
            for msg in important_messages:
                if any(keyword in msg.content.lower() for keyword in follow_up_keywords):
                    # Schedule follow-up
                    trigger_data = {
                        'conversation_id': conv.id,
                        'topic': msg.content[:50] + "...",
                        'original_message': msg.content
                    }
                    
                    follow_up_time = datetime.now() + timedelta(hours=random.randint(4, 8))
                    await self._schedule_event(db, user_id, 'follow_up', 
                                             follow_up_time, trigger_data)
                    break
    
    async def _schedule_event(
        self, 
        db: AsyncSession, 
        user_id: int, 
        event_type: str, 
        scheduled_time: datetime,
        trigger_data: Optional[Dict] = None
    ):
        """Schedule a proactive event"""
        # Check if similar event already exists
        result = await db.execute(
            select(ProactiveEvent).filter(
                ProactiveEvent.user_id == user_id,
                ProactiveEvent.event_type == event_type,
                ProactiveEvent.is_executed == False,
                ProactiveEvent.scheduled_time > datetime.now() - timedelta(hours=1)
            )
        )
        existing = result.scalars().first()
        
        if existing:
            return
        
        event = ProactiveEvent(
            user_id=user_id,
            event_type=event_type,
            trigger_data=trigger_data or {},
            scheduled_time=scheduled_time
        )
        
        db.add(event)
        await db.commit()
    
    async def handle_user_activity(self, user_id: int, activity_type: str, data: Dict):
        """Handle user activity for proactive opportunities"""
        async with get_db() as db:
            # Update user last seen
            result = await db.execute(select(User).filter(User.id == user_id))
            user = result.scalars().first()
            if user:
                user.last_seen = datetime.now()
                await db.commit()
            
            # Start monitoring if not already active
            if user_id not in self.active_tasks:
                await self.start_proactive_monitoring(user_id)

# Global instance
proactive_service = ProactiveService()