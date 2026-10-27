"""
QForge Unit Tests — Router Node
Validates routing decision logic, complexity thresholds, and state mutation.
"""
import pytest
from unittest.mock import patch, AsyncMock
from backend.agents.nodes.router_node import router_node, _compute_ast_complexity
from backend.agents.state import AgentState


@pytest.mark.asyncio
async def test_compute_ast_complexity_simple():
    fingerprint = {"function_count": 1, "class_count": 0, "async_function_count": 0, "decorator_count": 0}
    score = _compute_ast_complexity(fingerprint, "python")
    assert score <= 5


@pytest.mark.asyncio
async def test_compute_ast_complexity_complex():
    fingerprint = {"function_count": 3, "class_count": 2, "async_function_count": 2, "decorator_count": 2}
    score = _compute_ast_complexity(fingerprint, "python")
    assert score >= 7


@pytest.mark.asyncio
async def test_router_node_local_path(mock_vector_store, initial_agent_state):
    # Mock OllamaClient to return low complexity JSON
    mock_json = '{"language": "python", "complexity_score": 3, "complexity_reason": "simple function", "code_type": "math"}'
    with patch("backend.agents.nodes.router_node.OllamaClient") as mock_client_cls:
        instance = mock_client_cls.return_value
        instance.generate = AsyncMock(return_value=mock_json)

        res = await router_node(initial_agent_state, mock_vector_store)
        assert res["routing_path"] == "local"
        assert res["complexity_score"] == 3
        assert len(res["context_chunks"]) > 0


@pytest.mark.asyncio
async def test_router_node_cloud_path(mock_vector_store, initial_agent_state):
    # Mock OllamaClient to return high complexity JSON
    mock_json = '{"language": "python", "complexity_score": 9, "complexity_reason": "distributed cache", "code_type": "cache"}'
    with patch("backend.agents.nodes.router_node.OllamaClient") as mock_client_cls:
        instance = mock_client_cls.return_value
        instance.generate = AsyncMock(return_value=mock_json)

        res = await router_node(initial_agent_state, mock_vector_store)
        assert res["routing_path"] == "cloud"
        assert res["complexity_score"] == 9
