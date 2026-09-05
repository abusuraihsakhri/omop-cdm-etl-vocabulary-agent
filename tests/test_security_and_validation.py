"""
Security and input validation tests for omop-cdm-etl-vocabulary-agent.
"""
import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from pydantic import ValidationError

from agents.base import AuditTrail, PHIGuard, SecurityException, assert_no_phi
from agents.models import SystemTaskPayload, _validate_identifier


class TestAuditSecurity:
    """Tests for audit trail security requirements."""

    def test_audit_trail_requires_secret_key(self):
        """AuditTrail should fail without AUDIT_SECRET_KEY."""
        original = os.environ.pop("AUDIT_SECRET_KEY", None)
        try:
            with pytest.raises(SecurityException, match="AUDIT_SECRET_KEY"):
                AuditTrail()
        finally:
            if original:
                os.environ["AUDIT_SECRET_KEY"] = original

    def test_audit_trail_rejects_short_key(self):
        """AuditTrail should reject keys shorter than 16 chars."""
        with pytest.raises(SecurityException, match="at least 16 characters"):
            AuditTrail(secret_key="short")

    def test_audit_trail_accepts_valid_key(self):
        """AuditTrail should work with a valid key."""
        trail = AuditTrail(secret_key="this-is-a-valid-key-for-testing")
        assert trail is not None

    def test_audit_trail_custom_key_overrides_env(self):
        """Explicit key parameter should take precedence."""
        os.environ["AUDIT_SECRET_KEY"] = "env-key-that-is-long-enough-for-test"
        trail = AuditTrail(secret_key="explicit-key-for-test-validation")
        assert trail is not None


class TestInputValidation:
    """Tests for input validation on SystemTaskPayload."""

    def test_valid_task_id(self):
        """Standard task IDs should be accepted."""
        p = SystemTaskPayload(task_id="TASK-001", target_identifier="KEY-01", primary_metric=10.0)
        assert p.task_id == "TASK-001"

    def test_invalid_task_id_with_special_chars(self):
        """Task IDs with special characters should be rejected."""
        with pytest.raises(ValidationError):
            SystemTaskPayload(task_id="TASK-001; DROP TABLE", target_identifier="KEY-01", primary_metric=10.0)

    def test_invalid_task_id_path_traversal(self):
        """Task IDs with path traversal patterns should be rejected."""
        with pytest.raises(ValidationError):
            SystemTaskPayload(task_id="../../../etc/passwd", target_identifier="KEY-01", primary_metric=10.0)

    def test_empty_task_id_rejected(self):
        """Empty task IDs should be rejected."""
        with pytest.raises(ValidationError):
            SystemTaskPayload(task_id="", target_identifier="KEY-01", primary_metric=10.0)

    def test_status_descriptor_uppercased(self):
        """Status descriptors should be normalized to uppercase."""
        p = SystemTaskPayload(task_id="T1", target_identifier="K1", primary_metric=10.0, status_descriptor="discordant")
        assert p.status_descriptor == "DISCORDANT"

    def test_status_descriptor_too_long(self):
        """Overly long status descriptors should be rejected."""
        with pytest.raises(ValidationError, match="128 characters"):
            SystemTaskPayload(task_id="T1", target_identifier="K1", primary_metric=10.0, status_descriptor="A" * 200)

    def test_validate_identifier_function(self):
        """Direct test of identifier validation."""
        assert _validate_identifier("VALID_ID-123", "test") == "VALID_ID-123"
        with pytest.raises(ValueError):
            _validate_identifier("", "test")
        with pytest.raises(ValueError):
            _validate_identifier("has spaces", "test")
        with pytest.raises(ValueError):
            _validate_identifier("a" * 65, "test")


class TestPHIGuard:
    """Tests for PHI outbound guard."""

    def test_ssn_pattern_detected(self):
        """SSN patterns should be detected."""
        with pytest.raises(SecurityException):
            assert_no_phi("Patient SSN: 123-45-6789")

    def test_mrn_pattern_detected(self):
        """MRN patterns should be detected."""
        with pytest.raises(SecurityException):
            assert_no_phi("MRN-12345678 clinical note")

    def test_phone_pattern_detected(self):
        """Phone number patterns should be detected."""
        with pytest.raises(SecurityException):
            assert_no_phi("Contact: 555-123-4567")

    def test_email_pattern_detected(self):
        """Email patterns should be detected."""
        with pytest.raises(SecurityException):
            assert_no_phi("Email: patient@example.com")

    def test_clean_text_passes(self):
        """Non-PHI text should pass validation."""
        assert_no_phi("Clinical specimen KEY-001 within normal limits")
        assert_no_phi("TASK-2026-001 analysis complete")
