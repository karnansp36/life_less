from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError
from app.core.database import engine
from app.core.config import settings

def setup_vector_extension():
    """Setup pgvector extension if not already enabled"""
    try:
        with engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            conn.commit()
            print("✅ pgvector extension enabled")
    except ProgrammingError as e:
        print(f"⚠️ Error enabling pgvector extension: {e}")
        print("Note: Ensure PostgreSQL with pgvector extension is installed")

def create_tables():
    """Create all tables including vector-enabled ones"""
    from app.models.database import Base
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created")

def init_db():
    """Initialize the database with vector support"""
    setup_vector_extension()
    create_tables()