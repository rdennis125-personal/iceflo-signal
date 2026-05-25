# Data Flow

1. A client/source-system ingest source places CSV exports in that source system's landing zone.
2. For Mindful Oregon, the first external source is a shared Google Drive folder configured in `config/clients/mindful_oregon/ingest_sources.json`.
3. Ingestion adds source filename, load timestamp, row number, and source hash.
4. Validation checks required columns, blank required fields, parseable dates, and allowed documentation statuses.
5. Transformations write client-level EDW outputs under `edw/{environment}` so multiple source systems can contribute to common facts, dimensions, curated datasets, and presentation outputs.
6. Presentation renders one HTML file per clinician from the curated dataset.

Raw rows are treated as immutable. Downstream transformations should create new outputs instead of modifying source exports in place.

Google Drive folder IDs, OAuth client secrets, and token files are environment-specific configuration. They must not be committed.
