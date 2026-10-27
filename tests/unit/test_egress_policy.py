"""
QForge Unit Tests — Egress Policy & Sanitizer
Validates cloud egress gating, PII detection, and payload anonymization.
"""
import pytest
from backend.services.egress_guard.policy import EgressPolicy
from backend.services.egress_guard.sanitizer import PayloadSanitizer


def test_complexity_gate_rejection():
    policy = EgressPolicy(complexity_threshold=7)
    allowed, violations = policy.evaluate_egress(complexity_score=4, payload_text="def foo(): pass")
    assert allowed is False
    assert any("below threshold" in v for v in violations)


def test_complexity_gate_approval():
    policy = EgressPolicy(complexity_threshold=7)
    allowed, violations = policy.evaluate_egress(complexity_score=8, payload_text="def complex_algorithm(): pass")
    assert allowed is True
    assert len(violations) == 0


def test_pii_detection():
    policy = EgressPolicy()
    text_with_email = "Contact security at admin@tcs.corp for access."
    detected = policy.scan_for_pii(text_with_email)
    assert "email" in detected

    text_with_ip = "Connect to database server at 192.168.1.100:5432"
    detected_ip = policy.scan_for_pii(text_with_ip)
    assert "ipv4" in detected_ip


def test_payload_sanitizer():
    sanitizer = PayloadSanitizer()
    raw = "Connect with key api_key='sk_live_1234567890abcdef' or mail test@example.com at 10.0.0.1"
    sanitized, stats = sanitizer.sanitize(raw)
    assert "test@example.com" not in sanitized
    assert "[USER_EMAIL_PLACEHOLDER]" in sanitized
    assert "10.0.0.1" not in sanitized
    assert "[IP_ADDR_PLACEHOLDER]" in sanitized
