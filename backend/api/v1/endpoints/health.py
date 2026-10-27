"""
QForge — Health REST Endpoints
Liveness and readiness probes designed for Kubernetes, load balancers, and monitoring.
"""
from fastapi import APIRouter, status
from backend.core.app_state import get_vector_store
from backend.services.llm.ollama_client import OllamaClient
from backend.config import settings

router = APIRouter(tags=["Health"])


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """Liveness & readiness probe returning system components status."""
    try:
        vs = get_vector_store()
        faiss_loaded = getattr(vs, "_is_loaded", False) if vs else False
        chunk_count = len(getattr(vs, "_chunks", [])) if vs and hasattr(vs, "_chunks") else 0
    except Exception:
        faiss_loaded = False
        chunk_count = 0

    return {
        "status": "healthy",
        "service": "QForge Engine",
        "version": "1.0.0",
        "faiss_index_loaded": faiss_loaded,
        "guideline_chunks": chunk_count,
        "complexity_threshold": settings.complexity_threshold,
        "max_repair_cycles": settings.max_repair_cycles,
    }


@router.get("/health/ready", status_code=status.HTTP_200_OK)
async def readiness_probe():
    """Kubernetes readiness probe."""
    vs = get_vector_store()
    if not vs or not getattr(vs, "_is_loaded", False):
        return {"ready": False, "reason": "FAISS vector store initializing"}
    return {"ready": True}


@router.get("/health/live", status_code=status.HTTP_200_OK)
async def liveness_probe():
    """Kubernetes liveness probe."""
    return {"live": True}
