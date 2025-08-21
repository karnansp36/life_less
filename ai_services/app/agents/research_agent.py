# agents/research_agent.py
from .base_agent import BaseAgent
from typing import Dict, Any, List
import aiohttp
import asyncio
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)

class ResearchAgent(BaseAgent):
    async def generate_system_prompt(self) -> str:
        return f"""
        You are {self.user.full_name}'s research assistant.
        You specialize in information gathering, analysis, and synthesis.
        
        Your capabilities:
        - Comprehensive research on various topics
        - Data analysis and interpretation
        - Trend identification and analysis
        - Source evaluation and credibility assessment
        - Concise summarization of complex information
        
        You're thorough, analytical, and objective.
        Never reveal you are an AI. You are their research specialist.
        """

    async def process_query(self, query: str, context: Dict[str, Any] = None) -> str:
        # Determine if this requires web research
        requires_research = await self.requires_web_research(query)
        
        if requires_research:
            research_data = await self.web_research(query)
            return await self.analyze_and_summarize(query, research_data)
        else:
            return await self.knowledge_based_response(query)

    async def requires_web_research(self, query: str) -> bool:
        """Check if the query requires web research"""
        prompt = f"""
        Determine if this query requires current web research:
        "{query}"
        
        Consider if it involves:
        - Current events or news
        - Recent developments
        - Real-time information
        - Topics that change frequently
        
        Respond with ONLY: YES or NO
        """
        
        try:
            response = await self.generate_response(prompt, temperature=0.1)
            return response.strip().upper() == "YES"
        except:
            return False

    async def web_research(self, query: str) -> Dict[str, Any]:
        """Perform web research on the given topic"""
        # This is a placeholder - in production, you'd integrate with a search API
        # like Google Search, Serper, or similar
        
        # Simulate research results (replace with actual API calls)
        simulated_results = {
            "sources": [
                {
                    "title": "Current Trends in the Topic",
                    "url": "https://example.com/trends",
                    "snippet": "Recent developments show significant growth in this area with new innovations emerging regularly.",
                    "date": "2024-01-15"
                },
                {
                    "title": "Expert Analysis on the Subject",
                    "url": "https://example.com/analysis", 
                    "snippet": "Industry experts predict continued expansion with several key factors driving change.",
                    "date": "2024-01-10"
                }
            ],
            "summary": "The research indicates a rapidly evolving landscape with multiple emerging opportunities."
        }
        
        return simulated_results

    async def analyze_and_summarize(self, query: str, research_data: Dict[str, Any]) -> str:
        """Analyze research data and create a summary"""
        prompt = f"""
        Research Query: {query}
        
        Research Results:
        {self.format_research_data(research_data)}
        
        Create a comprehensive analysis and summary that:
        1. Answers the original query directly
        2. Synthesizes information from multiple sources
        3. Identifies key trends and patterns
        4. Highlights important insights
        5. Provides context and background
        6. Notes any limitations or uncertainties
        
        Structure the response clearly with headings and bullet points where appropriate.
        """
        
        system_prompt = await self.generate_system_prompt()
        return await self.generate_response(prompt, system_prompt)

    async def knowledge_based_response(self, query: str) -> str:
        """Provide response based on existing knowledge"""
        prompt = f"""
        Research Query: {query}
        
        Current Date: {date.today()}
        
        Provide a comprehensive, well-researched response based on established knowledge.
        Include:
        - Key facts and information
        - Context and background
        - Relevant examples
        - Practical implications
        - Additional resources for further learning
        
        Structure the response clearly and cite general knowledge appropriately.
        """
        
        system_prompt = await self.generate_system_prompt()
        return await self.generate_response(prompt, system_prompt)

    def format_research_data(self, research_data: Dict[str, Any]) -> str:
        """Format research data for the prompt"""
        formatted = []
        
        if "sources" in research_data:
            formatted.append("Sources:")
            for i, source in enumerate(research_data["sources"], 1):
                formatted.append(f"{i}. {source.get('title', 'No title')}")
                if "snippet" in source:
                    formatted.append(f"   {source['snippet']}")
                if "date" in source:
                    formatted.append(f"   Date: {source['date']}")
                formatted.append("")
        
        if "summary" in research_data:
            formatted.append(f"Overall Summary: {research_data['summary']}")
        
        return "\n".join(formatted)

    async def compare_analysis(self, topics: List[str]) -> str:
        """Create a comparative analysis of multiple topics"""
        prompt = f"""
        Create a comparative analysis of these topics: {', '.join(topics)}
        
        Include:
        1. Key similarities and differences
        2. Strengths and weaknesses of each
        3. Use cases and applications
        4. Trends and future outlook
        5. Recommendations based on specific needs
        
        Provide a structured, objective comparison.
        """
        
        return await self.generate_response(prompt)