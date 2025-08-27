#!/usr/bin/env python3
"""
Startup script for the Intelligent AI Chat System
This script handles database initialization and starts the server
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def initialize_system():
    """Initialize the system before starting"""
    print("🚀 Initializing Intelligent AI Chat System...")
    
    try:
        # Import after adding to path
        from app.core.database import init_database
        from app.core.config import settings
        
        print("🔧 Initializing database...")
        await init_database()
        
        print("✅ System initialization completed!")
        return True
        
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        return False

def start_server():
    """Start the FastAPI server"""
    import uvicorn
    from app.core.config import settings
    
    print(f"🌟 Starting server on {settings.HOST}:{settings.PORT}")
    print(f"📚 API Documentation: http://{settings.HOST}:{settings.PORT}/docs")
    print(f"🔄 Debug mode: {settings.DEBUG}")
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )

async def main():
    """Main startup function"""
    print("=" * 60)
    print("🧠 INTELLIGENT AI CHAT SYSTEM")
    print("=" * 60)
    
    # Check environment
    if not os.getenv("DATABASE_URL"):
        print("⚠️  DATABASE_URL not set. Using default PostgreSQL connection.")
        print("   Make sure PostgreSQL is running on localhost:5432")
    
    if not os.getenv("GEMINI_API_KEY"):
        print("⚠️  GEMINI_API_KEY not set. AI will run in fallback mode.")
        print("   Set your Gemini API key in .env file for full functionality")
    
    # Initialize system
    success = await initialize_system()
    
    if not success:
        print("❌ Failed to initialize system. Please check your configuration.")
        sys.exit(1)
    
    # Start server
    start_server()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Shutting down gracefully...")
    except Exception as e:
        print(f"💥 Startup error: {e}")
        sys.exit(1)