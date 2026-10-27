"""
QForge — WebSocket Streaming Endpoint
Primary real-time interface between the React frontend and the LangGraph agent.

Protocol:
  Client → Server:  JSON { "code": "...", "language": "python|sql", "session_id": "..." }
  Server → Client:  JSON stream of AgentStreamEvent objects (one per state transition)

Event types emitted to client:
  { "event": "node_start",    "node": "ROUTER",    "message": "..." }
  { "event": "node_complete", "node": "ROUTER",    "data": {...} }
  { "event": "repair_cycle",  "cycle": 2,          "errors": [...] }
  { "event": "final_result",  "status": "PASS",    "test_suite": "...", "audit": [...] }
  { "event": "error",         "message": "..." }
"""
import json
import uuid
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from backend.agents.graph import build_graph
from backend.agents.state import AgentState
from backend.db.client import get_db
from backend.db.repositories.audit_repo import save_audit_log
from backend.db.repositories.artifact_repo import save_artifact
from backend.core.app_state import get_vector_store
from backend.core.session_manager import session_manager

logger = logging.getLogger(__name__)
router = APIRouter()


async def _emit(ws: WebSocket, event: dict) -> None:
    """Send a JSON event frame to the WebSocket client."""
    try:
        await ws.send_text(json.dumps(event))
    except Exception:
        pass  # Client may have disconnected; suppress to avoid crashing agent loop


@router.websocket("/ws/qforge/{session_id}")
async def qforge_websocket(websocket: WebSocket, session_id: str):
    """
    Main WebSocket handler for a QForge agent session.
    Accepts code submission, streams agent lifecycle events,
    persists audit logs & artifacts, and closes after final result.
    """
    await websocket.accept()
    session_manager.register_socket(session_id, websocket)
    logger.info(f"[WS] Session {session_id} connected")

    try:
        # ── Receive code submission ───────────────────────────
        raw_message = await websocket.receive_text()
        payload = json.loads(raw_message)

        code_input = payload.get("code", "").strip()
        language = payload.get("language", "python").lower()

        if not code_input:
            await _emit(ws=websocket, event={"event": "error", "message": "No code provided."})
            await websocket.close()
            return

        # Normalize language aliases and support all 8 enterprise languages
        lang_alias_map = {
            "js": "javascript",
            "jsx": "javascript",
            "ts": "typescript",
            "tsx": "typescript",
            "py": "python",
            "cs": "csharp",
            "c#": "csharp",
            "rs": "rust",
            "golang": "go",
        }
        language = lang_alias_map.get(language, language)
        valid_languages = ("python", "javascript", "typescript", "java", "go", "rust", "csharp", "sql")
        if language not in valid_languages:
            # Auto-detect from code if unrecognized
            if "import " in code_input and ("react" in code_input or "from " in code_input):
                language = "javascript"
            elif "package " in code_input or "public class " in code_input:
                language = "java"
            elif "fn main" in code_input or "use std::" in code_input:
                language = "rust"
            elif "SELECT " in code_input.upper() or "CREATE TABLE" in code_input.upper():
                language = "sql"
            else:
                language = "python"

        # ── Build initial AgentState ───────────────────────────
        initial_state: AgentState = {
            "session_id": session_id,
            "raw_input": code_input,
            "language": language,
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

        await _emit(websocket, {
            "event": "session_start",
            "session_id": session_id,
            "language": language,
            "message": f"QForge session started. Language: {language.upper()}"
        })

        # ── Build and stream through LangGraph graph ───────────
        vector_store = get_vector_store()
        graph = build_graph(vector_store)

        current_state = initial_state

        async for event in graph.astream(initial_state, stream_mode="updates"):
            for node_name, node_output in event.items():
                node_upper = node_name.upper()

                # Detect repair cycle entry
                if node_name == "generator" and current_state.get("repair_cycle", 0) > 0:
                    await _emit(websocket, {
                        "event": "repair_cycle",
                        "cycle": current_state.get("repair_cycle", 0),
                        "errors": current_state.get("validation_errors", []),
                        "message": f"🔄 Self-heal cycle #{current_state.get('repair_cycle')} — sending errors back to Generator"
                    })

                # Emit node_start
                await _emit(websocket, {
                    "event": "node_start",
                    "node": node_upper,
                    "message": f"⚙️ {node_upper} node executing..."
                })

                # Merge output into current state for tracking
                current_state = {**current_state, **node_output}

                # Build rich node_complete payload
                node_data = {}
                if node_name == "router":
                    node_data = {
                        "complexity_score": current_state.get("complexity_score"),
                        "routing_path": current_state.get("routing_path"),
                        "language": current_state.get("language"),
                        "ast_fingerprint": current_state.get("ast_fingerprint"),
                        "context_chunks_count": len(current_state.get("context_chunks", [])),
                    }
                elif node_name == "generator":
                    suite = current_state.get("generated_test_suite", "")
                    node_data = {
                        "model_used": current_state.get("generation_model_used"),
                        "test_suite_preview": suite[:300] + "..." if len(suite) > 300 else suite,
                        "repair_cycle": current_state.get("repair_cycle", 0),
                    }
                elif node_name == "validator":
                    node_data = {
                        "validation_status": current_state.get("validation_status"),
                        "errors": current_state.get("validation_errors", []),
                        "repair_cycle": current_state.get("repair_cycle", 0),
                    }

                await _emit(websocket, {
                    "event": "node_complete",
                    "node": node_upper,
                    "data": node_data,
                    "audit_tail": current_state.get("audit_notes", [])[-3:],
                    "message": f"✅ {node_upper} complete"
                })

        # ── Deliver final result ───────────────────────────────
        final_status = current_state.get("validation_status", "FAIL")
        final_suite = current_state.get("final_test_suite", "")
        audit_notes = current_state.get("audit_notes", [])

        await _emit(websocket, {
            "event": "final_result",
            "status": final_status,
            "test_suite": final_suite or "",
            "model_used": current_state.get("generation_model_used", "unknown"),
            "routing_path": current_state.get("routing_path", "local"),
            "complexity_score": current_state.get("complexity_score", 0),
            "repair_cycles_used": current_state.get("repair_cycle", 0),
            "audit": audit_notes,
            "message": (
                "🎉 Test suite certified and ready!" if final_status == "PASS"
                else "⚠️ Generation failed after max repair cycles."
            ),
        })

        # ── Persist audit log and verified artifact to MongoDB ─
        try:
            db = get_db()
            await save_audit_log(db, session_id, current_state)
            if final_status == "PASS" and final_suite:
                await save_artifact(db, {
                    "artifact_id": f"art-{session_id}-{uuid.uuid4().hex[:6]}",
                    "session_id": session_id,
                    "language": language,
                    "verified_suite": final_suite,
                    "retry_count": current_state.get("repair_cycle", 0),
                    "validation_status": final_status,
                    "generation_model": current_state.get("generation_model_used", "unknown"),
                    "token_usage": {"input_chars": len(code_input), "output_chars": len(final_suite)},
                })

            # Record turn in persistent conversation history for ChatGPT-style recall
            from backend.db.repositories.chat_history_repo import save_turn
            await save_turn(
                db=db,
                session_id=session_id,
                user_prompt=code_input,
                language=language,
                generated_suite=final_suite or "",
                validation_status=final_status,
                repair_cycles=current_state.get("repair_cycle", 0),
                model_used=current_state.get("generation_model_used", "unknown"),
                repo_context=current_state.get("metadata", {}).get("repo", ""),
            )
        except Exception as db_err:
            logger.warning(f"[WS] Persistence warning for session {session_id}: {db_err}")

    except WebSocketDisconnect:
        logger.info(f"[WS] Session {session_id} — client disconnected")
    except json.JSONDecodeError:
        await _emit(websocket, {"event": "error", "message": "Invalid JSON payload received."})
    except Exception as e:
        logger.error(f"[WS] Session {session_id} — unhandled error: {e}", exc_info=True)
        await _emit(websocket, {"event": "error", "message": f"Internal agent error: {str(e)}"})
    finally:
        session_manager.unregister_socket(session_id)
        try:
            await websocket.close()
        except Exception:
            pass
        logger.info(f"[WS] Session {session_id} closed")
