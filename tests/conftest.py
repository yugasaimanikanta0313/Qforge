"""
QForge Test Suite — Shared Fixtures
Provides pytest fixtures: mock vector store, mock LLM clients, test states.
"""
import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock
from backend.agents.state import AgentState
from backend.services.vector_store.base import BaseVectorStore
from backend.services.llm.base import BaseLLMClient


class MockVectorStore(BaseVectorStore):
    """In-memory mock vector store returning deterministic guidelines."""

    def __init__(self, demo_chunks: list[str] | None = None):
        self._chunks = demo_chunks or [
            "Test functions must be prefixed with test_.",
            "SQL assertions must validate count and null handling.",
            "Use Arrange-Act-Assert structure.",
        ]
        self._is_loaded = True

    def build_from_directory(self, dir_path: str) -> None:
        pass

    def search(self, query: str, top_k: int = 5) -> list[str]:
        return self._chunks[:top_k]

    def save(self, index_path: str, metadata_path: str) -> None:
        pass

    def load(self, index_path: str, metadata_path: str) -> None:
        pass


class MockLLMClient(BaseLLMClient):
    """Mock LLM client returning scripted responses."""

    def __init__(self, response: str = ""):
        self.response = response

    async def generate(self, prompt: str, **kwargs) -> str:
        return self.response

    async def stream(self, prompt: str, **kwargs):
        yield self.response


@pytest.fixture
def mock_vector_store():
    return MockVectorStore()


@pytest.fixture
def sample_python_code():
    return """
def add(a: int, b: int) -> int:
    return a + b
"""


@pytest.fixture
def sample_sql_query():
    return """
SELECT user_id, email FROM users WHERE active = 1
"""


@pytest.fixture
def initial_agent_state(sample_python_code):
    return {
        "session_id": "test-session-123",
        "raw_input": sample_python_code.strip(),
        "language": "python",
        "complexity_score": 0,
        "routing_path": "local",
        "ast_fingerprint": {},
        "context_chunks": [],
        "generated_test_suite": "",
        "generation_model_used": "",
        "validation_status": "PENDING",
        "validation_errors": [],
        "repair_cycle": 0,
        "final_test_suite": None,
        "audit_notes": [],
    }
