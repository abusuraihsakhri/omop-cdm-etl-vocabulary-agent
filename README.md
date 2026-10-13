# OMOP CDM ETL Vocabulary Agent

An experimental Python payload-quality checker with two existing interfaces: the Pydantic/FastAPI worker system in `agents/` and a separate lightweight coordinator in `omop_cdm_etl/`.

**Important limitation:** Despite the repository name, the code does **not** perform OMOP CDM ETL, import OHDSI Athena vocabularies, map source codes to standard concept IDs, or validate CDM schemas. The numerical rules (primary >25; secondary >12 in `agents/`, >10 in `omop_cdm_etl/`) are demonstrations, not validated clinical thresholds.

## Browser demo

Open [`web/index.html`](web/index.html) in a current desktop/mobile browser, or open `index.html` to redirect there. No server, Python runtime, network access or dependencies are required. The browser demo evaluates synthetic identifiers, finite metrics, status keywords and a critical flag, then exports an **unsigned JSON report**. All evaluation happens locally in memory; nothing is sent to a server. There is **no Athena vocabulary lookup, ETL transformation or cryptographic audit** in the browser.

A GitHub Pages workflow is included. A public URL will be added only after a live deployment is verified. **Never enter PHI or identifying patient data.**

## Installation

Python 3.10–3.12 is tested by the repository's CI workflow; Python 3.9+ is declared by the package.

```sh
python -m pip install -e ".[test]"
export AUDIT_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"
python -m pytest -q
```

Use a fresh high-entropy key for each deployment. Never store it in source code, version control or browser JavaScript.

## Primary CLI

```sh
python cli.py audit --task-id TASK-001 --target KEY-001 --primary 28.5 --secondary 14.2 --status DISCORDANT
python cli.py chat "What is the status?"
python cli.py batch -i sample.csv -o results.csv
python cli.py verify-audit
python cli.py serve --host 127.0.0.1 --port 8000
```

The installed console script `omop-cdm-etl-vocabulary-engine` runs the **other** interface, `omop_cdm_etl.cli`. Its outputs and thresholds differ from the root `cli.py`. Both are preserved for backward compatibility.

## REST API

The primary FastAPI server provides `GET /health`, `GET /metrics` (JSON), `GET /metrics/prometheus` (text), `POST /api/audit`, `POST /api/chat`, `GET /api/audit/logs`, and `GET /docs`.

The root `/` serves the local browser demo when repository web files exist. Signatures in the server's audit log use HMAC-SHA256 and are revalidated on inspection, but **audit data is in memory only** and is lost on restart. The heuristic PHI-pattern guard is incomplete and is not a replacement for compliant clinical de-identification. The mock chat backend does not perform genuine language-model inference.

**The API has no authentication. Do not expose it publicly, or supply real patient identifiers or PHI.**

## Docker

```sh
export AUDIT_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"
docker compose up --build
```

Compose requires the environment-supplied secret and binds the service to `127.0.0.1:8000`. The Docker health check requests `/health`.

## Development and testing

```sh
python -m pytest -q
python -m compileall -q agents omop_cdm_etl
```

The CI workflow tests Python 3.10, 3.11 and 3.12, and signs a test audit entry with a freshly generated key. Tests cover workers, CLI, nested-input rejection, audit integrity, metrics, API, enrichment and static browser parsing. Current browser versions of Chrome, Firefox, Edge and Safari support the standard HTML/JavaScript demo.

This repository distributes no OMOP vocabulary dataset. Main modules: `agents/`, `omop_cdm_etl/`, `enrichment.py` and `web/index.html`.

## License

MIT. See [LICENSE](LICENSE).
