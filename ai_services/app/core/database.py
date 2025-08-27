from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
import redis.asyncio as redis   # <-- async Redis client
from typing import AsyncGenerator, Optional
from app.core.config import settings

# ---------- SQLAlchemy (Async) ----------
engine = create_async_engine(
    settings.DATABASE_URL,  # must be postgresql+asyncpg://
    pool_pre_ping=True,
    pool_recycle=300,
    echo=settings.DEBUG
)

# Renamed to AsyncSessionLocal for consistency with your imports
AsyncSessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Keep SessionLocal as an alias for backward compatibility
SessionLocal = AsyncSessionLocal

Base = declarative_base()

# ---------- Redis ----------
_redis_client: Optional[redis.Redis] = None

def get_redis() -> redis.Redis:
    """Get Redis async client instance"""
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            retry_on_timeout=True
        )
    return _redis_client

# Dependency for DB session
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as db:
        yield db

# ---------- Lifecycle ----------
async def init_database():
    """Initialize database with extensions and tables"""
    try:
        # Import all models to ensure they're registered with Base
        from app.models.database import Conversation, Message, User, PersonaSettings, ProactiveEvent
        
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        # Test Redis connection (async call now!)
        redis_client = get_redis()
        await redis_client.ping()

        print("✅ Database and Redis connection successful")
    except Exception as e:
        print(f"❌ Init failed: {e}")
        raise
    else:
        print("✅ Database initialized successfully")

async def close_database():
    """Close database connections"""
    global _redis_client
    if _redis_client:
        await _redis_client.close()   # <-- async close
        _redis_client = None
    
    if engine:
        await engine.dispose()
    print("✅ Database connections closed")