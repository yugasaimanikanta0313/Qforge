"""
QForge — Audit REST Endpoints
Endpoints for viewing compliance audit records and session traces.
"""
import logging
from fastapi import APIRouter, HTTPException
from backend.db.client import get_db
from backend.db.repositories.audit_repo import get_audit_logs, get_session_audit
from backend.api.v1.schemas.audit import AuditTraceResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/audit", tags=["Audit"])


@router.get("/logs")
async def list_logs(limit: int = 50):
    """Return the most recent agent execution audit logs."""
    try:
        db = get_db()
        logs = await get_audit_logs(db, limit=limit)
        return {"logs": logs, "count": len(logs)}
    except Exception as e:
        logger.error(f"[AUDIT] Log retrieval failed: {e}")
        return {"logs": [], "count": 0, "error": str(e)}


@router.get("/{session_id}/trace", response_model=AuditTraceResponse)
@router.get("/{session_id}")
async def get_session_trace(session_id: str):
    """Return all audit records and execution timeline for a session."""
    try:
        db = get_db()
        records = await get_session_audit(db, session_id)
        if not records:
            raise HTTPException(status_code=404, detail=f"No audit records found for session {session_id}")
        return AuditTraceResponse(
            session_id=session_id,
            count=len(records),
            records=records,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[AUDIT] Trace retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
