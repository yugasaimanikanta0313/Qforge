"""
QForge Unit Tests — Validator Node
Validates syntax parsing, semantic error detection, and MAX_REPAIR_CYCLES guard.
"""
import pytest
from unittest.mock import patch, AsyncMock
from backend.agents.nodes.validator_node import validator_node, _hard_syntax_check
from backend.agents.state import AgentState


def test_hard_syntax_check_valid_python():
    code = "def test_example(): assert 1 == 1"
    errors = _hard_syntax_check(code, "python")
    assert len(errors) == 0


def test_hard_syntax_check_invalid_python():
    code = "def test_broken( assert 1 == 1"
    errors = _hard_syntax_check(code, "python")
    assert len(errors) > 0
    assert "SyntaxError" in errors[0]


def test_hard_syntax_check_valid_sql():
    code = "SELECT id, name FROM users WHERE id = 1"
    errors = _hard_syntax_check(code, "sql")
    assert len(errors) == 0


def test_hard_syntax_check_invalid_sql():
    code = "SELECT FROM WHERE"
    errors = _hard_syntax_check(code, "sql")
    assert len(errors) > 0


@pytest.mark.asyncio
async def test_validator_node_pass_flow(initial_agent_state):
    state = dict(initial_agent_state)
    state["generated_test_suite"] = "def test_ok(): assert True"

    mock_llm_json = '{"status": "PASS", "errors": [], "summary": "Valid suite"}'
    with patch("backend.agents.nodes.validator_node.OllamaClient") as mock_cls:
        instance = mock_cls.return_value
        instance.generate = AsyncMock(return_value=mock_llm_json)

        res = await validator_node(state)
        assert res["validation_status"] == "PASS"
        assert res["final_test_suite"] is not None


@pytest.mark.asyncio
async def test_validator_node_repair_cycle_increment(initial_agent_state):
    state = dict(initial_agent_state)
    state["generated_test_suite"] = "def test_invalid_syntax(:"  # syntax error
    state["repair_cycle"] = 0

    res = await validator_node(state)
    assert res["validation_status"] == "FAIL"
    assert res["repair_cycle"] == 1
    assert len(res["validation_errors"]) > 0


@pytest.mark.asyncio
async def test_validator_node_max_cycles_exhausted(initial_agent_state):
    state = dict(initial_agent_state)
    state["generated_test_suite"] = "invalid python code ("
    state["repair_cycle"] = 3  # threshold reached

    res = await validator_node(state)
    assert res["validation_status"] == "FAIL"
    assert res["final_test_suite"] is None
    assert any("exhausted" in note for note in res["audit_notes"])
