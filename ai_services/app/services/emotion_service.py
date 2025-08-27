from typing import Dict, Any, List, Optional
import re
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.database import EmotionalProfile, Message, Conversation
import json

class EmotionService:
    def __init__(self):
        self.emotion_patterns = {
            'happy': ['happy', 'joy', 'excited', 'great', 'awesome', 'wonderful', 'fantastic', 'love', 'amazing'],
            'sad': ['sad', 'down', 'depressed', 'upset', 'crying', 'hurt', 'disappointed', 'blue'],
            'angry': ['angry', 'mad', 'furious', 'pissed', 'annoyed', 'frustrated', 'rage'],
            'anxious': ['anxious', 'worried', 'nervous', 'scared', 'afraid', 'panic', 'stress'],
            'confused': ['confused', 'lost', 'unclear', 'puzzled', 'bewildered'],
            'grateful': ['thanks', 'grateful', 'appreciate', 'thankful', 'blessed'],
            'lonely': ['lonely', 'alone', 'isolated', 'abandoned', 'solo']
        }
    
    async def analyze_emotion(self, text: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Analyze emotion from text with context awareness"""
        text_lower = text.lower()
        emotion_scores = {}
        
        for emotion, patterns in self.emotion_patterns.items():
            score = sum(1 for pattern in patterns if pattern in text_lower)
            if score > 0:
                emotion_scores[emotion] = min(score / len(patterns), 1.0)
        
        if context:
            emotion_scores = self._adjust_for_context(emotion_scores, context)
        
        primary_emotion = max(emotion_scores, key=emotion_scores.get) if emotion_scores else 'neutral'
        confidence = emotion_scores.get(primary_emotion, 0.0)
        
        sentiment = self._calculate_sentiment(emotion_scores)
        
        return {
            'primary_emotion': primary_emotion,
            'confidence': confidence,
            'all_emotions': emotion_scores,
            'sentiment': sentiment,
            'intensity': self._calculate_intensity(text, emotion_scores),
            'analysis_timestamp': datetime.now().isoformat()
        }
    
    def _adjust_for_context(self, scores: Dict[str, float], context: Dict) -> Dict[str, float]:
        recent_emotions = context.get('recent_emotions', [])
        if recent_emotions:
            last_emotion = recent_emotions[0] if recent_emotions else {}
            last_primary = last_emotion.get('primary_emotion', 'neutral')
            
            if last_primary in scores:
                scores[last_primary] = min(scores[last_primary] + 0.2, 1.0)
            elif not scores and last_primary != 'neutral':
                scores[last_primary] = 0.3
        
        return scores
    
    def _calculate_sentiment(self, emotion_scores: Dict[str, float]) -> Dict[str, float]:
        positive_emotions = ['happy', 'grateful', 'excited']
        negative_emotions = ['sad', 'angry', 'anxious', 'lonely']
        
        positive_score = sum(emotion_scores.get(emotion, 0) for emotion in positive_emotions)
        negative_score = sum(emotion_scores.get(emotion, 0) for emotion in negative_emotions)
        neutral_score = max(0, 1 - positive_score - negative_score)
        
        return {
            'positive': positive_score,
            'negative': negative_score,
            'neutral': neutral_score
        }
    
    def _calculate_intensity(self, text: str, emotion_scores: Dict[str, float]) -> float:
        intensity_factors = 0.0
        
        intensity_factors += min(text.count('!') * 0.1, 0.3)
        
        caps_ratio = sum(1 for c in text if c.isupper()) / len(text) if text else 0
        intensity_factors += min(caps_ratio * 0.5, 0.2)
        
        intensity_factors += min(text.count('?') * 0.05, 0.15)
        
        strong_words = ['extremely', 'very', 'really', 'so', 'totally', 'absolutely']
        strong_word_count = sum(1 for word in strong_words if word in text.lower())
        intensity_factors += min(strong_word_count * 0.1, 0.2)
        
        base_intensity = max(emotion_scores.values()) if emotion_scores else 0.0
        
        return min(base_intensity + intensity_factors, 1.0)
    
    async def update_emotional_profile(
        self, db: AsyncSession, user_id: int, emotion_analysis: Dict[str, Any]
    ):
        """Update user's emotional profile with new data"""
        result = await db.execute(
            select(EmotionalProfile).filter(EmotionalProfile.user_id == user_id)
        )
        profile = result.scalars().first()
        
        if not profile:
            profile = EmotionalProfile(user_id=user_id)
            db.add(profile)
        
        profile.current_mood = emotion_analysis['primary_emotion']
        
        mood_history = profile.mood_history or []
        mood_entry = {
            'emotion': emotion_analysis['primary_emotion'],
            'intensity': emotion_analysis['intensity'],
            'timestamp': datetime.now().isoformat()
        }
        mood_history.append(mood_entry)
        profile.mood_history = mood_history[-100:]
        
        patterns = profile.emotional_patterns or {}
        emotion = emotion_analysis['primary_emotion']
        patterns[emotion] = patterns.get(emotion, 0) + 1
        profile.emotional_patterns = patterns
        
        profile.last_updated = datetime.now()
        await db.commit()
    
    async def get_empathy_response_style(
        self, user_emotion: str, intensity: float
    ) -> Dict[str, str]:
        """Get appropriate response style based on user emotion"""
        empathy_styles = {
            'sad': {
                'tone': 'gentle and supportive',
                'approach': 'acknowledge feelings, offer comfort, be patient',
                'avoid': 'being overly cheerful, dismissing feelings'
            },
            'angry': {
                'tone': 'calm and understanding',
                'approach': 'validate feelings, de-escalate, find solutions',
                'avoid': 'being confrontational, dismissing anger'
            },
            'anxious': {
                'tone': 'reassuring and steady',
                'approach': 'provide reassurance, break down problems, be calming',
                'avoid': 'adding pressure, being rushed'
            },
            'happy': {
                'tone': 'warm and engaging',
                'approach': 'share in joy, be encouraging, maintain positive energy',
                'avoid': 'being dampening, overly serious'
            },
            'confused': {
                'tone': 'clear and helpful',
                'approach': 'clarify, provide structure, be patient with explanations',
                'avoid': 'being complex, overwhelming with information'
            },
            'lonely': {
                'tone': 'warm and present',
                'approach': 'be engaging, show interest, create connection',
                'avoid': 'being distant, rushing conversations'
            }
        }
        
        base_style = empathy_styles.get(user_emotion, {
            'tone': 'balanced and helpful',
            'approach': 'be responsive to user needs',
            'avoid': 'being insensitive'
        })
        
        if intensity > 0.7:
            base_style['intensity_note'] = 'User emotion is intense - be extra careful and supportive'
        
        return base_style

# Global instance
emotion_service = EmotionService()