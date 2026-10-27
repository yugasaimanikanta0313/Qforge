"""
QForge — Session Manager
In-memory registry of active WebSocket connections, session metadata,
and running LangGraph execution tasks.
"""
import asyncio
from typing import Dict, Any
from fastapi import WebSocket
from backend.core.logging import get_logger

logger = get_logger(__name__)


class SessionManager:
    """Manages active real-time sessions and their runner tasks."""

    def __init__(self):
        self._active_sockets: Dict[str, WebSocket] = {}
        self._active_tasks: Dict[str, asyncio.Task] = {}
        self._session_metadata: Dict[str, Dict[str, Any]] = {}

    def register_socket(self, session_id: str, websocket: WebSocket) -> None:
        """Register an open WebSocket connection for a session."""
        self._active_sockets[session_id] = websocket
        self._session_metadata[session_id] = {
            "status": "connected",
            "connected_at": asyncio.get_event_loop().time(),
        }
        logger.info("Session socket registered", session_id=session_id)

    def unregister_socket(self, session_id: str) -> None:
        """Unregister a session when WebSocket disconnects."""
        self._active_sockets.pop(session_id, None)
        task = self._active_tasks.pop(session_id, None)
        if task and not task.done():
            task.cancel()
        if session_id in self._session_metadata:
            self._session_metadata[session_id]["status"] = "disconnected"
        logger.info("Session socket unregistered", session_id=session_id)

    def register_task(self, session_id: str, task: asyncio.Task) -> None:
        """Register a background LangGraph runner task."""
        self._active_tasks[session_id] = task

    def get_socket(self, session_id: str) -> WebSocket | None:
        """Get WebSocket instance for an active session."""
        return self._active_sockets.get(session_id)

    def get_session_info(self, session_id: str) -> Dict[str, Any] | None:
        """Get session metadata and running state."""
        meta = self._session_metadata.get(session_id)
        if not meta:
            return None
        task = self._active_tasks.get(session_id)
        return {
            **meta,
            "has_running_task": bool(task and not task.done()),
            "socket_connected": session_id in self._active_sockets,
        }

    def list_active_sessions(self) -> Dict[str, Dict[str, Any]]:
        """Return all tracked sessions."""
        return {
            sid: self.get_session_info(sid) or {}
            for sid in self._session_metadata
        }

    async def cancel_session(self, session_id: str) -> bool:
        """Cancel a running agent task for a given session."""
        task = self._active_tasks.get(session_id)
        if task and not task.done():
            task.cancel()
            logger.info("Cancelled running task for session", session_id=session_id)
            return True
        return False


# Global singleton instance
session_manager = SessionManager()


def get_session_manager() -> SessionManager:
    """Dependency injection helper for FastAPI."""
    return session_manager
