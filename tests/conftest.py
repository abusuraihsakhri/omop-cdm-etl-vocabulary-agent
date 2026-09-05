"""
Pytest configuration and shared fixtures for omop-cdm-etl-vocabulary-agent tests.
"""
import os
import sys
from pathlib import Path

import pytest

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set a deterministic test audit key before any agent modules are imported
os.environ.setdefault("AUDIT_SECRET_KEY", "test-audit-key-for-unit-tests-only-do-not-use-in-production")


def pytest_configure(config):
    """Configure pytest environment."""
    # Ensure test audit key is set
    os.environ["AUDIT_SECRET_KEY"] = "test-audit-key-for-unit-tests-only-do-not-use-in-production"


@pytest.fixture(autouse=True)
def reset_audit_trail():
    """Reset the global audit trail before each test for isolation."""
    from agents.base import AuditLogger
    AuditLogger.reset()
    yield
    AuditLogger.reset()
