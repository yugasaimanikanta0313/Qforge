"""
QForge — GENERATOR NODE
Responsibilities:
  1. Decide which LLM to call based on routing_path in state
  2. On first pass: use GENERATOR_PROMPT with RAG context
  3. On repair pass (repair_cycle > 0): use REPAIR_PROMPT with error trace
  4. Apply Egress Policy & Payload Sanitizer before cloud dispatch
  5. Call local Ollama or cloud Gemini accordingly
  6. Store draft test suite in state
"""
import logging
from backend.agents.state import AgentState
from backend.agents.prompts.generation_prompts import GENERATOR_PROMPT
from backend.agents.prompts.repair_prompts import REPAIR_PROMPT
from backend.services.llm.ollama_client import OllamaClient
from backend.services.llm.gemini_client import GeminiClient
from backend.services.egress_guard.policy import egress_policy
from backend.services.egress_guard.sanitizer import payload_sanitizer
from backend.config import settings

logger = logging.getLogger(__name__)


import re

def strip_code_fences(text: str) -> str:
    """Safely extracts code block without using str.strip(chars) which corrupts trailing letters."""
    if not text:
        return ""
    text = text.strip()
    match = re.search(r"```(?:python|sql|py)?\r?\n([\s\S]*?)\r?\n```", text)
    if match:
        return match.group(1).strip()
    match_general = re.search(r"```\r?\n([\s\S]*?)\r?\n```", text)
    if match_general:
        return match_general.group(1).strip()
    text = re.sub(r"^```[a-zA-Z0-9_-]*\r?\n?", "", text)
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


async def generator_node(state: AgentState) -> dict:
    """
    LangGraph node: Synthesizes test suite via local or cloud LLM.
    Handles both initial generation and repair passes.
    """
    session_id = state["session_id"]
    repair_cycle = state.get("repair_cycle", 0)
    routing_path = state.get("routing_path", "local")
    lang = state.get("language", "python")
    context_chunks = state.get("context_chunks", [])
    audit = list(state.get("audit_notes", []))

    context_text = "\n\n".join(context_chunks) if context_chunks else "No enterprise guidelines loaded."

    # ── Build prompt based on whether this is a repair pass ───
    if repair_cycle > 0:
        logger.info(f"[GENERATOR] Session {session_id} — REPAIR pass #{repair_cycle}")
        audit.append(f"GENERATOR: Entering repair cycle #{repair_cycle} — fixing validation errors")
        prompt = REPAIR_PROMPT.format(
            language=lang,
            raw_input=state["raw_input"],
            generated_test_suite=state.get("generated_test_suite", ""),
            validation_errors="\n".join(state.get("validation_errors", [])),
            context_chunks=context_text,
        )
    else:
        logger.info(f"[GENERATOR] Session {session_id} — INITIAL generation, path={routing_path}")
        audit.append(f"GENERATOR: Initial test synthesis — routing_path={routing_path.upper()}")
        prompt = GENERATOR_PROMPT.format(
            language=lang,
            raw_input=state["raw_input"],
            context_chunks=context_text,
        )

    # ── Select LLM & Fallback Execution ─────────────────────────
    # Primary: Attempt Gemini cloud tier (if key configured)
    # Fallback: Local Qwen model (Ollama)
    test_suite = None
    model_used = None

    # Step A: Try Gemini cloud tier first if API key is present
    if settings.gemini_api_key:
        try:
            sanitized_prompt, sanitization_stats = payload_sanitizer.sanitize(prompt)
            if sanitization_stats:
                audit.append(
                    f"GENERATOR: Sanitized {sum(sanitization_stats.values())} proprietary literal(s) prior to cloud egress"
                )

            logger.info(f"[GENERATOR] Primary synthesis via Gemini API ({settings.gemini_model})")
            audit.append(f"GENERATOR: Dispatching primary generation to Gemini ({settings.gemini_model})")
            client = GeminiClient(model=settings.gemini_model)
            raw_output = await client.generate(sanitized_prompt)
            test_suite = strip_code_fences(raw_output)
            model_used = f"gemini:{settings.gemini_model}"
            audit.append(f"GENERATOR: Received {len(test_suite)} chars from Gemini cloud tier")
        except Exception as ge:
            err_text = str(ge)
            logger.warning(
                f"[GENERATOR] Gemini primary generation failed: {ge}. Falling back to local Ollama (qwen)."
            )
            if "429" in err_text or "RESOURCE_EXHAUSTED" in err_text:
                fallback_reason = "Gemini quota exhausted (429)"
            else:
                fallback_reason = f"Gemini error: {ge}"
            audit.append(
                f"GENERATOR: {fallback_reason} — smoothly falling back to local Qwen ({settings.ollama_generator_model})"
            )

    # Step B: Fallback to local Ollama (Qwen) if Gemini failed or not configured
    if not test_suite:
        try:
            logger.info(f"[GENERATOR] Synthesizing via local Ollama ({settings.ollama_generator_model})")
            audit.append(f"GENERATOR: Dispatching to local Ollama ({settings.ollama_generator_model})")
            client = OllamaClient(model=settings.ollama_generator_model, timeout=180.0)
            raw_output = await client.generate(prompt)
            test_suite = strip_code_fences(raw_output)
            model_used = f"ollama:{settings.ollama_generator_model} (fallback)"
            audit.append(f"GENERATOR: Received {len(test_suite)} chars from local Ollama")
        except Exception as oe:
            logger.error(f"[GENERATOR] Local Ollama also failed: {oe}")
            test_suite = f"# GENERATION FAILED\n# Error: {oe}\n"
            model_used = "error"
            audit.append(f"GENERATOR: Both Gemini and local Ollama failed — {oe}")

    return {
        "generated_test_suite": test_suite,
        "generation_model_used": model_used,
        "validation_status": "PENDING",
        "audit_notes": audit,
    }
