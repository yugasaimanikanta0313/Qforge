"""
QForge Integration Tests — Agent StateGraph Loop
Validates end-to-end multi-node LangGraph orchestration with mock LLMs.
"""
import pytest
from unittest.mock import patch, AsyncMock
from backend.agents.graph import build_graph
from backend.agents.state import AgentState


@pytest.mark.asyncio
async def test_agent_graph_full_pass(mock_vector_store, initial_agent_state):
    graph = build_graph(mock_vector_store)

    router_res = '{"language": "python", "complexity_score": 3, "complexity_reason": "simple", "code_type": "math"}'
    gen_code = "def test_add(): assert add(1, 2) == 3"
    val_res = '{"status": "PASS", "errors": [], "summary": "Looks good"}'

    with patch("backend.agents.nodes.router_node.OllamaClient") as mock_router, \
         patch("backend.agents.nodes.generator_node.OllamaClient") as mock_gen, \
         patch("backend.agents.nodes.validator_node.OllamaClient") as mock_val:

        mock_router.return_value.generate = AsyncMock(return_value=router_res)
        mock_gen.return_value.generate = AsyncMock(return_value=gen_code)
        mock_val.return_value.generate = AsyncMock(return_value=val_res)

        final_state = None
        async for event in graph.astream(initial_agent_state, stream_mode="values"):
            final_state = event

        assert final_state is not None
        assert final_state["validation_status"] == "PASS"
        assert final_state["final_test_suite"] == gen_code
        assert final_state["repair_cycle"] == 0
