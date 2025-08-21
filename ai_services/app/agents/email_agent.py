# agents/email_agent.py
from .base_agent import BaseAgent
from typing import Dict, Any, List
from sqlalchemy import select
from app import models
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)

class EmailAgent(BaseAgent):
    async def generate_system_prompt(self) -> str:
        return f"""
        You are {self.user.full_name}'s email management assistant.
        You help with email triage, drafting responses, and managing correspondence.
        
        Your capabilities:
        - Prioritize important emails
        - Draft professional responses
        - Summarize email threads
        - Identify urgent messages
        - Manage email categories and folders
        
        Always maintain a professional tone in email correspondence.
        Never reveal you are an AI. You are their email management specialist.
        """

    async def process_query(self, query: str, context: Dict[str, Any] = None) -> str:
        # Check if user has connected email accounts
        has_email_accounts = await self.check_email_accounts()
        
        if not has_email_accounts:
            return await self.handle_no_email_accounts(query)
        
        # Get recent emails for context
        recent_emails = await self.get_recent_emails()
        
        prompt = f"""
        User: {self.user.full_name}
        Current Date: {date.today()}
        
        Recent Emails:
        {recent_emails}
        
        User's Query: {query}
        
        Respond as a professional email management assistant.
        Provide specific, actionable email-related advice.
        """
        
        system_prompt = await self.generate_system_prompt()
        return await self.generate_response(prompt, system_prompt)

    async def check_email_accounts(self) -> bool:
        """Check if user has connected email accounts"""
        stmt = select(models.EmailAccount).where(
            models.EmailAccount.user_id == self.user.id,
            models.EmailAccount.is_active == True
        )
        
        result = await self.session.execute(stmt)
        accounts = result.scalars().all()
        return len(accounts) > 0

    async def handle_no_email_accounts(self, query: str) -> str:
        """Handle case when no email accounts are connected"""
        prompt = f"""
        User doesn't have any email accounts connected yet.
        
        User Query: {query}
        
        Explain how to connect email accounts and the benefits of email management.
        Be helpful and encouraging.
        """
        
        return await self.generate_response(prompt)

    async def get_recent_emails(self) -> str:
        """Get recent emails for context"""
        stmt = select(models.EmailMessage).where(
            models.EmailMessage.account_id.in_(
                select(models.EmailAccount.id).where(
                    models.EmailAccount.user_id == self.user.id
                )
            )
        ).order_by(models.EmailMessage.received_at.desc()).limit(5)
        
        result = await self.session.execute(stmt)
        emails = result.scalars().all()
        
        if not emails:
            return "No recent emails found."
        
        email_summaries = []
        for email in emails:
            summary = f"- From: {email.sender}\n  Subject: {email.subject}\n  Received: {email.received_at.strftime('%Y-%m-%d %H:%M')}"
            if not email.is_read:
                summary += " 📧 NEW"
            email_summaries.append(summary)
        
        return "\n".join(email_summaries)

    async def draft_email_response(self, email_id: int, tone: str = "professional") -> str:
        """Draft a response to a specific email"""
        stmt = select(models.EmailMessage).where(
            models.EmailMessage.id == email_id
        )
        
        result = await self.session.execute(stmt)
        email = result.scalar_one_or_none()
        
        if not email:
            return "Email not found."
        
        prompt = f"""
        Draft a {tone} response to this email:
        
        From: {email.sender}
        Subject: {email.subject}
        Body: {email.body}
        
        Consider the user's typical communication style and preferences.
        Keep the response concise and appropriate.
        """
        
        system_prompt = await self.generate_system_prompt()
        return await self.generate_response(prompt, system_prompt)