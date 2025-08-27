from app.agents.base_agent import BaseAgent
from app.services.ai_service import ai_service
from app.services.memory_service import memory_service
from typing import Dict, Any, Optional

class ConversationAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Aria",
            role="Primary Conversation Handler",
            expertise=["conversation", "general_chat", "questions", "assistance"]
        )
    
    async def process_request(
        self, 
        request: Dict[str, Any], 
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Handle main conversation flow"""
        
        user_message = request.get('message', '')
        user_id = request.get('user_id')
        conversation_id = request.get('conversation_id')
        persona_settings = request.get('persona_settings', {})
        
        # Get conversation context
        memory_context = context.get('memory_context', {})
        emotion_context = context.get('emotion_context', {})
        
        # Generate response using AI service
        response = await ai_service.generate_response(
            message=user_message,
            context=self._format_context(memory_context),
            persona_settings=persona_settings,
            emotion_context=emotion_context
        )
        
        # Update memory with successful interaction
        self.update_memory(f"last_interaction_{user_id}", {
            'message': user_message,
            'response': response['content'],
            'satisfaction': 'good'  # Could be enhanced with feedback
        })
        
        return {
            'agent': self.name,
            'response': response['content'],
            'model_used': response.get('model_used', 'unknown'),
            'confidence': 0.9,  # High confidence for general conversation
            'requires_followup': self._analyze_followup_need(user_message),
            'emotion_adapted': response.get('emotion_adapted', False)
        }
        
        if ai_service.gemini is None and response.get('model_used') == 'gemini':
            return {
                'agent': self.name,
                'response': "I am currently experiencing technical difficulties. Please try again later.",
                'model_used': 'fallback',
                'confidence': 0.0,
                'requires_followup': False,
                'emotion_adapted': False
            }
    
    def _format_context(self, memory_context: Dict) -> str:
        """Format memory context for AI prompt"""
        recent = memory_context.get('recent_conversation', '')
        relevant = memory_context.get('relevant_history', '')
        
        context = ""
        if recent:
            context += f"Recent conversation:\n{recent}\n\n"
        if relevant:
            context += f"Relevant past context:\n{relevant}"
        
        return context
    
    def _analyze_followup_need(self, message: str) -> bool:
        """Determine if message might need follow-up later"""
        followup_indicators = [
            'tomorrow', 'later', 'will try', 'planning to', 
            'interview', 'test', 'exam', 'appointment'
        ]
        
        return any(indicator in message.lower() for indicator in followup_indicators)
