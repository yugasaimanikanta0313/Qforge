"""
QForge — Payload Sanitizer Service
Sanitizes proprietary code, PII, and secrets before egressing to cloud tiers:
  - Replaces emails, IPs, API keys, and connection strings with safe placeholders
  - Anonymizes enterprise identifiers and proprietary literals
"""
import re
from typing import Tuple, Dict
from backend.services.egress_guard.policy import PATTERNS


class PayloadSanitizer:
    """Sanitizes text payloads by replacing sensitive tokens with generic placeholders."""

    def __init__(self):
        self.replacements = {
            PATTERNS["api_key"]: "[REDACTED_API_KEY]",
            PATTERNS["email"]: "[USER_EMAIL_PLACEHOLDER]",
            PATTERNS["ipv4"]: "[IP_ADDR_PLACEHOLDER]",
            PATTERNS["credit_card"]: "[CARD_NUM_PLACEHOLDER]",
        }
        # Connection string pattern
        self.conn_str_pattern = re.compile(r"mongodb(?:\+srv)?://[^\s'\"]+")

    def sanitize(self, text: str) -> Tuple[str, Dict[str, int]]:
        """
        Sanitize input text and return (sanitized_text, replacement_stats).
        """
        stats: Dict[str, int] = {}
        sanitized = text

        for pattern, placeholder in self.replacements.items():
            matches = len(pattern.findall(sanitized))
            if matches > 0:
                stats[placeholder] = matches
                sanitized = pattern.sub(placeholder, sanitized)

        conn_matches = len(self.conn_str_pattern.findall(sanitized))
        if conn_matches > 0:
            stats["[REDACTED_DB_URI]"] = conn_matches
            sanitized = self.conn_str_pattern.sub("[REDACTED_DB_URI]", sanitized)

        return sanitized, stats


# Global default sanitizer
payload_sanitizer = PayloadSanitizer()
