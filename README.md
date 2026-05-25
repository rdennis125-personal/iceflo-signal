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

## Client Data Layer

```text
{client_data_root}
  /sources
    /{source_system}
      /{environment}
        /landing
          /incoming
          /archive
          /rejected

  /edw
    /{environment}
      /raw
      /normalized
      /facts
      /dimensions
      /curated
      /presentation

  /utility
    /{environment}
      /config
      /schemas
      /templates
      /reference
```

Each ICEFLO client owns a data root in its own tenant and can choose the backing technology for that root, such as Google Drive now, GCS later, or a future database-backed repository. Source-system landing zones are source-specific. EDW layers are client-level because transformed facts, dimensions, curated datasets, and presentation outputs may combine multiple source systems.

Mindful Oregon's initial test layout is:

```text
mindful_oregon_data_root
  /sources
    /simple_practice
      /test
        /landing
          /incoming
          /archive
          /rejected

  /edw
    /test
      /raw
      /normalized
      /facts
      /dimensions
      /curated
      /presentation
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
- Repository-pattern storage access with dependency injection
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

## SimplePractice Transform Base

The `transform_base` work adds the first privacy-preserving SimplePractice CSV processing layer for the Mindful Oregon client namespace.

## Google Drive Ingest Setup

Client-owned Google Drive folders are configured per client, without committing folder IDs, OAuth tokens, or credential files.

The Mindful Oregon ingest source config lives at:

```text
config/clients/mindful_oregon/ingest_sources.json
config/clients/mindful_oregon/data_layers.json
```

It defines a `mindful_oregon_simple_practice_drive` source that downloads CSV files into:

```text
sources/simple_practice/test/landing/incoming
```

For local user-account OAuth, set:

```bash
export ICEFLO_MINDFUL_OREGON_TEST_ROOT_FOLDER_ID="google-drive-root-folder-id"
export ICEFLO_MINDFUL_OREGON_PROD_ROOT_FOLDER_ID="google-drive-root-folder-id"
export ICEFLO_MINDFUL_OREGON_SIMPLE_PRACTICE_TEST_INCOMING_FOLDER_ID="google-drive-incoming-folder-id"
export ICEFLO_GOOGLE_OAUTH_CLIENT_SECRETS_PATH="/local/secure/path/client_secret.json"
export ICEFLO_MINDFUL_OREGON_GOOGLE_TOKEN_PATH="/local/secure/path/mindful_oregon_token.json"
```

On Windows PowerShell:

```powershell
$env:ICEFLO_MINDFUL_OREGON_TEST_ROOT_FOLDER_ID = "google-drive-root-folder-id"
$env:ICEFLO_MINDFUL_OREGON_PROD_ROOT_FOLDER_ID = "google-drive-root-folder-id"
$env:ICEFLO_MINDFUL_OREGON_SIMPLE_PRACTICE_TEST_INCOMING_FOLDER_ID = "google-drive-incoming-folder-id"
$env:ICEFLO_GOOGLE_OAUTH_CLIENT_SECRETS_PATH = "C:\secure\iceflo-signal\client_secret.json"
$env:ICEFLO_MINDFUL_OREGON_GOOGLE_TOKEN_PATH = "C:\secure\iceflo-signal\mindful_oregon_token.json"
```

The committed `.env.example` file documents the required variable names. Copy it to `.env` for local use or set the variables directly in your shell. The real `.env` file is ignored by git.

Then run:

```bash
python -m iceflo_signal sync-google-drive \
  --config config/clients/mindful_oregon/ingest_sources.json \
  --data-layer-config config/clients/mindful_oregon/data_layers.json \
  --source-id mindful_oregon_simple_practice_drive
```

The first OAuth run opens a browser consent flow and writes a refreshable token to the configured token path. Credential and token JSON files must stay outside git and should later move to Google Secret Manager or another managed secret store.

## Storage Repository Pattern

Pipeline data access should go through repository interfaces under:

```text
src/iceflo_signal/storage/
```

The current repository implementations are:

- `LocalFileRepository`
- `GoogleDriveObjectRepository`

Workflows should inject repositories into ingestion, pipeline, and delivery code instead of hardcoding filesystem, Google Drive, GCS, or database calls into transformation logic. This lets us use Google Drive as the data layer now, replace it with GCS later, and move to a database if scale or scope requires it.

Client-specific SimplePractice processors live under:

```text
src/iceflo_signal/ingestion/clients/mindful_oregon/simple_practice/
```

The observed SimplePractice export definitions and privacy rules live under:

```text
config/clients/mindful_oregon/simple_practice/
  export_definitions.json
  privacy_rules.json
```

Supported initial export processors:

- `ClientPhoneSmsRemindersProcessor`
- `ClientEmailsProcessor`
- `UnpaidInsuranceAppointmentsProcessor`
- `InsuranceClaimsProcessor`
- `InsurancePaymentReportsProcessor`
- `InsuranceStatusChecksProcessor`
- `AppointmentStatusProcessor`
- `ClientDetailsProcessor`
- `ClientAttendanceProcessor`
- `ClientDemographicsProcessor`
- `InsuranceAgingProcessor`

### Client Privacy Rule

Client names are transformed into privacy-safe display values before downstream presentation.

```text
John Jones      -> Jo Jo
Joseph Johnson  -> Jo Jo
```

Display names are not unique and must never be used as join keys. Each client record also receives a stable `client_key` generated from a namespaced SHA-256 hash of the normalized source name. This allows the EDW to preserve uniqueness for client-specific reporting while keeping presentation outputs obfuscated.

### Export-Specific Handling

The appointment status export repeats `Charge`, `Paid`, and `Unpaid` headers. The processor maps those duplicate fields into semantic responsibility groups:

```text
Charge   -> client_responsibility_charge
Paid     -> client_responsibility_paid
Unpaid   -> client_responsibility_unpaid

Charge__2 -> insurance_responsibility_charge
Paid__2   -> insurance_responsibility_paid
Unpaid__2 -> insurance_responsibility_unpaid
```

The client attendance export includes a SimplePractice summary row such as:

```text
230 clients, 9 clinicians, 807 appointments, 1 office, 5 statuses
```

`ClientAttendanceProcessor` excludes that summary row from transformed attendance records.

The insurance aging export is payer-level aggregate data and does not include a client identity column.

### Incomplete Note Notifications

The primary notification use case filters `appointment-status-report.csv` to appointments where:

```text
Progress Note Status <> LOCKED
```

It renders one dry-run clinician notification per clinician. Each notification lists:

- Date of Service
- obfuscated Client display name
- Progress Note Status

Run the notification renderer:

```bash
python -m iceflo_signal render-incomplete-note-notifications \
  --input storage_sample/sources/simple_practice/test/landing/incoming/appointment-status-report.csv \
  --recipient rdennis125@gmail.com \
  --report-period "Weekly SimplePractice export" \
  --output storage_sample/edw/test/presentation/incomplete_note_notifications
```

The command writes browser-previewable HTML files and `.eml` email drafts under the output directory. Client display names are obfuscated before rendering, and the original source client names are not included in the notification output.

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
python -m iceflo_signal run-local --input storage_sample/sources/sample_sessions/test/landing/incoming/sample_sessions.csv --output storage_sample/edw/test
```

Render local demo email previews:

```bash
python -m iceflo_signal render-template-demo --recipient rdennis125@gmail.com --output storage_sample/edw/test/presentation/template_demos
```

The demo command writes browser-previewable HTML and `.eml` draft files for each registered template:

```text
storage_sample/edw/test/presentation/template_demos/
  index.html
  mindful_oregon_alert_review.html
  mindful_oregon_alert_review.eml
  mindful_oregon_base_card.html
  mindful_oregon_base_card.eml
  mindful_oregon_clinician_digest.html
  mindful_oregon_clinician_digest.eml
  mindful_oregon_exec_summary.html
  mindful_oregon_exec_summary.eml
```

Open `storage_sample/edw/test/presentation/template_demos/index.html` in a browser to inspect all demo templates. The `.eml` files are local email drafts addressed to the configured recipient; the project does not send email yet.

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
