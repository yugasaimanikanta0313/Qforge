"""
QForge — Sessions REST Endpoints
Handles session CRUD lifecycle:
  POST   /sessions      — Initiate new session
  GET    /sessions/{id} — Retrieve session details
  DELETE /sessions/{id} — Terminate / cleanup session
  GET    /sessions      — List active & recent sessions
"""
import uuid
import logging
from fastapi import APIRouter, HTTPException, Depends
from backend.db.client import get_db
from backend.core.session_manager import get_session_manager, SessionManager
from backend.db.repositories.session_repo import (
    create_session,
    get_session,
    delete_session,
    list_sessions,
)
from backend.api.v1.schemas.session import SessionCreate, SessionResponse
from backend.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/sessions", tags=["Sessions"])


@router.post("", response_model=SessionResponse, status_code=201)
async def create_new_session(
    payload: SessionCreate,
    session_mgr: SessionManager = Depends(get_session_manager),
):
    """Register a new software validation session."""
    session_id = payload.session_id or str(uuid.uuid4())[:8]
    session_data = {
        "session_id": session_id,
        "language": payload.language,
        "raw_input": payload.code,
        "status": "INIT",
        "metadata": payload.metadata or {},
    }

    try:
        db = get_db()
        await create_session(db, session_data)
    except Exception as e:
        logger.warning(f"[SESSIONS] DB write skipped for {session_id}: {e}")

    ws_url = f"/ws/qforge/{session_id}"
    return SessionResponse(
        session_id=session_id,
        language=payload.language,
        status="INIT",
        websocket_url=ws_url,
    )


from backend.db.repositories.chat_history_repo import get_recent_history, get_session_history

@router.get("/history")
async def get_all_history(limit: int = 50):
    """List recent prompt history for sidebar timeline."""
    try:
        db = get_db()
        history = await get_recent_history(db, limit=limit)
        return {"history": history, "count": len(history)}
    except Exception as e:
        logger.warning(f"[SESSIONS] History list failed: {e}")
        return {"history": [], "count": 0}


@router.get("/history/{session_id}")
async def get_session_conversation(session_id: str):
    """Retrieve all turns of a specific conversation."""
    try:
        db = get_db()
        turns = await get_session_history(db, session_id)
        return {"session_id": session_id, "turns": turns, "count": len(turns)}
    except Exception as e:
        logger.warning(f"[SESSIONS] Session history failed: {e}")
        return {"session_id": session_id, "turns": [], "count": 0}


@router.get("/{session_id}")
async def get_session_by_id(
    session_id: str,
    session_mgr: SessionManager = Depends(get_session_manager),
):
    """Retrieve session details by ID."""
    live_info = session_mgr.get_session_info(session_id)
    try:
        db = get_db()
        persisted = await get_session(db, session_id)
    except Exception:
        persisted = None

    if not live_info and not persisted:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    return {
        "session_id": session_id,
        "live": live_info,
        "persisted": persisted,
    }


@router.delete("/{session_id}")
async def terminate_session(
    session_id: str,
    session_mgr: SessionManager = Depends(get_session_manager),
):
    """Cancel and delete an active or stored session."""
    await session_mgr.cancel_session(session_id)
    try:
        db = get_db()
        deleted = await delete_session(db, session_id)
    except Exception:
        deleted = False

    return {"session_id": session_id, "deleted": deleted, "cancelled": True}


@router.get("")
async def get_all_sessions():
    """List recent validation sessions."""
    try:
        db = get_db()
        sessions = await list_sessions(db, limit=50)
        return {"sessions": sessions, "count": len(sessions)}
    except Exception as e:
        logger.warning(f"[SESSIONS] List failed: {e}")
        return {"sessions": [], "count": 0}
