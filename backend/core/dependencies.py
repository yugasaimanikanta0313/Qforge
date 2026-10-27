"""
QForge — FastAPI Dependency Injection
Provides reusable dependency providers for API route handlers:
  - Database client / session
  - FAISS Vector Store instance
  - Session Manager registry
"""
from backend.db.client import get_db
from backend.core.app_state import get_vector_store
from backend.core.session_manager import get_session_manager, SessionManager
from backend.services.vector_store.faiss_store import FaissVectorStore

__all__ = [
    "get_db",
    "get_vector_store",
    "get_session_manager",
    "SessionManager",
    "FaissVectorStore",
]
