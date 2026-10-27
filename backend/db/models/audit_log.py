"""
QForge — Audit Log Model Schema
Pydantic document model representing an audit log entry for compliance and tracking.
"""
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class AuditLogModel(BaseModel):
    """Audit log entry representation in MongoDB."""
    session_id: str = Field(..., description="Target session ID")
    node: str = Field(..., description="LangGraph node name (ROUTER | GENERATOR | VALIDATOR)")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    input_hash: Optional[str] = Field(None, description="SHA256 fingerprint of input")
    outcome: str = Field(..., description="Outcome of execution (PASS | FAIL | RETRY | ERROR)")
    duration_ms: Optional[float] = Field(None, description="Execution duration in ms")
    details: Dict[str, Any] = Field(default_factory=dict, description="Metadata and audit trail notes")
