"""Regression tests for audit integrity, PHI handling and HTTP integration."""
import os

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from agents.base import AuditTrail, AuditLogger, SecurityException
from agents.models import SystemTaskPayload
from agents.supervisor import SystemSupervisor
from agents.api import app


def test_recomputed_hmac_detects_modified_signed_fields():
    trail = AuditTrail(secret_key="a-valid-independent-test-key")
    trail.log("test", "test", "EVALUATION", {"count": 1})
    assert trail.verify_integrity()
    trail.logs[0]["payload_hash"] = "0" * 64
    assert not trail.verify_integrity()


def test_chain_detects_modified_hash():
    trail = AuditTrail(secret_key="a-valid-independent-test-key")
    trail.log("test", "test", "ONE", {"value": 1})
    trail.log("test", "test", "TWO", {"value": 2})
    trail.logs[0]["current_hash"] = "f" * 64
    assert not trail.verify_integrity()


def test_audit_access_is_snapshot():
    trail = AuditTrail(secret_key="a-valid-independent-test-key")
    trail.log("test", "test", "ONE", {"value": 1})
    trail.get_trail()[0]["event_type"] = "CHANGED"
    assert trail.verify_integrity()


def test_nonfinite_metrics_and_oversize_attributes_rejected():
    base = dict(task_id="T1", target_identifier="KEY-01", primary_metric=1.0)
    with pytest.raises(ValidationError):
        SystemTaskPayload(**(base | {"primary_metric": float("inf")}))
    with pytest.raises(ValidationError):
        SystemTaskPayload(**(base | {"secondary_metric": float("nan")}))
    with pytest.raises(ValidationError):
        SystemTaskPayload(**(base | {"attributes": {"payload": "x" * 17000}}))


def test_nested_attributes_phi_rejected():
    supervisor = SystemSupervisor()
    payload = SystemTaskPayload(task_id="T1", target_identifier="KEY-01", primary_metric=1, attributes={"nested": {"contact": "patient@example.com"}})
    with pytest.raises(SecurityException):
        supervisor.process_task(payload)


def test_api_smoke_and_safe_validation():
    client = TestClient(app)
    assert client.get("/health").status_code == 200
    assert client.get("/").status_code == 200
    clean = client.post("/api/audit", json={"task_id":"T1","target_identifier":"KEY-01","primary_metric":5})
    assert clean.status_code == 200
    assert clean.json()["overall_urgency"] == "ROUTINE"
    assert "system_tasks_total" in client.get("/metrics/prometheus").text
    rejected = client.post("/api/audit", json={"task_id":"T2","target_identifier":"KEY-01","primary_metric":5,"attributes":{"email":"patient@example.com"}})
    assert rejected.status_code == 422
    assert "patient@example.com" not in rejected.text
    assert client.get("/api/audit/logs").json()["verified"] is True
