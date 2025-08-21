import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta

from app import models
from app.ollama_client import ollama_client

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self, session: AsyncSession, user: models.User):
        self.session = session
        self.user = user

    async def get_email_accounts(self) -> List[models.EmailAccount]:
        """Get user's email accounts"""
        stmt = select(models.EmailAccount).where(
            models.EmailAccount.user_id == self.user.id,
            models.EmailAccount.is_active == True
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_recent_emails(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent emails for the user"""
        stmt = select(models.EmailMessage).where(
            models.EmailMessage.account_id.in_(
                select(models.EmailAccount.id).where(
                    models.EmailAccount.user_id == self.user.id
                )
            )
        ).order_by(models.EmailMessage.received_at.desc()).limit(limit)
        
        result = await self.session.execute(stmt)
        emails = result.scalars().all()
        
        return [{
            "id": email.id,
            "subject": email.subject,
            "sender": email.sender,
            "received_at": email.received_at,
            "is_read": email.is_read,
            "importance": email.importance
        } for email in emails]

    async def get_unread_count(self) -> int:
        """Get count of unread emails"""
        stmt = select(models.EmailMessage).where(
            models.EmailMessage.account_id.in_(
                select(models.EmailAccount.id).where(
                    models.EmailAccount.user_id == self.user.id
                )
            ),
            models.EmailMessage.is_read == False
        )
        result = await self.session.execute(stmt)
        emails = result.scalars().all()
        return len(emails)

    async def categorize_email(self, email_id: int) -> str:
        """Categorize an email using AI"""
        stmt = select(models.EmailMessage).where(models.EmailMessage.id == email_id)
        result = await self.session.execute(stmt)
        email = result.scalar_one_or_none()
        
        if not email:
            return "unknown"
        
        prompt = f"""
        Categorize this email:
        Subject: {email.subject}
        Body: {email.body[:500]}...
        
        Possible categories: urgent, important, newsletter, social, promotion, personal, work, other
        
        Respond with only the category name.
        """
        
        try:
            category = await ollama_client.generate(prompt=prompt, temperature=0.1)
            return category.strip().lower()
        except Exception as e:
            logger.error(f"Error categorizing email: {e}")
            return "other"

    async def draft_response(self, email_id: int, tone: str = "professional") -> str:
        """Draft a response to an email"""
        stmt = select(models.EmailMessage).where(models.EmailMessage.id == email_id)
        result = await self.session.execute(stmt)
        email = result.scalar_one_or_none()
        
        if not email:
            return "Email not found."
        
        prompt = f"""
        Draft a {tone} response to this email:
        
        From: {email.sender}
        Subject: {email.subject}
        Body: {email.body}
        
        Keep the response concise and appropriate for a {tone} tone.
        """
        
        try:
            response = await ollama_client.generate(prompt=prompt, temperature=0.7)
            return response
        except Exception as e:
            logger.error(f"Error drafting email response: {e}")
            return "I apologize, but I'm having trouble drafting a response right now."

    async def summarize_email_thread(self, thread_id: str) -> str:
        """Summarize an email thread"""
        # This would integrate with actual email provider API
        # For now, return a placeholder
        return "Email thread summarization would be implemented with actual email provider integration."