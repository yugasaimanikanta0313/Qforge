"""
QForge — LangGraph Agent State Definition
The AgentState TypedDict is the single shared mutable state
object passed between every node in the LangGraph StateGraph.
"""
from typing import TypedDict, Optional, Literal


class AgentState(TypedDict):
    # ── Input ──────────────────────────────────────────────────
    session_id: str
    raw_input: str                           # Original code / SQL submitted by user
    language: Literal["python", "sql"]       # Detected or user-provided language

    # ── Router Node outputs ────────────────────────────────────
    complexity_score: int                    # 0–10; >= threshold → cloud tier
    routing_path: Literal["local", "cloud"]  # Which LLM tier was selected
    ast_fingerprint: dict                    # AST-parsed structure metadata
    context_chunks: list[str]               # Top-K retrieved guideline chunks from FAISS

    # ── Generator Node outputs ─────────────────────────────────
    generated_test_suite: str               # Raw LLM-generated test code (may have errors)
    generation_model_used: str              # Which model produced this draft

    # ── Validator Node outputs ─────────────────────────────────
    validation_status: Literal["PASS", "FAIL", "PENDING"]
    validation_errors: list[str]            # Syntax / assertion errors found
    repair_cycle: int                       # Current retry count (0 = first attempt)

    # ── Final outputs ──────────────────────────────────────────
    final_test_suite: Optional[str]         # Verified and certified test suite
    audit_notes: list[str]                  # Step-by-step audit trail
