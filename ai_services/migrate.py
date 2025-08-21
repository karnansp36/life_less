# migrate.py
import asyncio
from app.database import engine, Base
from app.models import *

async def migrate():
    async with engine.begin() as conn:
        print("Dropping all tables...")
        await conn.run_sync(Base.metadata.drop_all)
        print("Creating new tables...")
        await conn.run_sync(Base.metadata.create_all)
    print("Migration complete!")

if __name__ == "__main__":
    asyncio.run(migrate())