"""
Database initialization and migration script
Creates tables if they don't exist, then applies migrations
"""

import asyncio
import sys
from sqlalchemy import text
from app.core.database import AsyncSessionLocal, engine, Base
from app.models.database import Base, User, Conversation, Message, PersonaSettings, EmotionalProfile, ProactiveEvent


async def create_tables():
    """Create tables using SQLAlchemy models"""
    try:
        async with engine.begin() as conn:
            print("🔄 Creating database tables...")
            await conn.run_sync(Base.metadata.create_all)

            # Debug: list what Base.metadata THINKS it created
            print("\n📋 Models registered in Base.metadata:")
            for tbl in Base.metadata.tables.keys():
                print(f"  - {tbl}")

        print("✅ Tables created successfully!")
        return True
    except Exception as e:
        print(f"❌ Error while creating tables: {e}")
        return False


async def check_table_exists(db, table_name: str):
    """Check if a table exists in Postgres"""
    result = await db.execute(text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = :table_name
        )
    """), {"table_name": table_name})
    return result.scalar()


async def migrate_database():
    """Migrate database schema (embedding column fixes, etc.)"""
    try:
        print("🔧 Starting database migration...")
        
        async with AsyncSessionLocal() as db:
            try:
                # Ensure target table exists
                table_exists = await check_table_exists(db, "fastapimessage")
                if not table_exists:
                    print("❌ fastapimessage table doesn't exist! Did you forget to import Message model?")
                    return False
                
                # Drop legacy embedding column if it exists
                result = await db.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name='fastapimessage' AND column_name='embedding'
                """))
                if result.fetchone():
                    print("🗑️ Dropping old 'embedding' column...")
                    await db.execute(text("ALTER TABLE fastapimessage DROP COLUMN IF EXISTS embedding"))
                
                # Add embedding_id column if missing
                result = await db.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name='fastapimessage' AND column_name='embedding_id'
                """))
                if not result.fetchone():
                    print("➕ Adding embedding_id column...")
                    await db.execute(text("ALTER TABLE fastapimessage ADD COLUMN embedding_id TEXT"))
                
                await db.commit()
                print("✅ Migration completed successfully!")
                return True
            
            except Exception as e:
                print(f"⚠️ Migration error: {e}")
                await db.rollback()
                return False
    
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False


async def verify_database_schema():
    """Verify database schema after creation + migration"""
    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            tables = result.fetchall()
            print("\n📋 Tables in database after init:")
            for t in tables:
                print(f"  - {t[0]}")
            
            # Show fastapimessage structure
            result = await db.execute(text("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name='fastapimessage'
                ORDER BY ordinal_position
            """))
            columns = result.fetchall()
            print("\n📋 fastapimessage table structure:")
            if not columns:
                print("  ❌ fastapimessage table not found!")
            else:
                for col in columns:
                    print(f"  - {col[0]} ({col[1]}) {'NULL' if col[2] == 'YES' else 'NOT NULL'}")
    
    except Exception as e:
        print(f"❌ Schema verification failed: {e}")


async def main():
    """Main async function"""
    print("🚀 Database Initialization & Migration Tool")
    print("=" * 50)

    # Step 1: Create tables
    tables_created = await create_tables()

    if tables_created:
        # Step 2: Run migration
        migration_ok = await migrate_database()

        # Step 3: Verify schema
        print("\n🔍 Verifying database schema...")
        await verify_database_schema()

        if migration_ok:
            print("\n🎉 Database initialization completed successfully!")
        else:
            print("\n⚠️ Migration completed with issues")
    else:
        print("\n❌ Failed to create tables!")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
