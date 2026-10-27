"""
QForge — Application State Container
Stores singleton instances (FAISS vector store) that are initialized
once at FastAPI lifespan startup and shared across all request handlers.
"""
from backend.services.vector_store.faiss_store import FaissVectorStore

# Global singleton — set during lifespan startup
_vector_store: FaissVectorStore | None = None


def set_vector_store(store: FaissVectorStore) -> None:
    global _vector_store
    _vector_store = store


def get_vector_store() -> FaissVectorStore:
    if _vector_store is None:
        raise RuntimeError("VectorStore not initialized. Check lifespan startup.")
    return _vector_store
