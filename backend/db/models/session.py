"""
QForge — Session Model Schema
Pydantic document model representing an agent validation session.
"""
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class SessionModel(BaseModel):
    """Session representation in MongoDB."""
    session_id: str = Field(..., description="Unique session identifier")
    language: str = Field(default="python", description="Code language (python | sql)")
    raw_input: str = Field(..., description="Original raw code or query")
    complexity_score: int = Field(default=0, ge=0, le=10)
    routing_path: str = Field(default="local", description="local | cloud")
    status: str = Field(default="INIT", description="INIT | RUNNING | COMPLETED | FAILED")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)
