"""
QForge — Prompt Templates Registry
Re-exports prompt templates for backwards compatibility and ease of iteration.
"""
from backend.agents.prompts.routing_prompts import ROUTER_PROMPT
from backend.agents.prompts.generation_prompts import GENERATOR_PROMPT
from backend.agents.prompts.repair_prompts import REPAIR_PROMPT, VALIDATOR_PROMPT

__all__ = [
    "ROUTER_PROMPT",
    "GENERATOR_PROMPT",
    "REPAIR_PROMPT",
    "VALIDATOR_PROMPT",
]
