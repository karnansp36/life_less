import logging
from datetime import datetime, date
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app import models

logger = logging.getLogger(__name__)

class FinanceService:
    def __init__(self, session: AsyncSession, user: models.User):
        self.session = session
        self.user = user

    async def create_expense(self, expense_data: Dict[str, Any]) -> models.Expense:
        """Create a new expense"""
        expense = models.Expense(
            user_id=self.user.id,
            amount=expense_data["amount"],
            currency=expense_data.get("currency", "USD"),
            category=expense_data["category"],
            description=expense_data["description"],
            tags=expense_data.get("tags", [])
        )
        
        self.session.add(expense)
        await self.session.flush()
        return expense

    async def get_recent_expenses(self, limit: int = 10) -> List[models.Expense]:
        """Get recent expenses"""
        stmt = select(models.Expense).where(
            models.Expense.user_id == self.user.id
        ).order_by(models.Expense.date.desc()).limit(limit)
        
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_expense_summary(self, days: int = 30) -> Dict[str, Any]:
        """Get expense summary for a period"""
        start_date = date.today() - timedelta(days=days)
        
        # Get total expenses
        stmt = select(func.sum(models.Expense.amount)).where(
            models.Expense.user_id == self.user.id,
            models.Expense.date >= start_date
        )
        result = await self.session.execute(stmt)
        total = result.scalar() or 0
        
        # Get expenses by category
        category_stmt = select(
            models.Expense.category,
            func.sum(models.Expense.amount).label("total")
        ).where(
            models.Expense.user_id == self.user.id,
            models.Expense.date >= start_date
        ).group_by(models.Expense.category)
        
        category_result = await self.session.execute(category_stmt)
        by_category = {row[0]: row[1] for row in category_result}
        
        # Calculate daily average
        daily_avg = total / days if days > 0 else 0
        
        return {
            "total": round(total, 2),
            "daily_average": round(daily_avg, 2),
            "by_category": by_category,
            "period_days": days
        }

    async def get_spending_trends(self) -> Dict[str, Any]:
        """Analyze spending trends"""
        # This would do more sophisticated analysis
        # For now, return basic insights
        
        summary = await self.get_expense_summary(30)
        
        insights = []
        if summary["daily_average"] > 50:
            insights.append("Your daily spending is relatively high. Consider reviewing discretionary expenses.")
        
        if "entertainment" in summary["by_category"] and summary["by_category"]["entertainment"] > 200:
            insights.append("Entertainment expenses are significant. You might want to set a budget for this category.")
        
        return {
            "summary": summary,
            "insights": insights,
            "recommendations": [
                "Track expenses daily for better awareness",
                "Set category-specific budgets",
                "Review subscriptions regularly"
            ]
        }

    async def categorize_expense(self, description: str, amount: float) -> str:
        """Suggest category for an expense"""
        prompt = f"""
        Categorize this expense:
        Description: {description}
        Amount: ${amount}
        
        Possible categories: food, transport, entertainment, shopping, health, education, bills, other
        
        Respond with only the category name.
        """
        
        try:
            from app.ollama_client import ollama_client
            category = await ollama_client.generate(prompt=prompt, temperature=0.1)
            return category.strip().lower()
        except Exception as e:
            logger.error(f"Error categorizing expense: {e}")
            return "other"