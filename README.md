# ICEFLO Signal

ICEFLO Signal is a plug-and-play operational reporting and notification platform for healthcare and service-based organizations.

The platform ingests manually exported CSV files, validates and transforms them through governed reporting layers, and produces curated datasets for operational notifications, dashboards, and future analytics.

## Initial Use Case

Clinician documentation follow-up.

The system identifies prior-week sessions with incomplete documentation and prepares clinician-specific reporting datasets that can support branded HTML email notifications and future dashboards.

## Architecture

```text
Manual CSV Export
  -> Landing Zone
  -> Raw Layer
  -> Normalized Layer
  -> Denormalized Facts & Dimensions
  -> Curated Use-Case Datasets
  -> Delivery Layer
```

## Storage Zones

```text
/storage
  /landing
    /incoming
    /archive
    /rejected

  /transformed
    /raw
    /normalized
    /facts
    /dimensions
    /curated

  /utility
    /config
    /schemas
    /templates
    /reference
```

## Technology Stack

- Python
- pandas
- pydantic
- jinja2
- pytest
- Google Cloud Storage
- Google Cloud Run
- Google Cloud Scheduler
- Google Cloud Logging
- Google Secret Manager

## Design Principles

- CSV-first for portability
- Python-first for transferability
- Configuration-driven processing
- No hardcoded clinician/report rules
- Immutable raw file retention
- Repeatable transformations
- HIPAA-conscious handling
- Minimal PHI exposure
- Audit-friendly processing logs
- Cloud-portable architecture

## Transformation Layers

### Raw

Stores source-shaped records from the manual CSV export with ingestion metadata.

### Normalized

Standardizes dates, identifiers, statuses, names, codes, and null handling.

### Facts and Dimensions

Reusable reporting structures such as:

- `DIM_CLINICIAN`
- `DIM_DATE`
- `DIM_LOCATION`
- `DIM_PROGRAM`
- `FACT_SESSION`
- `FACT_DOCUMENTATION_STATUS`
- `FACT_BILLING_READINESS`

### Curated

Use-case-ready 2D datasets such as:

- `CURATED_CLINICIAN_DOCUMENTATION_STATUS`
- `CURATED_CORPORATE_BILLING_READINESS`
- `CURATED_DOCUMENTATION_AGING`

## Local Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
pytest
```

Run the sample pipeline:

```bash
python -m iceflo_signal run-local --input storage_sample/landing/incoming/sample_sessions.csv --output storage_sample/transformed
```

## Security Notes

Do not commit:

- real PHI
- real clinician data
- credentials
- production exports
- client-specific secrets

Use synthetic sample data only.

## Status

Initial scaffold in progress.
