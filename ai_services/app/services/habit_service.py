import logging
from datetime import datetime, date, timedelta
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app import models

logger = logging.getLogger(__name__)

class HabitService:
    def __init__(self, session: AsyncSession, user: models.User):
        self.session = session
        self.user = user

    async def get_all_habits(self) -> List[models.Habit]:
        """Get all user habits"""
        stmt = select(models.Habit).where(
            models.Habit.user_id == self.user.id
        ).options(selectinload(models.Habit.completions))
        
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def create_habit(self, habit_data: Dict[str, Any]) -> models.Habit:
        """Create a new habit"""
        habit = models.Habit(
            user_id=self.user.id,
            name=habit_data["name"],
            description=habit_data.get("description"),
            frequency=habit_data.get("frequency", "daily"),
            target_count=habit_data.get("target_count", 1)
        )
        
        self.session.add(habit)
        await self.session.flush()
        return habit

    async def mark_habit_complete(self, habit_id: int, notes: str = None) -> models.HabitCompletion:
        """Mark a habit as completed for today"""
        completion = models.HabitCompletion(
            habit_id=habit_id,
            notes=notes
        )
        
        self.session.add(completion)
        await self.session.flush()
        
        # Update habit streak
        await self._update_habit_streak(habit_id)
        
        return completion

    async def _update_habit_streak(self, habit_id: int):
        """Update habit streak based on completions"""
        stmt = select(models.Habit).where(models.Habit.id == habit_id)
        result = await self.session.execute(stmt)
        habit = result.scalar_one_or_none()
        
        if not habit:
            return
        
        # Get completions ordered by date
        completions_stmt = select(models.HabitCompletion).where(
            models.HabitCompletion.habit_id == habit_id
        ).order_by(models.HabitCompletion.completed_at.desc())
        
        completions_result = await self.session.execute(completions_stmt)
        completions = completions_result.scalars().all()
        
        # Calculate current streak
        current_streak = 0
        current_date = date.today()
        
        for completion in completions:
            comp_date = completion.completed_at.date()
            if comp_date == current_date:
                current_streak += 1
                current_date -= timedelta(days=1)
            else:
                break
        
        habit.current_streak = current_streak
        habit.longest_streak = max(habit.longest_streak, current_streak)
        
        await self.session.flush()

    async def get_today_habits(self) -> List[Dict[str, Any]]:
        """Get habits that need to be completed today"""
        habits = await self.get_all_habits()
        today = date.today()
        
        result = []
        for habit in habits:
            # Check if habit was completed today
            completed_today = any(
                c.completed_at.date() == today 
                for c in habit.completions
            )
            
            result.append({
                "id": habit.id,
                "name": habit.name,
                "description": habit.description,
                "completed_today": completed_today,
                "current_streak": habit.current_streak,
                "longest_streak": habit.longest_streak,
                "frequency": habit.frequency
            })
        
        return result

    async def get_habit_stats(self, days: int = 30) -> Dict[str, Any]:
        """Get habit statistics for a period"""
        start_date = date.today() - timedelta(days=days)
        
        stmt = select(models.HabitCompletion).where(
            models.HabitCompletion.habit_id.in_(
                select(models.Habit.id).where(models.Habit.user_id == self.user.id)
            ),
            models.HabitCompletion.completed_at >= start_date
        )
        
        result = await self.session.execute(stmt)
        completions = result.scalars().all()
        
        # Calculate completion rate
        total_possible = len(await self.get_all_habits()) * days
        actual_completions = len(completions)
        completion_rate = (actual_completions / total_possible * 100) if total_possible > 0 else 0
        
        return {
            "total_completions": actual_completions,
            "completion_rate": round(completion_rate, 1),
            "period_days": days,
            "average_daily_completions": round(actual_completions / days, 1) if days > 0 else 0
        }