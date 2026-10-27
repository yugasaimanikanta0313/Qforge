"""
QForge — FastAPI Application Entry Point
Defines the app factory, lifespan hooks, CORS configuration, and route registration.

Startup sequence:
  1. Initialize MongoDB connection (Motor async client)
  2. Load FAISS vector store (build from guidelines/ directory or disk)
  3. Register REST (v1) and WebSocket routers
  4. Server is ready to accept connections
"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
from backend.core.lifespan import lifespan
from backend.api.v1.router import api_v1_router, ws_router

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Factory function that creates and configures the FastAPI application."""
    app = FastAPI(
        title="QForge API",
        description="Hybrid Multi-Agent RAG Platform for Enterprise Software Validation",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # ── CORS — allow React dev server ─────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Register Routers ───────────────────────────────────────
    app.include_router(ws_router)        # WebSocket: /ws/qforge/{session_id}
    app.include_router(api_v1_router)    # REST:      /api/v1/*

    # ── Mount Frontend Static Files if built ──────────────────
    import os
    from fastapi.staticfiles import StaticFiles

    frontend_dist = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "dist"))
    if os.path.exists(frontend_dist):
        app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")
    else:
        @app.get("/", tags=["Root"])
        async def root():
            return {
                "name": "QForge Framework API",
                "version": "1.0.0",
                "status": "operational",
                "docs": "/docs",
                "health": "/api/v1/health",
            }

    return app


# Application instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level="debug" if settings.debug else "info",
    )
