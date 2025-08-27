from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
import asyncio
import uvicorn
import logging
from datetime import datetime

from app.core.config import settings
from app.core.database import init_database, close_database
from app.api import chat, persona, health
from app.services.proactive_service import proactive_service
from app.agents.crew_coordinator import crew_coordinator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    logger.info("🚀 Starting Intelligent AI Chat System...")
    
    # Initialize database
    await init_database()
    
    # Initialize services
    logger.info("✅ Services initialized")
    
    # Store startup time
    app.state.startup_time = datetime.now()
    
    logger.info("🎯 System ready for intelligent conversations!")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down...")
    
    # Close database connections
    await close_database()
    
    logger.info("✅ Shutdown complete")

# Create FastAPI app
app = FastAPI(
    title="Intelligent AI Chat System",
    description="Advanced AI chat with multi-agent intelligence, emotional awareness, and proactive engagement",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None
)

# Security middleware
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["localhost", "127.0.0.1", "*"] if settings.DEBUG else ["yourdomain.com"]
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = asyncio.get_event_loop().time()
    
    response = await call_next(request)
    
    process_time = asyncio.get_event_loop().time() - start_time
    logger.info(
        f"{request.method} {request.url.path} - {response.status_code} - {process_time:.3f}s"
    )
    
    return response

# Include routers
app.include_router(
    chat.router,
    prefix=f"{settings.API_V1_STR}/chat",
    tags=["chat"]
)

app.include_router(
    persona.router,
    prefix=f"{settings.API_V1_STR}/persona", 
    tags=["persona"]
)

app.include_router(
    health.router,
    prefix="/health",
    tags=["health"]
)

# Root endpoints
@app.get("/")
async def root():
    """Root endpoint with system information"""
    uptime = (datetime.now() - app.state.startup_time).total_seconds() if hasattr(app.state, 'startup_time') else 0
    
    return {
        "message": "🧠 Intelligent AI Chat System",
        "version": "2.0.0",
        "status": "operational",
        "uptime_seconds": uptime,
        "features": {
            "multi_agent_coordination": True,
            "emotional_intelligence": True, 
            "proactive_conversations": True,
            "vector_memory": True,
            "real_time_chat": True
        },
        "documentation": "/docs" if settings.DEBUG else None
    }

@app.get("/system/info")
async def system_info():
    """Detailed system information"""
    agent_status = await crew_coordinator.get_agent_status()
    
    return {
        "system": "Intelligent AI Chat",
        "architecture": "Multi-Agent with CrewAI Coordination",
        "agents": agent_status,
        "ai_models": {
            "primary": "Google Gemini Pro",
            "embeddings": "nomic-embed-text-v1.5"
        },
        "capabilities": {
            "emotional_intelligence": "Real-time emotion analysis and empathetic responses",
            "proactive_engagement": "Context-aware proactive conversations",
            "semantic_memory": "Vector-based conversation memory",
            "personality_adaptation": "Dynamic personality based on user preferences"
        }
    }

# Error handlers
from fastapi.responses import JSONResponse

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        content={"error": exc.detail},
        status_code=exc.status_code
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        content={"error": "Internal server error"},
        status_code=500
    )

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )
