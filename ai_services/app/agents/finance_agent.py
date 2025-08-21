# agents/finance_agent.py
from .base_agent import BaseAgent
from typing import Dict, Any
from sqlalchemy import select, func
from app import models
from datetime import datetime, date, timedelta
import json

class FinanceAgent(BaseAgent):
    async def generate_system_prompt(self) -> str:
        return f"""
        You are {self.user.full_name}'s personal finance manager.
        You help with budgeting, expense tracking, financial planning, and money management.
        
        Your expertise:
        - Practical budgeting advice
        - Expense categorization and analysis
        - Saving strategies
        - Financial goal setting
        - Spending pattern identification
        
        Be professional, non-judgmental, and focused on solutions.
        Never reveal you are an AI. You are their financial advisor.
        """

    async def process_query(self, query: str, context: Dict[str, Any] = None) -> str:
        # Get financial overview
        financial_overview = await self.get_financial_overview()
        
        prompt = f"""
        User: {self.user.full_name}
        Current Date: {date.today()}
        
        Financial Overview:
        {financial_overview}
        
        User's Query: {query}
        
        Respond as a professional financial manager. Provide specific, actionable advice.
        Use numbers and concrete suggestions when possible.
        """
        
        system_prompt = await self.generate_system_prompt()
        return await self.generate_response(prompt, system_prompt)

    async def get_financial_overview(self) -> str:
        """Get overview of user's financial situation"""
        # Get this month's expenses
        first_day = date.today().replace(day=1)
        stmt = select(models.Expense).where(
            models.Expense.user_id == self.user.id,
            models.Expense.date >= first_day
        )
        
        result = await self.session.execute(stmt)
        monthly_expenses = result.scalars().all()
        
        # Calculate totals by category
        category_totals = {}
        total_monthly = 0
        
        for expense in monthly_expenses:
            category = expense.category.value if hasattr(expense.category, 'value') else expense.category
            category_totals[category] = category_totals.get(category, 0) + expense.amount
            total_monthly += expense.amount
        
        # Format overview
        overview = f"Total expenses this month: ${total_monthly:.2f}\n\n"
        overview += "Breakdown by category:\n"
        
        for category, amount in category_totals.items():
            percentage = (amount / total_monthly * 100) if total_monthly > 0 else 0
            overview += f"  {category}: ${amount:.2f} ({percentage:.1f}%)\n"
        
        # Add weekly average if we're partway through month
        days_in_month = (date.today() - first_day).days + 1
        daily_average = total_monthly / days_in_month if days_in_month > 0 else 0
        overview += f"\nDaily average: ${daily_average:.2f}"
        
        return overview