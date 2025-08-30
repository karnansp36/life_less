from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import AsyncGenerator
from app.core.database import AsyncSessionLocal
import os

# Load API secret from environment variable (set in .env)
API_SECRET = os.getenv("API_SECRET_KEY", "supersecretapikey")

async def verify_api_key(request: Request):
    """
    Simple API key authentication: only Wasp backend can call FastAPI.
    """
    api_key = request.headers.get("x-api-key")
    if not api_key or api_key != API_SECRET:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API Key"
        )
    return {"service": "wasp-backend"}

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get async database session"""
    async with AsyncSessionLocal() as db:
        try:
            yield db
        finally:
            await db.close()




