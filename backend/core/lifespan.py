"""
QForge — FastAPI Lifespan Handler
Handles startup initialization and graceful shutdown:
  1. Connects to MongoDB Motor client
  2. Ingests enterprise guidelines into FAISS vector store
  3. Probes/warms local Ollama inference service
  4. Flushes and cleans up connections on shutdown
"""
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from backend.config import settings
from backend.db.client import init_db, close_db
from backend.core.app_state import set_vector_store
from backend.services.vector_store.faiss_store import FaissVectorStore
from backend.services.llm.ollama_client import OllamaClient
from backend.core.logging import get_logger, setup_logging

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context manager for startup and shutdown hooks.
    """
    setup_logging()
    logger.info("Starting QForge Application Lifespan")

    # ── 1. Initialize Database Connection ─────────────────────
    try:
        await init_db()
        logger.info("MongoDB connection initialized successfully")
    except Exception as e:
        logger.warning("MongoDB initialization failed, continuing without persistence", error=str(e))

    # ── 2. Initialize FAISS Vector Store ──────────────────────
    try:
        logger.info("Initializing FAISS Vector Store with BGE-small embeddings", model=settings.embedding_model)
        vector_store = FaissVectorStore(embedding_model=settings.embedding_model)
        # Attempt to load serialized index or build from directory
        try:
            vector_store.load(settings.faiss_index_path, settings.faiss_metadata_path)
            logger.info("Loaded pre-built FAISS index from disk")
        except Exception:
            logger.info("Building FAISS index from guideline docs...")
            vector_store.build_from_directory("data/guidelines")
        set_vector_store(vector_store)
        logger.info("FAISS Vector Store ready", chunks_loaded=len(vector_store._chunks or []))
    except Exception as e:
        logger.error("Failed to build FAISS store", error=str(e))

    # ── 3. Warm/Probe Local Ollama Service ─────────────────────
    try:
        ollama = OllamaClient(model=settings.ollama_router_model)
        is_ready = await ollama.ping()
        logger.info("Ollama service connectivity check", model=settings.ollama_router_model, ready=is_ready)
    except Exception as e:
        logger.warning("Ollama check skipped", error=str(e))

    logger.info("QForge Engine Ready [OK]")
    yield

    # ── 4. Shutdown Cleanup ────────────────────────────────────
    logger.info("Shutting down QForge...")
    try:
        await close_db()
        logger.info("MongoDB client closed")
    except Exception as e:
        logger.warning("Error during DB cleanup", error=str(e))
    logger.info("QForge shutdown complete")
