"""
QForge — Audit Schemas
Pydantic schemas for compliance audit trail and execution traces.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class AuditLogEntry(BaseModel):
    """Single audit log document representation."""
    session_id: str
    timestamp: datetime
    language: Optional[str] = None
    complexity_score: Optional[int] = None
    routing_path: Optional[str] = None
    validation_status: Optional[str] = None
    repair_cycles_used: Optional[int] = 0
    generation_model_used: Optional[str] = None
    validation_errors: Optional[List[str]] = Field(default_factory=list)
    audit_notes: Optional[List[str]] = Field(default_factory=list)
    ast_fingerprint: Optional[Dict[str, Any]] = Field(default_factory=dict)
    input_length: Optional[int] = 0
    output_length: Optional[int] = 0


class AuditTraceResponse(BaseModel):
    """Response containing execution records for a specific session."""
    session_id: str
    count: int
    records: List[Dict[str, Any]]
