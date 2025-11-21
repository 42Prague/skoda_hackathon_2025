from fastapi import APIRouter
from app.core.vector_store import check_qdrant_health
from app.core.database import get_connection

router = APIRouter()


@router.get("/health")
async def health_check():
    """Basic health check"""
    return {"status": "ok"}


@router.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check including Qdrant and database"""
    health_status = {
        "status": "ok",
        "services": {}
    }
    
    # Check Qdrant
    try:
        qdrant_health = check_qdrant_health()
        health_status["services"]["qdrant"] = qdrant_health
    except Exception as e:
        health_status["services"]["qdrant"] = {
            "status": "error",
            "error": str(e)
        }
    
    # Check DuckDB
    try:
        conn = get_connection()
        conn.execute("SELECT 1")
        health_status["services"]["duckdb"] = {
            "status": "healthy"
        }
    except Exception as e:
        health_status["services"]["duckdb"] = {
            "status": "error",
            "error": str(e)
        }
    
    # Overall status
    all_healthy = all(
        service.get("status") == "healthy" 
        for service in health_status["services"].values()
    )
    
    if not all_healthy:
        health_status["status"] = "degraded"
    
    return health_status

