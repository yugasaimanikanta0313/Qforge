"""
QForge E2E Tests — Full Pipeline Execution
End-to-end integration test with live components: FAISS vector retrieval,
AST analysis, routing, LLM synthesis, and validation.
"""
import pytest
from backend.config import settings
from backend.services.vector_store.faiss_store import FaissVectorStore
from backend.agents.graph import build_graph
from backend.agents.state import AgentState


@pytest.mark.asyncio
async def test_full_pipeline_python_e2e():
    """Run real FAISS search and full StateGraph pipeline on simple Python code."""
    vs = FaissVectorStore(embedding_model=settings.embedding_model)
    vs.build_from_directory("data/guidelines")

    graph = build_graph(vs)

    state: AgentState = {
        "session_id": "e2e-test-session",
        "raw_input": "def square(x):\n    return x * x\n",
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

    final_state = None
    async for event in graph.astream(state, stream_mode="values"):
        final_state = event

    assert final_state is not None
    assert final_state["validation_status"] in ("PASS", "FAIL")
    assert len(final_state["audit_notes"]) > 0
    assert final_state["complexity_score"] > 0
