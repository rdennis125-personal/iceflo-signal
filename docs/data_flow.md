# Data Flow

1. A synthetic CSV export is read from the landing zone.
2. Ingestion adds source filename, load timestamp, row number, and source hash.
3. Validation checks required columns, blank required fields, parseable dates, and allowed documentation statuses.
4. Transformations produce normalized sessions, dimensions, facts, and curated clinician documentation status.
5. Delivery renders one HTML file per clinician from the curated dataset.

Raw rows are treated as immutable. Downstream transformations should create new outputs instead of modifying source exports in place.
