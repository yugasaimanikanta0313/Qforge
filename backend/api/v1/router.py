"""
QForge — API v1 Router Aggregator
Combines all v1 endpoint routers (sessions, audit, health, websocket) into a unified APIRouter.
"""
from fastapi import APIRouter
from backend.api.v1.endpoints.sessions import router as sessions_router
from backend.api.v1.endpoints.audit import router as audit_router
from backend.api.v1.endpoints.health import router as health_router
from backend.api.v1.endpoints.github import router as github_router
from backend.api.v1.endpoints.websocket import router as ws_router

api_v1_router = APIRouter(prefix="/api/v1")

# Include sub-routers
api_v1_router.include_router(sessions_router)
api_v1_router.include_router(audit_router)
api_v1_router.include_router(health_router)
api_v1_router.include_router(github_router)

__all__ = ["api_v1_router", "ws_router"]
