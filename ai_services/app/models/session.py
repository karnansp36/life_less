# session.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from core.config import settings

# Async engine
engine = create_async_engine(settings.DATABASE_URL, echo=True, future=True)

# Async session
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    class_=AsyncSession
)

# Dependency
async def get_db():
    async with SessionLocal() as session:
        yield session
