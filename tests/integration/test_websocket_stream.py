"""
QForge Integration Tests — WebSocket Stream & Event Sequence
Validates real-time WebSocket protocol and emitted event frames.
"""
import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from backend.main import app
from backend.core.app_state import set_vector_store


def test_websocket_stream_lifecycle(mock_vector_store):
    set_vector_store(mock_vector_store)
    client = TestClient(app)

    router_res = '{"language": "python", "complexity_score": 3, "complexity_reason": "simple", "code_type": "math"}'
    gen_code = "def test_hello(): assert True"
    val_res = '{"status": "PASS", "errors": [], "summary": "Valid"}'

    with patch("backend.agents.nodes.router_node.OllamaClient") as mock_router, \
         patch("backend.agents.nodes.generator_node.OllamaClient") as mock_gen, \
         patch("backend.agents.nodes.validator_node.OllamaClient") as mock_val:

        mock_router.return_value.generate = AsyncMock(return_value=router_res)
        mock_gen.return_value.generate = AsyncMock(return_value=gen_code)
        mock_val.return_value.generate = AsyncMock(return_value=val_res)

        with client.websocket_connect("/ws/qforge/test-session-ws-1") as websocket:
            # Send initial code submission
            websocket.send_json({
                "code": "def hello(): pass",
                "language": "python",
                "session_id": "test-session-ws-1"
            })

            events_received = []
            while True:
                try:
                    data = websocket.receive_json()
                    events_received.append(data.get("event"))
                    if data.get("event") == "final_result":
                        break
                except Exception:
                    break

            assert "session_start" in events_received
            assert "node_start" in events_received
            assert "node_complete" in events_received
            assert "final_result" in events_received
