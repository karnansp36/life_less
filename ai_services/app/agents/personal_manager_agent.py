# agents/personal_manager_agent.py
from .base_agent import BaseAgent
from typing import Dict, Any, List
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app import models
from datetime import datetime, date
import json

class PersonalManagerAgent(BaseAgent):
    async def generate_system_prompt(self) -> str:
        return f"""
        You are {self.user.full_name}'s personal manager and assistant. You are NOT an AI - you are their dedicated personal manager.
        
        About {self.user.full_name}:
        - Timezone: {self.user.timezone}
        - Wake time: {self.user.wake_time.strftime('%H:%M')}
        - Sleep time: {self.user.sleep_time.strftime('%H:%M')}
        - Work hours: {self.user.work_hours_start.strftime('%H:%M')} to {self.user.work_hours_end.strftime('%H:%M')}
        
        Your personality:
        - Warm, professional, and empathetic
        - Proactive and organized
        - Supportive but direct when needed
        - Focus on practical solutions
        - Remember personal details and preferences
        - Adapt your tone to match the user's emotional state
        
        Always respond as a human personal manager would. Never reveal you are an AI.
        """

    async def process_query(self, query: str, context: Dict[str, Any] = None) -> str:
        # Detect emotion in the query
        emotion = await self.detect_emotion(query)
        empathetic_opening = await self.generate_empathetic_response(query, emotion)
        
        # Get user's recent activities
        recent_activities = await self.get_recent_activities()
        
        # Build context-aware prompt
        prompt = f"""
        {empathetic_opening}
        
        Recent Activities:
        {recent_activities}
        
        User's Query: {query}
        
        Current date: {date.today()}
        Current time: {datetime.now().strftime('%H:%M')}
        
        Respond as a professional personal manager. Be helpful, organized, and personable.
        """
        
        system_prompt = await self.generate_system_prompt()
        return await self.generate_response(prompt, system_prompt)

    async def get_recent_activities(self) -> str:
        """Get user's recent activities for context"""
        activities = []
        
        # Get recent habits
        stmt = select(models.Habit).where(
            models.Habit.user_id == self.user.id,
            models.Habit.is_active == True
        ).options(selectinload(models.Habit.completions))
        
        result = await self.session.execute(stmt)
        habits = result.scalars().all()
        
        for habit in habits:
            completions_today = [
                c for c in habit.completions 
                if c.completed_at.date() == date.today()
            ]
            status = "✓ Completed today" if completions_today else "⏰ Pending today"
            activities.append(f"Habit: {habit.name} - {status}")
        
        # Get recent expenses
        stmt = select(models.Expense).where(
            models.Expense.user_id == self.user.id
        ).order_by(models.Expense.date.desc()).limit(3)
        
        result = await self.session.execute(stmt)
        recent_expenses = result.scalars().all()
        
        if recent_expenses:
            activities.append("Recent Expenses:")
            for expense in recent_expenses:
                activities.append(f"  - {expense.amount} {expense.currency} for {expense.description}")
        
        return "\n".join(activities) if activities else "No recent activities recorded."