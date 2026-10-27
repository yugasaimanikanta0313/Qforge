"""
QForge — Streaming Event Schemas
Pydantic schemas for WebSocket telemetry and event frames.
"""
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field


class TokenDelta(BaseModel):
    """Token chunk emitted during LLM streaming."""
    delta: str
    node: str = "GENERATOR"


class ErrorEvent(BaseModel):
    """Error frame emitted when agent encounters unrecoverable failure."""
    event: Literal["error"] = "error"
    message: str
    node: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class AgentStreamEvent(BaseModel):
    """Universal frame schema emitted over WebSocket."""
    event: str = Field(..., description="node_start | node_complete | repair_cycle | final_result | error")
    node: Optional[str] = None
    data: Optional[Dict[str, Any]] = Field(default_factory=dict)
    message: Optional[str] = None
    cycle: Optional[int] = None
    errors: Optional[List[str]] = None
    status: Optional[str] = None
    test_suite: Optional[str] = None
    routing_path: Optional[str] = None
    model_used: Optional[str] = None
    complexity_score: Optional[int] = None
    audit: Optional[List[str]] = None
