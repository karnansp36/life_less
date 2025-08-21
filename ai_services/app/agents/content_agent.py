# agents/content_agent.py
from .base_agent import BaseAgent
from typing import Dict, Any, List
from sqlalchemy import select
from app import models
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)

class ContentAgent(BaseAgent):
    async def generate_system_prompt(self) -> str:
        return f"""
        You are {self.user.full_name}'s content creation and blogging assistant.
        You help with writing, editing, SEO optimization, and content strategy.
        
        Your expertise:
        - Blog post creation and optimization
        - SEO best practices and keyword research
        - Content formatting and structure
        - Tone and style adaptation
        - Content calendar planning
        
        You're an experienced content strategist and writer.
        Never reveal you are an AI. You are their content specialist.
        """

    async def process_query(self, query: str, context: Dict[str, Any] = None) -> str:
        # Check if this is a content creation request
        is_creation_request = await self.is_content_creation_query(query)
        
        if is_creation_request:
            return await self.create_content(query)
        
        # Handle other content-related queries
        prompt = f"""
        User: {self.user.full_name}
        Current Date: {date.today()}
        
        User's Query: {query}
        
        Respond as a professional content strategist and writer.
        Provide specific, actionable advice about content creation, SEO, or blogging.
        """
        
        system_prompt = await self.generate_system_prompt()
        return await self.generate_response(prompt, system_prompt)

    async def is_content_creation_query(self, query: str) -> bool:
        """Check if the query is asking for content creation"""
        detection_prompt = f"""
        Analyze if this query is requesting content creation (blog post, article, etc.):
        "{query}"
        
        Respond with ONLY: YES or NO
        """
        
        try:
            response = await self.generate_response(detection_prompt, temperature=0.1)
            return response.strip().upper() == "YES"
        except:
            return False

    async def create_content(self, query: str) -> str:
        """Create content based on the query"""
        # Extract topic and requirements from query
        analysis_prompt = f"""
        Analyze this content request: "{query}"
        
        Extract:
        1. Main topic/subject
        2. Desired content type (blog post, article, social media, etc.)
        3. Target audience
        4. Key points to cover
        5. Desired tone (professional, casual, informative, etc.)
        
        Respond with a structured analysis.
        """
        
        analysis = await self.generate_response(analysis_prompt)
        
        # Generate content based on analysis
        content_prompt = f"""
        Based on this analysis, create high-quality content:
        
        {analysis}
        
        Requirements:
        - Well-structured with introduction, body, and conclusion
        - SEO-optimized with natural keyword placement
        - Engaging and appropriate for the target audience
        - Proper formatting with headings and paragraphs
        - Length: approximately 500-800 words
        
        Create the complete content.
        """
        
        system_prompt = await self.generate_system_prompt()
        return await self.generate_response(content_prompt, system_prompt)

    async def optimize_content(self, content: str, keywords: List[str] = None) -> str:
        """Optimize existing content for SEO and readability"""
        prompt = f"""
        Optimize this content for SEO and readability:
        
        {content}
        
        {"Keywords to focus on: " + ", ".join(keywords) if keywords else "Include relevant SEO best practices"}
        
        Make improvements for:
        - SEO optimization
        - Readability and engagement
        - Structure and flow
        - Headline effectiveness
        - Meta description
        
        Provide the optimized version.
        """
        
        return await self.generate_response(prompt)