"""
QForge — Custom Exceptions
Enterprise exception hierarchy for the QForge framework.
"""


class QForgeError(Exception):
    """Base exception for all QForge framework errors."""

    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class AgentTimeoutError(QForgeError):
    """Raised when an agent node or LLM call exceeds execution timeout."""
    pass


class ValidationCycleExhausted(QForgeError):
    """Raised when max_repair_cycles threshold is breached in the self-heal loop."""
    pass


class EgressPolicyViolationError(QForgeError):
    """Raised when data violates cloud boundary policy (e.g. unscrubbed PII)."""
    pass


class VectorStoreError(QForgeError):
    """Raised when vector indexing or similarity search fails."""
    pass


class ASTParseError(QForgeError):
    """Raised when raw code cannot be parsed by AST or sqlglot."""
    pass
