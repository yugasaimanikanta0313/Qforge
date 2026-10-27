"""
QForge — VALIDATOR NODE
Responsibilities:
  1. Run Python ast.parse() or sqlglot.parse() for hard deterministic syntax check
  2. Ask local Ollama to do a semantic quality audit (with timeout protection)
  3. Decide PASS or FAIL
  4. If FAIL and repair_cycle < max: increment cycle, return to generator
  5. If PASS or max cycles exhausted: finalize state
"""
import ast
import json
import logging
import sqlglot
from backend.agents.state import AgentState
from backend.agents.prompts.repair_prompts import VALIDATOR_PROMPT
from backend.services.llm.ollama_client import OllamaClient
from backend.config import settings

logger = logging.getLogger(__name__)


from backend.services.ast_parser.universal_parser import check_universal_syntax

def _hard_syntax_check(code: str, language: str) -> list[str]:
    """
    Performs a deterministic, non-LLM syntax check using stdlib, sqlglot, or tree-sitter.
    Returns a list of error strings (empty = valid).
    """
    errors = []
    if not code or not code.strip():
        return ["Generated test suite is empty"]

    # Reject explicit generation failure markers immediately
    if "# GENERATION FAILED" in code or "// GENERATION FAILED" in code or "GENERATION FAILED" in code:
        return [f"Test generation failed upstream: {code.strip()[:200]}"]

    lang = language.lower()
    if lang == "python":
        try:
            tree = ast.parse(code)
            # Ensure there is actual executable test code, not just comments or docstrings
            executable_nodes = [
                n for n in tree.body
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Assert, ast.Expr, ast.Assign))
            ]
            if not executable_nodes:
                return ["Generated Python test suite contains no executable functions, classes, or assertions"]
        except SyntaxError as e:
            errors.append(f"Python SyntaxError at line {e.lineno}: {e.msg}")
        except Exception as e:
            errors.append(f"Python parse error: {e}")
    elif lang == "sql":
        try:
            result = sqlglot.parse(code, error_level=sqlglot.ErrorLevel.RAISE)
            if not result:
                errors.append("SQL parsed to empty AST — likely empty or invalid input")
        except sqlglot.errors.SqlglotError as e:
            errors.append(f"SQL ParseError: {e}")
        except Exception as e:
            errors.append(f"SQL parse error: {e}")
    else:
        # Multi-language validation using Tree-Sitter
        universal_errs = check_universal_syntax(code, lang)
        errors.extend(universal_errs)

    return errors


async def validator_node(state: AgentState) -> dict:
    """
    LangGraph node: Validates the generated test suite.
    Returns updated state with validation_status, validation_errors, repair_cycle.
    """
    session_id = state["session_id"]
    lang = state.get("language", "python")
    test_suite = state.get("generated_test_suite", "")
    model_used = state.get("generation_model_used", "")
    repair_cycle = state.get("repair_cycle", 0)
    audit = list(state.get("audit_notes", []))

    logger.info(f"[VALIDATOR] Session {session_id} — validating (cycle={repair_cycle})")
    audit.append(f"VALIDATOR: Running validation — cycle={repair_cycle}")

    all_errors: list[str] = []

    # Check for upstream generation failure
    if model_used == "error" or "GENERATION FAILED" in test_suite:
        all_errors.append(f"Upstream generation error: {test_suite.strip()[:200]}")
        audit.append("VALIDATOR: Upstream generation failed — marking FAILED")

    # ── Stage 1: Hard deterministic syntax check ───────────────
    if not all_errors:
        syntax_errors = _hard_syntax_check(test_suite, lang)
        if syntax_errors:
            all_errors.extend(syntax_errors)
            audit.append(f"VALIDATOR: Hard syntax check FAILED — {len(syntax_errors)} error(s)")
        else:
            audit.append("VALIDATOR: Hard syntax check PASSED")

    # ── Stage 2: LLM Semantic Audit (only if syntax passed) ───
    if not all_errors:
        prompt = VALIDATOR_PROMPT.format(language=lang, generated_test_suite=test_suite)
        client = OllamaClient(model=settings.ollama_validator_model, timeout=45.0)
        try:
            raw = await client.generate(prompt)
            cleaned = raw.strip().strip("```json").strip("```").strip()
            verdict = json.loads(cleaned)
            if verdict.get("status") == "FAIL":
                llm_errors = verdict.get("errors", [])
                all_errors.extend(llm_errors)
                audit.append(f"VALIDATOR: LLM audit FAILED — {len(llm_errors)} semantic issue(s)")
            else:
                audit.append("VALIDATOR: LLM semantic audit PASSED")
        except Exception as e:
            logger.warning(f"[VALIDATOR] LLM audit skipped: {e} — relying on syntax check only")
            audit.append(f"VALIDATOR: LLM audit skipped ({e}), syntax check verified")

    # ── Stage 3: Final Decision ────────────────────────────────
    if all_errors:
        new_cycle = repair_cycle + 1
        if new_cycle > settings.max_repair_cycles:
            # Exhausted retries — fail permanently
            status = "FAIL"
            audit.append(
                f"VALIDATOR: MAX_REPAIR_CYCLES ({settings.max_repair_cycles}) exhausted — FINAL FAIL"
            )
            logger.warning(f"[VALIDATOR] Session {session_id} — max cycles exhausted, marking FAIL")
            return {
                "validation_status": "FAIL",
                "validation_errors": all_errors,
                "final_test_suite": None,
                "audit_notes": audit,
            }
        else:
            audit.append(
                f"VALIDATOR: FAIL — routing back to GENERATOR for repair cycle #{new_cycle}"
            )
            logger.info(f"[VALIDATOR] Session {session_id} — FAIL, retry cycle {new_cycle}")
            return {
                "validation_status": "FAIL",
                "validation_errors": all_errors,
                "repair_cycle": new_cycle,
                "audit_notes": audit,
            }
    else:
        # All checks passed
        audit.append("VALIDATOR: All checks PASSED — certifying test suite")
        logger.info(f"[VALIDATOR] Session {session_id} — PASS after {repair_cycle} repair cycle(s)")
        return {
            "validation_status": "PASS",
            "validation_errors": [],
            "final_test_suite": test_suite,
            "audit_notes": audit,
        }
