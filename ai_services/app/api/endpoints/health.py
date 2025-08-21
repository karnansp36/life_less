from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
import logging

from app.database import get_db_session
from app.ollama_client import ollama_client

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "service": "personal-manager-ai",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

@router.get("/ready")
async def readiness_check(db: AsyncSession = Depends(get_db_session)):
    """Comprehensive readiness check including dependencies"""
    checks = {
        "database": False,
        "ollama": False,
        "overall": False
    }
    
    # Check database connection
    try:
        result = await db.execute("SELECT 1")
        checks["database"] = True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        checks["database"] = False
    
    # Check Ollama connection
    try:
        # Simple ping to Ollama
        async with ollama_client.session.get(f"{ollama_client.base_url}/api/tags") as response:
            checks["ollama"] = response.status == 200
    except Exception as e:
        logger.error(f"Ollama connection failed: {e}")
        checks["ollama"] = False
    
    checks["overall"] = checks["database"] and checks["ollama"]
    
    return {
        "status": "ready" if checks["overall"] else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": checks
    }

@router.get("/version")
async def version_info():
    """Get service version information"""
    return {
        "name": "Personal Manager AI Microservice",
        "version": "1.0.0",
        "description": "AI-powered personal manager for Wasp MERN stack",
        "api_version": "v1",
        "timestamp": datetime.utcnow().isoformat()
    }