"""
Database migration script to fix embedding storage issues
Run this to update your existing database schema
"""

import asyncio
import sys
from sqlalchemy import text
from app.core.database import engine, AsyncSessionLocal

async def migrate_database():
    """Migrate database to fix embedding issues"""
    
    try:
        print("🔧 Starting database migration...")
        
        async with AsyncSessionLocal() as db:
            # Check if we need to drop the embedding column (if it exists and causes issues)
            try:
                # Check if embedding column exists
                result = await db.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name='messages' AND column_name='embedding'
                """))
                
                if result.fetchone():
                    print("🗑️ Dropping problematic embedding column...")
                    await db.execute(text("ALTER TABLE messages DROP COLUMN IF EXISTS embedding"))
                
                # Add embedding_id column if it doesn't exist
                result = await db.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name='messages' AND column_name='embedding_id'
                """))
                
                if not result.fetchone():
                    print("➕ Adding embedding_id column...")
                    await db.execute(text("ALTER TABLE messages ADD COLUMN embedding_id VARCHAR"))
                
                # Commit the changes
                await db.commit()
                print("✅ Database migration completed successfully!")
                
            except Exception as e:
                print(f"⚠️ Migration error: {e}")
                await db.rollback()
                raise
                
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        sys.exit(1)

async def verify_database_schema():
    """Verify the database schema is correct"""
    try:
        async with AsyncSessionLocal() as db:
            # Check messages table structure
            result = await db.execute(text("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name='messages' 
                ORDER BY ordinal_position
            """))
            
            columns = result.fetchall()
            print("📋 Messages table structure:")
            for col in columns:
                print(f"  - {col[0]} ({col[1]}) {'NULL' if col[2] == 'YES' else 'NOT NULL'}")
            
            # Verify other tables exist
            tables_to_check = ['users', 'conversations', 'persona_settings', 'emotional_profiles', 'proactive_events']
            
            result = await db.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema='public' AND table_type='BASE TABLE'
            """))
            
            existing_tables = [row[0] for row in result.fetchall()]
            print(f"\n📊 Existing tables: {existing_tables}")
            
            missing_tables = [t for t in tables_to_check if t not in existing_tables]
            if missing_tables:
                print(f"⚠️ Missing tables: {missing_tables}")
            else:
                print("✅ All required tables exist")
                
    except Exception as e:
        print(f"❌ Schema verification failed: {e}")

if __name__ == "__main__":
    print("🚀 Database Migration Tool")
    print("=" * 50)
    
    # Run migration
    asyncio.run(migrate_database())
    
    # Verify schema
    print("\n🔍 Verifying database schema...")
    asyncio.run(verify_database_schema())
    
    print("\n🎉 Migration process completed!")
    print("You can now restart your application.")