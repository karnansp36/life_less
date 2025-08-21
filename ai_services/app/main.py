from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
import logging

from app.settings import settings
from app.database import engine, Base
from app.api.endpoints import chat, health
from app.utils.logging_config import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Personal Manager AI Microservice",
    version="1.0.0",
    description="AI-powered personal manager microservice for Wasp MERN stack"
)

# CORS - allow requests from main app
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include endpoints
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(health.router, prefix="/health", tags=["health"])

async def init_db():
    """Initialize database with pgvector extension and tables"""
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database initialized successfully")

@app.on_event("startup")
async def startup():
    """Initialize application on startup"""
    await init_db()
    logger.info("Microservice started successfully")

@app.on_event("shutdown")
async def shutdown():
    logger.info("Microservice shutting down")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)