"""
QForge — LangGraph StateGraph Definition
Wires together: ROUTER → GENERATOR → VALIDATOR
with a cyclic self-heal edge back to GENERATOR on validation failure.

Graph structure:
  START → router → generator → validator ─┐
                      ↑                    │ (FAIL + cycles remaining)
                      └────────────────────┘
                                           │ (PASS or max cycles exhausted)
                                          END
"""
import functools
import logging
from typing import Any
from langgraph.graph import StateGraph, END
from backend.agents.state import AgentState
from backend.agents.nodes.router_node import router_node
from backend.agents.nodes.generator_node import generator_node
from backend.agents.nodes.validator_node import validator_node
from backend.services.vector_store.faiss_store import FaissVectorStore
from backend.config import settings

logger = logging.getLogger(__name__)


def _should_repair_or_end(state: AgentState) -> str:
    """
    Conditional edge function for LangGraph.
    Returns the name of the next node to route to.
    """
    status = state.get("validation_status", "PENDING")
    repair_cycle = state.get("repair_cycle", 0)

    if status == "PASS":
        logger.info(f"[GRAPH] Routing to END — validation PASSED")
        return "end"
    elif repair_cycle > settings.max_repair_cycles:
        logger.warning(f"[GRAPH] Routing to END — max repair cycles exhausted")
        return "end"
    else:
        logger.info(f"[GRAPH] Routing back to GENERATOR — repair cycle {repair_cycle}")
        return "generator"


def build_graph(vector_store: FaissVectorStore) -> Any:
    """
    Constructs and compiles the QForge LangGraph StateGraph.
    The vector_store is injected via functools.partial so nodes
    remain pure functions while sharing the singleton FAISS instance.
    """
    graph = StateGraph(AgentState)

    # ── Register Nodes ─────────────────────────────────────────
    # Router gets vector_store injected; others are plain async funcs
    graph.add_node(
        "router",
        functools.partial(router_node, vector_store=vector_store)
    )
    graph.add_node("generator", generator_node)
    graph.add_node("validator", validator_node)

    # ── Define Edges ───────────────────────────────────────────
    graph.set_entry_point("router")
    graph.add_edge("router", "generator")
    graph.add_edge("generator", "validator")

    # Cyclic conditional edge: validator → generator (repair) OR end
    graph.add_conditional_edges(
        "validator",
        _should_repair_or_end,
        {
            "generator": "generator",
            "end": END,
        },
    )

    compiled = graph.compile()
    logger.info("[GRAPH] QForge StateGraph compiled successfully")
    return compiled
