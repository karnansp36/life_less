#!/usr/bin/env python3
import asyncio
import os
import sys
from pathlib import Path

# Add the app directory to the path
sys.path.append(str(Path(__file__).parent.parent))

from app.database import engine, Base
from app.settings import settings

async def setup_database():
    """Setup database with required extensions and tables"""
    print("Setting up database...")
    
    try:
        async with engine.begin() as conn:
            # Create pgvector extension
            await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
            # Create all tables
            await conn.run_sync(Base.metadata.create_all)
        
        print("✅ Database setup completed successfully!")
        
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(setup_database())