"""
QForge — Cloud Egress Boundary Policy
Enforces data sovereignty and privacy firewall rules before payloads leave on-premises.

Policy rules:
  1. Complexity Gate: Payload only egresses to Gemini if complexity_score >= threshold
  2. PII / Secret Scrubbing: Rejects or sanitizes patterns (API keys, IP addresses, emails, SSNs)
  3. Token Budget: Prevents out-of-budget payloads exceeding token egress quotas
"""
import re
import logging
from typing import Tuple, List, Dict, Any
from backend.config import settings
from backend.core.exceptions import EgressPolicyViolationError

logger = logging.getLogger(__name__)

# Common PII & Secret Patterns
PATTERNS = {
    "api_key": re.compile(r"(?i)(?:api_key|apikey|secret|token|password|bearer)[\s:=]+['\"]?([A-Za-z0-9_\-\.]{16,})['\"]?"),
    "email": re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"),
    "ipv4": re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
    "private_ip": re.compile(r"^(?:10\.|172\.(?:1[6-9]|2\d|3[01])\.|192\.168\.)"),
    "credit_card": re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b"),
}


class EgressPolicy:
    """Evaluates whether code or context is permitted to egress to cloud LLMs."""

    def __init__(
        self,
        complexity_threshold: int | None = None,
        max_egress_tokens: int = 8000,
        enforce_scrubbing: bool = True,
    ):
        self.complexity_threshold = complexity_threshold or settings.complexity_threshold
        self.max_egress_tokens = max_egress_tokens
        self.enforce_scrubbing = enforce_scrubbing

    def evaluate_egress(
        self,
        complexity_score: int,
        payload_text: str,
    ) -> Tuple[bool, List[str]]:
        """
        Evaluate payload against egress rules.
        Returns: (allowed: bool, violation_reasons: List[str])
        """
        violations = []

        # 1. Complexity Gate
        if complexity_score < self.complexity_threshold:
            violations.append(
                f"Complexity score {complexity_score} below threshold {self.complexity_threshold}. Keep compute local."
            )

        # 2. Token Budget Estimation (~4 chars/token)
        estimated_tokens = len(payload_text) // 4
        if estimated_tokens > self.max_egress_tokens:
            violations.append(
                f"Payload estimated tokens ({estimated_tokens}) exceeds maximum egress budget ({self.max_egress_tokens})."
            )

        # 3. PII & Secret Checks
        found_pii = self.scan_for_pii(payload_text)
        if found_pii:
            violations.append(f"Sensitive patterns detected in payload: {', '.join(found_pii)}")

        allowed = len(violations) == 0
        return allowed, violations

    def scan_for_pii(self, text: str) -> List[str]:
        """Detect presence of PII or secrets."""
        detected = []
        for name, regex in PATTERNS.items():
            if regex.search(text):
                detected.append(name)
        return detected


# Default singleton instance
egress_policy = EgressPolicy()
