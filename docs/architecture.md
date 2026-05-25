# Architecture

ICEFLO Signal uses a layered reporting architecture that starts with manual CSV exports and ends with curated datasets for delivery channels.

The initial implementation uses local paths to keep development portable, but data access should go through repository interfaces instead of direct filesystem calls whenever a workflow reads or writes pipeline data.

## Repository Pattern

Pipeline storage is abstracted behind `ObjectRepository`:

```text
src/iceflo_signal/storage/repositories.py
```

Current implementations:

- `LocalFileRepository` for local development and sample runs.
- `GoogleDriveObjectRepository` for Drive-backed object storage.

This keeps ingestion, validation, transformation, and delivery logic independent from the storage backend. A workflow can compose repositories like:

```text
Google Drive repository -> pipeline transformations -> Google Drive repository
Google Drive repository -> pipeline transformations -> GCS repository
GCS repository          -> pipeline transformations -> database repository
```

Repository implementations own storage mechanics such as object keys, folders, credentials, uploads, downloads, and backend-specific APIs. Transformation code should receive already-loaded records/dataframes and should not know whether data came from local files, Google Drive, GCS, or a future database.

## Client Data Roots

ICEFLO does not assume one shared storage root for every client. Each client has one or more client-owned data roots, configured under `config/clients/{client_key}/data_layers.json`.

Source-system landing is source-specific:

```text
{client_data_root}/sources/{source_system}/{environment}/landing/incoming
{client_data_root}/sources/{source_system}/{environment}/landing/archive
{client_data_root}/sources/{source_system}/{environment}/landing/rejected
```

EDW outputs are client-level because facts, dimensions, curated datasets, and presentation artifacts may combine multiple source systems:

```text
{client_data_root}/edw/{environment}/raw
{client_data_root}/edw/{environment}/normalized
{client_data_root}/edw/{environment}/facts
{client_data_root}/edw/{environment}/dimensions
{client_data_root}/edw/{environment}/curated
{client_data_root}/edw/{environment}/presentation
```

## Layers

- Landing: manually exported CSV files arrive in a source-system namespace such as `sources/simple_practice/test/landing/incoming`, inside the configured client data root.
- Raw: source-shaped records plus ingestion metadata.
- Normalized: standardized dates, identifiers, statuses, and null handling.
- Facts and dimensions: reusable reporting tables.
- Curated: use-case-specific datasets ready for dashboards or notifications.
- Presentation: dry-run HTML files, email drafts, and dashboard-ready extracts.
