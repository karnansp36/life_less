import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.ollama_client import ollama_client

logger = logging.getLogger(__name__)

class ContentService:
    def __init__(self, session: AsyncSession, user):
        self.session = session
        self.user = user

    async def generate_blog_post(self, topic: str, style: str = "informative", 
                               length: str = "medium") -> Dict[str, Any]:
        """Generate a blog post on a given topic"""
        prompt = f"""
        Write a {style} blog post about: {topic}
        
        Requirements:
        - Length: {length} (approximately 500-800 words)
        - Style: {style}
        - Include engaging introduction and conclusion
        - Use appropriate headings and structure
        - Make it informative and valuable for readers
        
        Please provide the complete blog post with proper formatting.
        """
        
        try:
            content = await ollama_client.generate(prompt=prompt, temperature=0.8, max_tokens=2000)
            
            # Generate SEO suggestions
            seo_prompt = f"""
            Analyze this blog post topic and suggest SEO keywords:
            Topic: {topic}
            
            Provide 5-7 relevant SEO keywords and a meta description.
            """
            
            seo_analysis = await ollama_client.generate(prompt=seo_prompt, temperature=0.3)
            
            return {
                "content": content,
                "topic": topic,
                "style": style,
                "seo_suggestions": seo_analysis,
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Error generating blog post: {e}")
            return {
                "status": "error",
                "message": "Failed to generate content"
            }

    async def improve_content(self, content: str, improvements: List[str] = None) -> str:
        """Improve existing content"""
        improvements_text = ", ".join(improvements) if improvements else "clarity, engagement, and structure"
        
        prompt = f"""
        Improve the following content with better {improvements_text}:
        
        {content}
        
        Please provide the improved version while maintaining the original meaning and intent.
        """
        
        try:
            improved = await ollama_client.generate(prompt=prompt, temperature=0.6)
            return improved
        except Exception as e:
            logger.error(f"Error improving content: {e}")
            return content

    async def generate_social_media_post(self, topic: str, platform: str = "twitter") -> str:
        """Generate social media content"""
        prompt = f"""
        Create a {platform} post about: {topic}
        
        Make it engaging, concise, and appropriate for {platform}.
        Include relevant hashtags if appropriate.
        """
        
        try:
            post = await ollama_client.generate(prompt=prompt, temperature=0.7)
            return post
        except Exception as e:
            logger.error(f"Error generating social media post: {e}")
            return f"Engaging post about {topic} for {platform}"

    async def analyze_content_quality(self, content: str) -> Dict[str, Any]:
        """Analyze content quality and provide suggestions"""
        prompt = f"""
        Analyze this content and provide quality feedback:
        
        {content}
        
        Evaluate:
        1. Readability and clarity
        2. Engagement level
        3. Structure and flow
        4. Grammar and style
        5. Overall effectiveness
        
        Provide specific suggestions for improvement.
        """
        
        try:
            analysis = await ollama_client.generate(prompt=prompt, temperature=0.3)
            
            return {
                "analysis": analysis,
                "word_count": len(content.split()),
                "estimated_reading_time": f"{len(content.split()) / 200:.1f} minutes"
            }
        except Exception as e:
            logger.error(f"Error analyzing content: {e}")
            return {
                "analysis": "Unable to analyze content quality at this time.",
                "word_count": len(content.split())
            }