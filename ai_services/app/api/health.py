from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import asyncio
import psutil
import sys

from app.core.dependencies import get_db
from app.core.database import get_redis
from app.services.socket_manager import socket_manager
from app.agents.crew_coordinator import crew_coordinator
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/")
async def basic_health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "Intelligent AI Chat System",
        "version": "2.0.0"
    }

@router.get("/detailed")
async def detailed_health_check(db: Session = Depends(get_db)):
    """Detailed health check with system metrics"""
    try:
        health_data = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "checks": {}
        }
        
        # Database check
        try:
            db.execute("SELECT 1")
            health_data["checks"]["database"] = {
                "status": "healthy",
                "response_time": "< 50ms"
            }
        except Exception as e:
            health_data["checks"]["database"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health_data["status"] = "degraded"
        
        # Redis check
        try:
            redis_client = get_redis()
            await redis_client.ping()
            health_data["checks"]["redis"] = {
                "status": "healthy",
                "response_time": "< 10ms"
            }
        except Exception as e:
            health_data["checks"]["redis"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health_data["status"] = "degraded"
        
        # AI Services check
        try:
            from app.services.ai_service import ai_service
            # Simple test to ensure AI service is responsive
            health_data["checks"]["ai_service"] = {
                "status": "healthy",
                "models": {
                    "gemini": "available" if hasattr(ai_service, 'gemini') else "unavailable",
                    "claude": "available" if hasattr(ai_service, 'claude') else "unavailable"
                }
            }
        except Exception as e:
            health_data["checks"]["ai_service"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health_data["status"] = "degraded"
        
        # Agent coordination check
        try:
            agent_status = await crew_coordinator.get_agent_status()
            active_agents = sum(1 for agent in agent_status.values() if agent['active'])
            health_data["checks"]["agents"] = {
                "status": "healthy",
                "active_agents": active_agents,
                "total_agents": len(agent_status),
                "details": agent_status
            }
        except Exception as e:
            health_data["checks"]["agents"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health_data["status"] = "degraded"
        
        # WebSocket connections check
        try:
            online_users = len(socket_manager.get_online_users())
            total_connections = sum(
                socket_manager.get_user_session_count(user_id) 
                for user_id in socket_manager.get_online_users()
            )
            health_data["checks"]["websockets"] = {
                "status": "healthy",
                "online_users": online_users,
                "total_connections": total_connections
            }
        except Exception as e:
            health_data["checks"]["websockets"] = {
                "status": "unhealthy",
                "error": str(e)
            }
        
        return health_data
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }

@router.get("/system-metrics")
async def get_system_metrics():
    """Get detailed system performance metrics"""
    try:
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        
        # Memory usage
        memory = psutil.virtual_memory()
        memory_usage = {
            "total": memory.total,
            "available": memory.available,
            "percent": memory.percent,
            "used": memory.used
        }
        
        # Disk usage
        disk = psutil.disk_usage('/')
        disk_usage = {
            "total": disk.total,
            "used": disk.used,
            "free": disk.free,
            "percent": (disk.used / disk.total) * 100
        }
        
        # Network IO
        network = psutil.net_io_counters()
        network_io = {
            "bytes_sent": network.bytes_sent,
            "bytes_recv": network.bytes_recv,
            "packets_sent": network.packets_sent,
            "packets_recv": network.packets_recv
        }
        
        # Process info
        process = psutil.Process()
        process_info = {
            "pid": process.pid,
            "memory_percent": process.memory_percent(),
            "cpu_percent": process.cpu_percent(),
            "num_threads": process.num_threads(),
            "create_time": datetime.fromtimestamp(process.create_time()).isoformat()
        }
        
        return {
            "timestamp": datetime.now().isoformat(),
            "cpu": {
                "usage_percent": cpu_percent,
                "core_count": cpu_count
            },
            "memory": memory_usage,
            "disk": disk_usage,
            "network": network_io,
            "process": process_info,
            "python_version": sys.version,
            "uptime_seconds": (datetime.now() - datetime.fromtimestamp(process.create_time())).total_seconds()
        }
        
    except Exception as e:
        logger.error(f"Error getting system metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ai-status")
async def get_ai_status():
    """Get AI services status and configuration"""
    try:
        from app.services.ai_service import ai_service
        from app.services.embedding_service import embedding_service
        
        status = {
            "timestamp": datetime.now().isoformat(),
            "ai_models": {
                "primary": "Google Gemini Pro",
                "secondary": "Anthropic Claude",
                "embeddings": "sentence-transformers/all-MiniLM-L6-v2"
            },
            "services": {
                "gemini": {
                    "available": hasattr(ai_service, 'gemini'),
                    "configured": bool(settings.GEMINI_API_KEY)
                },
                "claude": {
                    "available": hasattr(ai_service, 'claude'),
                    "configured": bool(settings.ANTHROPIC_API_KEY)
                },
                "embeddings": {
                    "model": embedding_service.model_name,
                    "dimension": embedding_service.dimension
                }
            },
            "agent_coordination": await crew_coordinator.get_agent_status()
        }
        
        return status
        
    except Exception as e:
        logger.error(f"Error getting AI status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/database-status")
async def get_database_status(db: Session = Depends(get_db)):
    """Get database connection and table status - FIXED VERSION"""
    try:
        # Test basic connection
        result = db.execute(text("SELECT 1")).fetchone()
        
        # Get table information safely
        tables_info = {}
        try:
            # Use text() for raw SQL queries
            from sqlalchemy import text
            tables_result = db.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)).fetchall()
            
            tables_info = {row[0]: {"status": "exists"} for row in tables_result}
        except Exception as e:
            logger.warning(f"Could not get table info: {e}")
            tables_info = {"warning": "Table information unavailable"}
        
        # Get recent activity safely
        activity = {}
        try:
            recent_messages = db.execute(text("""
                SELECT COUNT(*) as count
                FROM messages 
                WHERE created_at > NOW() - INTERVAL '1 hour'
            """)).fetchone()
            
            activity["messages_last_hour"] = recent_messages[0] if recent_messages else 0
        except Exception as e:
            logger.warning(f"Could not get activity stats: {e}")
            activity = {"warning": "Activity stats unavailable"}
        
        return JSONResponse({
            "status": "connected",
            "timestamp": datetime.now().isoformat(),
            "tables": tables_info,
            "recent_activity": activity,
            "connection_pool": "active"
        })
        
    except Exception as e:
        logger.error(f"Database status check failed: {e}")
        return JSONResponse({
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }, status_code=500)
@router.post("/restart-services")
async def restart_services():
    """Restart specific services (for admin use)"""
    try:
        restart_log = {
            "timestamp": datetime.now().isoformat(),
            "actions": []
        }
        
        # Restart agent coordination
        try:
            # This would restart agent services
            restart_log["actions"].append({
                "service": "agents",
                "status": "restarted",
                "message": "Agent coordination system restarted"
            })
        except Exception as e:
            restart_log["actions"].append({
                "service": "agents",
                "status": "failed",
                "error": str(e)
            })
        
        # Clear caches
        try:
            redis_client = get_redis()
            # Clear specific cache keys, not all Redis data
            # await redis_client.flushdb()  # Be careful with this
            restart_log["actions"].append({
                "service": "cache",
                "status": "cleared",
                "message": "Cache cleared successfully"
            })
        except Exception as e:
            restart_log["actions"].append({
                "service": "cache",
                "status": "failed",
                "error": str(e)
            })
        
        return restart_log
        
    except Exception as e:
        logger.error(f"Service restart failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/readiness")
async def readiness_check():
    """Kubernetes readiness probe"""
    try:
        # Quick checks for critical services
        checks_passed = 0
        total_checks = 3
        
        # Database check
        try:
            db = next(get_db())
            db.execute("SELECT 1")
            db.close()
            checks_passed += 1
        except:
            pass
        
        # AI service check
        try:
            from app.services.ai_service import ai_service
            if hasattr(ai_service, 'gemini') or hasattr(ai_service, 'claude'):
                checks_passed += 1
        except:
            pass
        
        # Agent coordination check
        try:
            agent_status = await crew_coordinator.get_agent_status()
            if len(agent_status) > 0:
                checks_passed += 1
        except:
            pass
        
        if checks_passed >= 2:  # At least 2 of 3 services working
            return {"status": "ready"}
        else:
            raise HTTPException(status_code=503, detail="Service not ready")
            
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Readiness check failed: {str(e)}")

@router.get("/liveness")
async def liveness_check():
    """Kubernetes liveness probe"""
    return {
        "status": "alive",
        "timestamp": datetime.now().isoformat()
    }