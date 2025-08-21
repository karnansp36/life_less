# agents/admin_agent.py
from .base_agent import BaseAgent
from typing import Dict, Any, List
from sqlalchemy import select
from app import models
from datetime import datetime, date, timedelta
import logging

logger = logging.getLogger(__name__)

class AdminAgent(BaseAgent):
    async def generate_system_prompt(self) -> str:
        return f"""
        You are {self.user.full_name}'s administrative assistant.
        You handle scheduling, task management, organization, and workflow automation.
        
        Your responsibilities:
        - Calendar management and scheduling
        - Task prioritization and organization
        - Workflow optimization
        - Meeting coordination
        - Deadline tracking
        
        You're highly organized, proactive, and efficient.
        Never reveal you are an AI. You are their administrative specialist.
        """

    async def process_query(self, query: str, context: Dict[str, Any] = None) -> str:
        # Check what type of admin task is being requested
        task_type = await self.identify_task_type(query)
        
        if task_type == "scheduling":
            return await self.handle_scheduling(query)
        elif task_type == "task_management":
            return await self.handle_task_management(query)
        elif task_type == "organization":
            return await self.handle_organization(query)
        else:
            return await self.handle_general_admin(query)

    async def identify_task_type(self, query: str) -> str:
        """Identify the type of administrative task"""
        prompt = f"""
        Identify the type of administrative task in this query:
        "{query}"
        
        Types:
        - scheduling: Calendar, meetings, appointments
        - task_management: To-dos, tasks, reminders
        - organization: Sorting, categorizing, structuring
        - general: Other administrative tasks
        
        Respond with ONLY the type name.
        """
        
        try:
            response = await self.generate_response(prompt, temperature=0.1)
            return response.strip().lower()
        except:
            return "general"

    async def handle_scheduling(self, query: str) -> str:
        """Handle scheduling-related queries"""
        prompt = f"""
        User: {self.user.full_name}
        Current Date: {date.today()}
        Working Hours: {self.user.work_hours_start.strftime('%H:%M')} - {self.user.work_hours_end.strftime('%H:%M')}
        
        Query: {query}
        
        As an administrative assistant, provide scheduling advice considering:
        - Time management best practices
        - Buffer time between meetings
        - Focus time blocks
        - Realistic time allocation
        - Priority-based scheduling
        
        Be specific and practical.
        """
        
        system_prompt = await self.generate_system_prompt()
        return await self.generate_response(prompt, system_prompt)

    async def handle_task_management(self, query: str) -> str:
        """Handle task management queries"""
        prompt = f"""
        User: {self.user.full_name}
        Current Date: {date.today()}
        
        Query: {query}
        
        As a task management specialist, provide advice on:
        - Prioritization techniques (Eisenhower Matrix, ABC method)
        - Time blocking and focus sessions
        - Breaking down large tasks
        - Setting realistic deadlines
        - Avoiding procrastination
        
        Provide actionable strategies.
        """
        
        system_prompt = await self.generate_system_prompt()
        return await self.generate_response(prompt, system_prompt)

    async def handle_organization(self, query: str) -> str:
        """Handle organization-related queries"""
        prompt = f"""
        User: {self.user.full_name}
        
        Query: {query}
        
        As an organization specialist, provide advice on:
        - Digital organization (files, emails, documents)
        - Physical organization (workspace, materials)
        - Information management systems
        - Workflow optimization
        - Productivity tools and techniques
        
        Be practical and specific.
        """
        
        system_prompt = await self.generate_system_prompt()
        return await self.generate_response(prompt, system_prompt)

    async def handle_general_admin(self, query: str) -> str:
        """Handle general administrative queries"""
        prompt = f"""
        User: {self.user.full_name}
        Current Date: {date.today()}
        
        Query: {query}
        
        As an administrative assistant, provide professional, organized advice.
        Focus on efficiency, organization, and practical solutions.
        """
        
        system_prompt = await self.generate_system_prompt()
        return await self.generate_response(prompt, system_prompt)

    async def create_task_plan(self, goal: str, timeframe: str = "1 week") -> str:
        """Create a detailed task plan for achieving a goal"""
        prompt = f"""
        Create a detailed task plan to achieve this goal: {goal}
        
        Timeframe: {timeframe}
        
        Include:
        1. Breakdown of main tasks
        2. Subtasks for each main task
        3. Estimated time requirements
        4. Priority levels
        5. Suggested schedule
        6. Potential obstacles and solutions
        
        Make it practical and actionable.
        """
        
        return await self.generate_response(prompt)