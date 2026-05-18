# Codex Guidance

This repository handles healthcare-adjacent operational reporting. Keep all sample data synthetic.

## Working Rules

- Do not commit PHI, credentials, production exports, or real clinician data.
- Keep business rules configuration-driven where practical.
- Keep metric calculations in Python transformations, not HTML templates.
- Treat raw input files as immutable.
- Preserve ingestion metadata through transformation layers.
- Prefer small, testable modules with clear boundaries.

## Validation

Before handing off changes, run:

```bash
pip install -e .
pytest
python -m iceflo_signal run-local --input storage_sample/landing/incoming/sample_sessions.csv --output storage_sample/transformed
```
