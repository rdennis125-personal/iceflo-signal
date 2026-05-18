# Architecture

ICEFLO Signal uses a layered reporting architecture that starts with manual CSV exports and ends with curated datasets for delivery channels.

The initial implementation uses local paths to keep development portable. Storage access is isolated enough that Google Cloud Storage can later replace local filesystem paths without changing validation, transformation, or rendering logic.

## Layers

- Landing: manually exported CSV files arrive in `storage_sample/landing/incoming`.
- Raw: source-shaped records plus ingestion metadata.
- Normalized: standardized dates, identifiers, statuses, and null handling.
- Facts and dimensions: reusable reporting tables.
- Curated: use-case-specific datasets ready for dashboards or notifications.
- Delivery: dry-run HTML files rendered locally.
