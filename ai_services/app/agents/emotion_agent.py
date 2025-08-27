from app.agents.base_agent import BaseAgent
from app.services.emotion_service import emotion_service
from typing import Dict, Any, Optional

class EmotionAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Empathy",
            role="Emotional Intelligence Specialist", 
            expertise=["emotion_analysis", "empathy", "mood_tracking"]
        )
    
    async def process_request(
        self, 
        request: Dict[str, Any], 
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Analyze emotions and provide empathetic guidance"""
        
        user_message = request.get('message', '')
        user_id = request.get('user_id')
        conversation_context = context.get('emotional_context', {})
        
        # Analyze current emotion
        emotion_analysis = await emotion_service.analyze_emotion(
            user_message, conversation_context
        )
        
        # Get appropriate empathy style
        empathy_style = await emotion_service.get_empathy_response_style(
            emotion_analysis['primary_emotion'],
            emotion_analysis['intensity']
        )
        
        # Store emotion pattern
        self.update_memory(f"emotion_pattern_{user_id}", {
            'current_emotion': emotion_analysis['primary_emotion'],
            'intensity': emotion_analysis['intensity'],
            'trend': self._analyze_emotion_trend(user_id, emotion_analysis)
        })
        
        return {
            'agent': self.name,
            'emotion_analysis': emotion_analysis,
            'empathy_guidance': empathy_style,
            'emotional_state': self._assess_emotional_state(emotion_analysis),
            'recommendations': self._get_response_recommendations(emotion_analysis),
            'confidence': emotion_analysis['confidence']
        }
    
    def _analyze_emotion_trend(self, user_id: int, current_analysis: Dict) -> str:
        """Analyze if user's emotional state is improving/declining"""
        previous_emotions = self.get_memory(f"emotion_history_{user_id}") or []
        
        if not previous_emotions:
            return "baseline"
        
        current_sentiment = current_analysis.get('sentiment', {})
        prev_sentiment = previous_emotions[-1].get('sentiment', {}) if previous_emotions else {}
        
        current_positive = current_sentiment.get('positive', 0)
        prev_positive = prev_sentiment.get('positive', 0)
        
        if current_positive > prev_positive + 0.2:
            return "improving"
        elif current_positive < prev_positive - 0.2:
            return "declining"
        else:
            return "stable"
    
    def _assess_emotional_state(self, analysis: Dict) -> str:
        """Assess overall emotional state"""
        primary_emotion = analysis['primary_emotion']
        intensity = analysis['intensity']
        
        if primary_emotion in ['sad', 'angry', 'anxious'] and intensity > 0.7:
            return "needs_support"
        elif primary_emotion == 'happy' and intensity > 0.6:
            return "positive"
        elif primary_emotion == 'confused':
            return "needs_clarity"
        else:
            return "stable"
    
    def _get_response_recommendations(self, analysis: Dict) -> Dict[str, Any]:
        """Get recommendations for how to respond"""
        emotion = analysis['primary_emotion']
        intensity = analysis['intensity']
        
        recommendations = {
            'tone': 'neutral',
            'pace': 'normal',
            'support_level': 'standard',
            'follow_up': False
        }
        
        if emotion == 'sad':
            recommendations.update({
                'tone': 'gentle',
                'pace': 'slower',
                'support_level': 'high',
                'follow_up': intensity > 0.6
            })
        elif emotion == 'angry':
            recommendations.update({
                'tone': 'calm',
                'pace': 'patient',
                'support_level': 'de-escalating',
                'follow_up': True
            })
        elif emotion == 'anxious':
            recommendations.update({
                'tone': 'reassuring',
                'pace': 'steady',
                'support_level': 'calming',
                'follow_up': intensity > 0.5
            })
        elif emotion == 'happy':
            recommendations.update({
                'tone': 'warm',
                'pace': 'energetic',
                'support_level': 'encouraging'
            })
        
        return recommendations