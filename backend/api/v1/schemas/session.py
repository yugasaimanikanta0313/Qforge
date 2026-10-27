"""
QForge — Session Schemas
Pydantic schemas for session lifecycle management.
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field


class SessionCreate(BaseModel):
    """Payload to initiate a new software validation session."""
    code: str = Field(..., description="Raw source code or SQL query to test")
    language: str = Field("python", description="Language: 'python' or 'sql'")
    session_id: Optional[str] = Field(None, description="Optional custom session UUID")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class SessionResponse(BaseModel):
    """Response returned after session registration or query."""
    session_id: str
    language: str
    status: str
    complexity_score: Optional[int] = 0
    routing_path: Optional[str] = "local"
    created_at: Optional[datetime] = None
    websocket_url: str
