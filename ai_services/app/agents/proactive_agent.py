from app.agents.base_agent import BaseAgent
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from app.models.database import ProactiveEvent
import asyncio

class ProactiveAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="ProactiveEngager",
            role="Proactive Conversation Management",
            expertise=["proactive_engagement", "scheduling", "follow_up"]
        )
    
    async def process_request(self, request: Dict[str, Any], context: Optional[Dict] = None) -> Dict[str, Any]:
        if request.get('type') == 'proactive_action':
            return await self._handle_proactive_action(request)
        
        # Analyze current conversation for future proactive opportunities
        conversation_response = context.get('conversation_response', {}) if context else {}
        emotion_analysis = context.get('emotion_analysis', {}) if context else {}
        db_session = context.get('db_session') if context else None
        
        events_scheduled = 0
        
        if db_session and request.get('user_id'):
            events_scheduled = await self._schedule_proactive_events(
                request, conversation_response, emotion_analysis, db_session
            )
        
        return {
            'events_scheduled': events_scheduled,
            'recommendations': await self._generate_recommendations(conversation_response),
            'confidence': 0.7
        }
    
    async def _handle_proactive_action(self, request: Dict) -> Dict[str, Any]:
        action_type = request.get('action_type', '')
        context = request.get('context', {})
        
        messages = {
            'morning_greeting': "Good morning! How are you feeling today?",
            'check_in': "Hi there! Just wanted to check in and see how you're doing.",
            'follow_up': f"I was thinking about our conversation about {context.get('topic', 'that topic')}. How did it go?",
            'interest_based': "I found something that might interest you based on our previous conversations!"
        }
        
        return {
            'message': messages.get(action_type, "Hi! Hope you're having a great day!"),
            'action_executed': True
        }
    
    async def _schedule_proactive_events(
        self, request: Dict, conversation_response: Dict, 
        emotion_analysis: Dict, db_session
    ) -> int:
        user_id = request.get('user_id')
        message = request.get('message', '')
        events_created = 0
        
        # Check for follow-up opportunities
        follow_up_keywords = ['tomorrow', 'next week', 'later', 'planning', 'will try', 'interview', 'exam', 'test']
        
        if any(keyword in message.lower() for keyword in follow_up_keywords):
            # Schedule follow-up
            follow_up_time = datetime.now() + timedelta(hours=6)
            event = ProactiveEvent(
                user_id=user_id,
                event_type='follow_up',
                trigger_data={'topic': message[:50], 'original_message': message},
                scheduled_time=follow_up_time
            )
            db_session.add(event)
            events_created += 1
        
        # Check emotional state for check-ins
        primary_emotion = emotion_analysis.get('primary_emotion')
        if primary_emotion in ['sadness', 'anger', 'fear'] and emotion_analysis.get('intensity', 0) > 0.6:
            # Schedule wellness check-in
            checkin_time = datetime.now() + timedelta(hours=2)
            event = ProactiveEvent(
                user_id=user_id,
                event_type='check_in',
                trigger_data={'emotional_context': emotion_analysis},
                scheduled_time=checkin_time
            )
            db_session.add(event)
            events_created += 1
        
        if events_created > 0:
            db_session.commit()
        
        return events_created
    
    async def _generate_recommendations(self, conversation_response: Dict) -> list:
        recommendations = []
        
        # Based on conversation quality
        confidence = conversation_response.get('confidence', 0.0)
        if confidence < 0.5:
            recommendations.append("Consider asking clarifying questions to better understand user needs")
        
        # Based on conversation length
        if conversation_response.get('requires_followup', False):
            recommendations.append("Schedule follow-up conversation to check progress")
        
        return recommendations