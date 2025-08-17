from fastapi import FastAPI
from sqlalchemy import text
from app.db import engine, Base

async def init_db(app: FastAPI):
    # Ensure pgvector extension exists (no-op if already there)
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)
