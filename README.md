# OMOP CDM ETL Vocabulary Agent

> **Domain:** Clinical Decision Support & Biomedical Computing
> **Standards:** OHDSI OMOP Common Data Model v5.4, CAP, CLSI, ISO

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## 📖 What It Does

The OMOP CDM ETL Vocabulary Agent is a multi-agent orchestration system for clinical data quality assessment and ETL pipeline monitoring. It provides:

- **Multi-Agent Evaluation**: Three specialized workers (InvariantQC, SafetyEscalation, ProtocolConformance) evaluate clinical data payloads
- **Consensus Dossier Generation**: Aggregates worker alerts into a unified assessment with HMAC-SHA256 audit trail
- **PHI Outbound Guard**: Prevents protected health information from leaving the system via regex pattern detection
- **Prometheus Metrics**: Exports operational metrics for monitoring and alerting
- **FastAPI REST API**: HTTP endpoints for integration with clinical data pipelines

---

## ⚙️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    SystemSupervisor                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ InvariantQC  │  │   Safety     │  │  Protocol    │      │
│  │   Worker     │  │ Escalation   │  │ Conformance  │      │
│  │              │  │   Worker     │  │   Worker     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│         │                 │                 │               │
│         └─────────────────┼─────────────────┘               │
│                    Consensus Dossier                        │
│                           │                                 │
│              HMAC-SHA256 Audit Trail                        │
└─────────────────────────────────────────────────────────────┘
```

### Key Modules

| Module | Purpose |
|--------|---------|
| `agents/supervisor.py` | Master orchestrator coordinating worker evaluations |
| `agents/workers.py` | Specialized domain workers for QC, safety, and conformance |
| `agents/base.py` | PHI guard, HMAC audit trail, security utilities |
| `agents/models.py` | Pydantic schemas with input validation |
| `agents/metrics.py` | Prometheus metrics exporter |
| `agents/learning.py` | Bayesian calibration for worker reliability |
| `agents/api.py` | FastAPI REST endpoints |
| `omop_cdm_etl/` | Secondary ETL coordination module |

---

## 💻 Installation

```bash
# Clone the repository
git clone https://github.com/abusuraihsakhri/omop-cdm-etl-vocabulary-agent.git
cd omop-cdm-etl-vocabulary-agent

# Install dependencies
pip install fastapi uvicorn pydantic pytest

# Set required environment variable for audit security
export AUDIT_SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
```

---

## 💻 CLI Usage

### 1. Single Task Evaluation
```bash
python cli.py audit --task-id TASK-001 --target KEY-01 --primary 28.5 --secondary 14.2 --critical --status DISCORDANT
```

### 2. Interactive Chat Query
```bash
python cli.py chat "What is the system status?"
```

### 3. Batch CSV Processing
```bash
python cli.py batch -i sample.csv -o results.csv
```

### 4. Verify Audit Trail Integrity
```bash
python cli.py verify-audit
```

### 5. Launch REST API Server
```bash
python cli.py serve --host 127.0.0.1 --port 8000
```

### Parameter Reference

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `--task-id` | string | TASK-2026-001 | Unique task identifier (alphanumeric, hyphens, underscores) |
| `--target` | string | KEY-TARGET-01 | Target entity identifier |
| `--primary` | float | 28.5 | Primary measurement value |
| `--secondary` | float | 14.2 | Secondary measurement value |
| `--critical` | flag | False | Mark as critical priority |
| `--status` | string | DISCORDANT | Status descriptor |

---

## 🛡️ Security Features

### Zero-PHI Outbound Interceptor
Active regex inspection blocks SSNs, MRNs, phone numbers, emails, and patient identifiers from outbound data.

```python
from agents.base import PHIGuard

# Raises SecurityException if PHI detected
PHIGuard.assert_no_phi("Patient MRN-12345")  # Raises!

# Or redact PHI automatically
safe_text = PHIGuard.redact_phi("Contact: patient@email.com")
# Returns: "Contact: [REDACTED_IDENTIFIER]"
```

### HMAC-SHA256 Tamper-Evident Audit Trail
Every evaluation is logged with a chained cryptographic hash. The `AUDIT_SECRET_KEY` environment variable is **required** and must be at least 16 characters.

### Input Validation
All task IDs and identifiers are validated against injection attacks:
- Only alphanumeric characters, hyphens, and underscores allowed
- Maximum 64 characters
- Path traversal and SQL injection patterns rejected

---

## 🧪 Testing

```bash
# Run all tests
pytest -v

# Run with coverage
pytest -v --cov=agents --cov=omop_cdm_etl

# Run specific test modules
pytest tests/test_security_and_validation.py -v
pytest tests/test_metrics_and_learning.py -v
```

### Test Coverage

- **Security & Validation**: Audit key enforcement, input validation, PHI detection
- **Core Functionality**: Worker evaluation, supervisor consensus, CLI commands
- **Metrics & Learning**: Prometheus export, Bayesian calibration
- **Enrichment Suite**: Feature engines, threshold escalation

---

## 🐳 Docker Deployment

```bash
# Build container
docker build -t omop-cdm-etl-vocabulary-agent .

# Run with audit key
docker run -p 8000:8000 -e AUDIT_SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))") omop-cdm-etl-vocabulary-agent
```

---

## 📊 Prometheus Metrics

The `/metrics` endpoint exposes:
- `system_tasks_total` - Total tasks processed
- `alerts_triggered_total` - Alerts by urgency tier
- `phi_outbound_blocks_total` - PHI guard blocks
- `audit_chain_blocks_total` - Audit blocks signed
- `task_processing_duration_avg_seconds` - Average latency

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.
