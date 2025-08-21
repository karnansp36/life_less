# agents/habit_agent.py
from .base_agent import BaseAgent
from typing import Dict, Any
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app import models
from datetime import datetime, date, timedelta
import json

class HabitAgent(BaseAgent):
    async def generate_system_prompt(self) -> str:
        return f"""
        You are {self.user.full_name}'s habit coach and accountability partner.
        You help them build and maintain positive habits, track progress, and stay motivated.
        
        Your approach:
        - Encouraging but honest
        - Focus on small, sustainable changes
        - Celebrate progress, no matter how small
        - Help identify obstacles and solutions
        - Provide practical advice based on habit science
        
        Never reveal you are an AI. You are their personal habit coach.
        """

    async def process_query(self, query: str, context: Dict[str, Any] = None) -> str:
        # Get current habits and progress
        habits_status = await self.get_habits_status()
        
        prompt = f"""
        User: {self.user.full_name}
        Current Date: {date.today()}
        
        Current Habits Status:
        {habits_status}
        
        User's Query: {query}
        
        Respond as a supportive habit coach. Provide specific, actionable advice.
        Celebrate progress and help overcome challenges.
        """
        
        system_prompt = await self.generate_system_prompt()
        return await self.generate_response(prompt, system_prompt)

    async def get_habits_status(self) -> str:
        """Get current status of all habits"""
        stmt = select(models.Habit).where(
            models.Habit.user_id == self.user.id,
            models.Habit.is_active == True
        ).options(selectinload(models.Habit.completions))
        
        result = await self.session.execute(stmt)
        habits = result.scalars().all()
        
        if not habits:
            return "No active habits. Let's help them start building some positive routines!"
        
        status_lines = []
        today = date.today()
        
        for habit in habits:
            # Check completions for today
            completed_today = any(
                c.completed_at.date() == today 
                for c in habit.completions
            )
            
            # Check streak status
            streak_status = f"Current streak: {habit.current_streak} days"
            if habit.current_streak > 0:
                streak_status += f" (Longest: {habit.longest_streak} days)"
            
            status = "✅ Completed today" if completed_today else "⏰ Not completed today"
            status_lines.append(f"{habit.name}: {status} | {streak_status}")
        
        return "\n".join(status_lines)