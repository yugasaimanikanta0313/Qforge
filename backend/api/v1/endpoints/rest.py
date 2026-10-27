"""
QForge — REST Endpoints: Sessions & Audit Logs
Provides HTTP endpoints for non-streaming operations:
  GET /api/v1/health       — Liveness probe
  GET /api/v1/audit/logs   — Recent audit log listing
  GET /api/v1/audit/{id}   — Session-specific audit trace
"""
import logging
from fastapi import APIRouter, HTTPException
from backend.db.client import get_db
from backend.db.repositories.audit_repo import get_audit_logs, get_session_audit
from backend.core.app_state import get_vector_store

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1")


@router.get("/health")
async def health_check():
    """Liveness + readiness probe. Returns service status and FAISS index info."""
    vs = get_vector_store()
    faiss_loaded = vs._is_loaded
    chunk_count = len(vs._chunks) if vs._chunks else 0
    return {
        "status": "healthy",
        "faiss_index_loaded": faiss_loaded,
        "guideline_chunks": chunk_count,
        "service": "QForge API v1",
    }


@router.get("/audit/logs")
async def list_audit_logs(limit: int = 50):
    """Return the most recent agent execution audit logs."""
    try:
        db = get_db()
        logs = await get_audit_logs(db, limit=limit)
        return {"logs": logs, "count": len(logs)}
    except Exception as e:
        logger.error(f"[REST] Audit log retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/audit/{session_id}")
async def get_session_trace(session_id: str):
    """Return all audit records for a specific session ID."""
    try:
        db = get_db()
        records = await get_session_audit(db, session_id)
        if not records:
            raise HTTPException(status_code=404, detail=f"No audit records for session {session_id}")
        return {"session_id": session_id, "records": records}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[REST] Session trace retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
