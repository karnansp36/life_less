from app.agents.base_agent import BaseAgent
from app.services.memory_service import memory_service
from typing import Dict, Any, Optional

class MemoryAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Memory",
            role="Conversation Memory Specialist",
            expertise=["context_retrieval", "pattern_recognition", "user_modeling"]
        )
    
    async def process_request(
        self, 
        request: Dict[str, Any], 
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Handle memory retrieval and context building"""
        
        user_id = request.get('user_id')
        conversation_id = request.get('conversation_id')
        current_message = request.get('message', '')
        db_session = context.get('db_session')
        
        # Get conversation context
        conversation_context = await memory_service.get_conversation_context(
            db_session, user_id, conversation_id, current_message
        )
        
        # Identify conversation patterns
        patterns = await self._identify_patterns(conversation_context, user_id)
        
        # Build user model insights
        user_insights = await self._build_user_insights(
            conversation_context, user_id, patterns
        )
        
        # Update agent memory with patterns
        self.update_memory(f"user_patterns_{user_id}", patterns)
        self.update_memory(f"user_insights_{user_id}", user_insights)
        
        return {
            'agent': self.name,
            'context': conversation_context,
            'patterns': patterns,
            'user_insights': user_insights,
            'memory_quality': self._assess_memory_quality(conversation_context),
            'confidence': 0.85
        }
    
    async def _identify_patterns(
        self, context: Dict[str, Any], user_id: int
    ) -> list[Dict[str, Any]]:
        """Identify conversation and behavioral patterns"""
        patterns = []
        
        # Analyze conversation topics
        recent_messages = context.get('recent_conversation', '')
        if recent_messages:
            topics = self._extract_topics(recent_messages)
            if topics:
                patterns.append({
                    'type': 'topic_preference',
                    'pattern': f"User frequently discusses: {', '.join(topics[:3])}",
                    'confidence': 0.7
                })
        
        # Analyze emotional patterns from context
        emotional_context = context.get('emotional_context', {})
        recent_emotions = emotional_context.get('recent_emotions', [])
        
        if len(recent_emotions) >= 3:
            emotion_pattern = self._analyze_emotion_pattern(recent_emotions)
            if emotion_pattern:
                patterns.append({
                    'type': 'emotional_pattern',
                    'pattern': emotion_pattern,
                    'confidence': 0.6
                })
        
        # Analyze conversation timing patterns
        timing_pattern = self._analyze_timing_patterns(context)
        if timing_pattern:
            patterns.append({
                'type': 'timing_preference',
                'pattern': timing_pattern,
                'confidence': 0.5
            })
        
        return patterns
    
    def _extract_topics(self, conversation_text: str) -> list[str]:
        """Extract main topics from conversation"""
        # Simple keyword extraction - could be enhanced with NLP
        common_topics = {
            'work': ['work', 'job', 'career', 'office', 'boss', 'colleague'],
            'relationships': ['relationship', 'friend', 'family', 'partner', 'dating'],
            'health': ['health', 'doctor', 'exercise', 'diet', 'sleep', 'wellness'],
            'technology': ['computer', 'software', 'app', 'internet', 'phone', 'tech'],
            'entertainment': ['movie', 'music', 'game', 'book', 'show', 'netflix'],
            'learning': ['learn', 'study', 'course', 'education', 'skill', 'training']
        }
        
        text_lower = conversation_text.lower()
        found_topics = []
        
        for topic, keywords in common_topics.items():
            if any(keyword in text_lower for keyword in keywords):
                found_topics.append(topic)
        
        return found_topics
    
    def _analyze_emotion_pattern(self, recent_emotions: list[Dict]) -> Optional[str]:
        """Analyze emotional patterns"""
        if not recent_emotions:
            return None
        
        # Get primary emotions from recent interactions
        primary_emotions = [
            emotion.get('primary_emotion', 'neutral') 
            for emotion in recent_emotions[-5:]  # Last 5 emotions
        ]
        
        # Check for consistent patterns
        if len(set(primary_emotions)) == 1:
            return f"User consistently shows {primary_emotions[0]} emotions"
        
        # Check for mood swings
        positive_emotions = ['happy', 'grateful', 'excited']
        negative_emotions = ['sad', 'angry', 'anxious', 'frustrated']
        
        pos_count = sum(1 for e in primary_emotions if e in positive_emotions)
        neg_count = sum(1 for e in primary_emotions if e in negative_emotions)
        
        if pos_count > 0 and neg_count > 0:
            return "User shows varied emotional states - may need consistent support"
        elif neg_count > pos_count:
            return "User tends toward negative emotions - may benefit from mood lifting"
        elif pos_count > neg_count:
            return "User generally maintains positive emotions"
        
        return None
    
    def _analyze_timing_patterns(self, context: Dict) -> Optional[str]:
        """Analyze when user typically interacts"""
        # This could be enhanced with actual timestamp analysis
        conversation_length = context.get('conversation_length', 0)
        
        if conversation_length > 20:
            return "User engages in long conversations"
        elif conversation_length < 5:
            return "User prefers brief interactions"
        
        return None
    
    async def _build_user_insights(
        self, context: Dict, user_id: int, patterns: list[Dict]
    ) -> Dict[str, Any]:
        """Build comprehensive user insights"""
        insights = {
            'communication_style': 'unknown',
            'preferred_topics': [],
            'emotional_tendency': 'neutral',
            'engagement_level': 'medium',
            'support_needs': []
        }
        
        # Analyze communication style from recent conversation
        recent_conv = context.get('recent_conversation', '')
        if recent_conv:
            message_count = recent_conv.count('user:')
            avg_length = len(recent_conv) / max(message_count, 1)
            
            if avg_length > 100:
                insights['communication_style'] = 'detailed'
            elif avg_length < 30:
                insights['communication_style'] = 'concise'
            else:
                insights['communication_style'] = 'balanced'
        
        # Extract preferred topics from patterns
        topic_patterns = [p for p in patterns if p['type'] == 'topic_preference']
        if topic_patterns:
            insights['preferred_topics'] = topic_patterns[0]['pattern'].split(': ')[1].split(', ')
        
        # Extract emotional tendency
        emotion_patterns = [p for p in patterns if p['type'] == 'emotional_pattern']
        if emotion_patterns:
            pattern_text = emotion_patterns[0]['pattern'].lower()
            if 'negative' in pattern_text:
                insights['emotional_tendency'] = 'needs_support'
            elif 'positive' in pattern_text:
                insights['emotional_tendency'] = 'generally_positive'
            elif 'varied' in pattern_text:
                insights['emotional_tendency'] = 'emotionally_dynamic'
        
        # Determine engagement level
        conversation_length = context.get('conversation_length', 0)
        if conversation_length > 15:
            insights['engagement_level'] = 'high'
        elif conversation_length < 5:
            insights['engagement_level'] = 'low'
        
        return insights
    
    def _assess_memory_quality(self, context: Dict) -> float:
        """Assess quality of retrieved memory context"""
        score = 0.0
        
        # Points for recent conversation context
        if context.get('recent_conversation'):
            score += 0.4
        
        # Points for historical context
        if context.get('relevant_history'):
            score += 0.3
        
        # Points for emotional context
        if context.get('emotional_context'):
            score += 0.2
        
        # Points for conversation length (more context = better quality)
        conv_length = context.get('conversation_length', 0)
        if conv_length > 10:
            score += 0.1
        
        return min(score, 1.0)
