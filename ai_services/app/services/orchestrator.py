import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app import models
from app.agents import (
    PersonalManagerAgent, HabitAgent, FinanceAgent, 
    EmailAgent, ContentAgent, AdminAgent, ResearchAgent
)
from app.ollama_client import ollama_client
from app.memory_manager import MemoryManager

logger = logging.getLogger(__name__)

class Orchestrator:
    def __init__(self, session: AsyncSession, user: models.User):
        self.session = session
        self.user = user
        self.memory_manager = MemoryManager(session, user.id)
        
        # Initialize all agents
        self.agents = {
            "personal_manager": PersonalManagerAgent(session, user),
            "habit": HabitAgent(session, user),
            "finance": FinanceAgent(session, user),
            "email": EmailAgent(session, user),
            "content": ContentAgent(session, user),
            "admin": AdminAgent(session, user),
            "research": ResearchAgent(session, user)
        }
        
        # Default agent
        self.default_agent = self.agents["personal_manager"]

    async def route_message(self, message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Route message to appropriate agent and return response"""
        try:
            # Detect which agent should handle this message
            agent_name = await self.detect_agent(message)
            
            # Get relevant memories for context
            relevant_memories = await self.memory_manager.retrieve_relevant_memories(message)
            
            # Build enhanced context
            enhanced_context = {
                "user": {
                    "id": self.user.id,
                    "name": self.user.full_name,
                    "timezone": self.user.timezone
                },
                "memories": relevant_memories,
                "agent": agent_name
            }
            
            if context:
                enhanced_context.update(context)
            
            # Route to the appropriate agent
            agent = self.agents.get(agent_name, self.default_agent)
            response = await agent.process_query(message, enhanced_context)
            
            # Store this interaction in memory if important
            await self._evaluate_and_store_memory(message, response, agent_name)
            
            return {
                "response": response,
                "agent_used": agent_name,
                "memories_used": len(relevant_memories)
            }
            
        except Exception as e:
            logger.error(f"Error routing message: {str(e)}")
            # Fallback to default agent
            response = await self.default_agent.process_query(message, context)
            return {
                "response": response,
                "agent_used": "personal_manager",
                "memories_used": 0,
                "error": str(e)
            }

    async def detect_agent(self, message: str) -> str:
        """Detect which agent should handle this message"""
        prompt = f"""
        Analyze this user message and determine which specialist should handle it:
        "{message}"
        
        Available specialists:
        - personal_manager: General personal management, emotional support, daily check-ins
        - habit: Habit tracking, routines, fitness, health, exercise
        - finance: Expenses, budgeting, money management, financial planning
        - email: Email management, correspondence, inbox organization
        - content: Writing, blogging, content creation, SEO optimization
        - admin: Scheduling, task management, calendar, organization
        - research: Information gathering, analysis, fact-finding, summaries
        
        Consider the content, intent, and context of the message.
        Respond with ONLY the specialist name.
        """
        
        try:
            agent_name = await ollama_client.generate(
                prompt=prompt,
                temperature=0.1,
                max_tokens=50
            )
            agent_name = agent_name.strip().lower()
            
            # Validate the agent name
            if agent_name in self.agents:
                return agent_name
            else:
                logger.warning(f"Invalid agent detected: {agent_name}, using default")
                return "personal_manager"
                
        except Exception as e:
            logger.error(f"Error detecting agent: {str(e)}")
            return "personal_manager"

    async def _evaluate_and_store_memory(self, query: str, response: str, agent_used: str):
        """Evaluate if this interaction should be stored in long-term memory"""
        evaluation_prompt = f"""
        Evaluate if this user interaction contains important personal information that should be remembered long-term.
        
        User query: {query}
        Assistant response: {response}
        Specialist used: {agent_used}
        
        Consider storing if it contains:
        - Personal preferences or dislikes
        - Important life events
        - Goals or aspirations
        - Habits or routines
        - Financial information
        - Health information
        - Work or professional details
        
        Respond with ONLY: YES or NO
        """
        
        try:
            should_store = await ollama_client.generate(
                prompt=evaluation_prompt,
                temperature=0.1
            )
            
            if should_store.strip().upper() == "YES":
                memory_content = f"User mentioned: {query}. Context: {response} (Handled by: {agent_used})"
                await self.memory_manager.store_memory(
                    content=memory_content,
                    memory_type="personal",
                    importance=0.7,
                    tags=["conversation", "personal", agent_used]
                )
                
        except Exception as e:
            logger.error(f"Error evaluating memory storage: {str(e)}")

    async def get_agent_stats(self) -> Dict[str, Any]:
        """Get statistics about agent usage"""
        # This would track agent usage over time
        return {
            "total_agents": len(self.agents),
            "available_agents": list(self.agents.keys()),
            "default_agent": "personal_manager"
        }