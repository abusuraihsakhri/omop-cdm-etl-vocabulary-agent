"""
Pydantic v2 schemas and data definitions for Omop Cdm Etl Vocabulary Agent.
Domain: Clinical & Biomedical AI
Standard: CAP / CLSI / ISO Standards
"""
import datetime
import re
from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, field_validator

# Security: Allowed pattern for identifiers to prevent injection attacks
_IDENTIFIER_PATTERN = re.compile(r'^[A-Za-z0-9_\-]{1,64}$')


def _validate_identifier(value: str, field_name: str) -> str:
    """Validate that an identifier is safe and well-formed."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    if not _IDENTIFIER_PATTERN.match(value):
        raise ValueError(
            f"{field_name} contains invalid characters. "
            "Only alphanumeric, hyphens, and underscores allowed (max 64 chars)."
        )
    return value


class UrgencyLevel(str, Enum):
    ROUTINE = "ROUTINE"
    ELEVATED = "ELEVATED_RISK"
    CRITICAL_STAT = "CRITICAL_STAT_PANIC"


class SystemIntegrityStatus(str, Enum):
    VALIDATED = "VALIDATED_OPTIMAL"
    DISCORDANT = "DISCORDANT_ANOMALY"
    RECALIBRATION_REQUIRED = "RECALIBRATION_REQUIRED"


class SystemTaskPayload(BaseModel):
    task_id: str = Field(..., description="Unique task / case identifier")
    target_identifier: str = Field(..., description="Entity, patient key, or genomic/cryptographic target")
    primary_metric: float = Field(..., description="Primary domain measurement or score")
    secondary_metric: float = Field(default=0.0, description="Secondary kinetic or confidence score")
    status_descriptor: str = Field(default="NOMINAL", description="Status code or phenotype descriptor")
    is_critical_flag: bool = Field(default=False, description="Emergency escalation or high priority trigger")
    attributes: Dict[str, Any] = Field(default_factory=dict, description="Metadata key-value pairs")
    timestamp: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())

    @field_validator('task_id')
    @classmethod
    def validate_task_id(cls, v):
        return _validate_identifier(v, 'task_id')

    @field_validator('target_identifier')
    @classmethod
    def validate_target_identifier(cls, v):
        return _validate_identifier(v, 'target_identifier')

    @field_validator('status_descriptor')
    @classmethod
    def validate_status_descriptor(cls, v):
        if not isinstance(v, str) or not v.strip():
            raise ValueError("status_descriptor must be a non-empty string")
        if len(v) > 128:
            raise ValueError("status_descriptor must be 128 characters or less")
        return v.upper()


class AgentAlert(BaseModel):
    alert_id: str
    origin_worker: str
    urgency: UrgencyLevel
    summary: str
    technical_details: str
    actionable_remediation: str
    standard_reference: str = "CAP / CLSI / ISO Standards"
    timestamp: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()


class ConsensusDossier(BaseModel):
    dossier_id: str
    system_slug: str = "omop-cdm-etl-vocabulary-agent"
    domain: str = "Clinical & Biomedical AI"
    task_id: str
    target_identifier: str
    overall_urgency: UrgencyLevel
    integrity_status: SystemIntegrityStatus
    total_alerts: int
    critical_alerts_count: int
    alerts: List[AgentAlert]
    standard_reference: str = "CAP / CLSI / ISO Standards"
    consensus_summary: str
    audit_hash: str
    timestamp: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()
