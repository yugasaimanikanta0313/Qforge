"""
QForge — Test Artifact Model Schema
Pydantic document model representing generated and verified test suites.
"""
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class TestArtifactModel(BaseModel):
    """Verified test artifact document representation in MongoDB."""
    artifact_id: str = Field(..., description="Unique artifact identifier")
    session_id: str = Field(..., description="Associated session ID")
    language: str = Field(..., description="Language (python | sql)")
    verified_suite: str = Field(..., description="Certified test suite code")
    retry_count: int = Field(default=0, description="Self-heal repair cycles taken")
    validation_status: str = Field(default="PASS", description="PASS | FAIL")
    generation_model: str = Field(..., description="LLM used for synthesis")
    token_usage: Dict[str, int] = Field(default_factory=dict, description="Estimated prompt and completion tokens")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
