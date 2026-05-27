# ICEFLO Signal Terraform

This Terraform scaffold creates the initial Google Cloud runtime resources for ICEFLO Signal:

- Optional Google Cloud Storage client data-root bucket and prefix placeholders.
- Artifact Registry Docker repository.
- Cloud Run runtime service account.
- Secret Manager placeholder secrets for Google Drive ingest.
- Cloud Run Jobs for scheduled ICEFLO Signal ingest and workflow execution.

Storage is client-provided and selected by client configuration. This Terraform module configures the GCS implementation of that contract for the first deployment. For development, Terraform can create a dedicated client data-root bucket with `manage_client_data_root_bucket = true`. For a real client-provided GCS bucket, set `manage_client_data_root_bucket = false` and provide the existing bucket name.

The storage layout mirrors the client data root used by `storage_sample/`:

```text
gs://<mindful_oregon_test_data_root>/
  sources/simple_practice/test/landing/incoming/
  sources/simple_practice/test/landing/archive/
  sources/simple_practice/test/landing/rejected/
  sources/simple_practice/prod/landing/incoming/
  sources/simple_practice/prod/landing/archive/
  sources/simple_practice/prod/landing/rejected/
  edw/test/raw/
  edw/test/normalized/
  edw/test/facts/
  edw/test/dimensions/
  edw/test/curated/
  edw/test/presentation/
  edw/prod/raw/
  edw/prod/normalized/
  edw/prod/facts/
  edw/prod/dimensions/
  edw/prod/curated/
  edw/prod/presentation/
  utility/test/config/
  utility/test/schemas/
  utility/test/templates/
  utility/test/reference/
  utility/prod/config/
  utility/prod/schemas/
  utility/prod/templates/
  utility/prod/reference/
```

## Usage

```bash
terraform init
terraform plan -var-file=environments/dev.tfvars
terraform apply -var-file=environments/dev.tfvars
```

Copy `environments/dev.tfvars.example` to `environments/dev.tfvars` and set project-specific values before applying.

## Required Local Environment

Authenticate Terraform with your Terraform service account before running:

```powershell
$env:GOOGLE_APPLICATION_CREDENTIALS = "C:\secure\iceflo-signal\terraform-sa.json"
```

The Terraform service account needs permission to manage the resources above. For a dev project, a practical bootstrap set is:

- `roles/serviceusage.serviceUsageAdmin`
- `roles/storage.admin`
- `roles/artifactregistry.admin`
- `roles/run.admin`
- `roles/iam.serviceAccountAdmin`
- `roles/secretmanager.admin`

## Runtime Secrets

Terraform creates the Secret Manager secret containers, but does not commit or populate secret values. Add versions outside git:

```bash
mkdir -p .local/secrets

cp secret_templates/mindful_oregon_simple_practice_test_incoming_folder_id.txt .local/secrets/mindful_oregon_simple_practice_test_incoming_folder_id.txt
cp secret_templates/google_oauth_client_secrets.json .local/secrets/google_oauth_client_secrets.json
cp secret_templates/mindful_oregon_google_token.json .local/secrets/mindful_oregon_google_token.json

gcloud secrets versions add iceflo-mindful-oregon-simple-practice-test-incoming-folder-id --data-file=.local/secrets/mindful_oregon_simple_practice_test_incoming_folder_id.txt
gcloud secrets versions add iceflo-google-oauth-client-secrets --data-file=.local/secrets/google_oauth_client_secrets.json
gcloud secrets versions add iceflo-mindful-oregon-google-token --data-file=.local/secrets/mindful_oregon_google_token.json
```

The committed files under `secret_templates/` are bootstrap placeholders only. Copy them to `.local/secrets/`, replace placeholder values with real values when available, and keep `.local/` out of git. The Cloud Run Jobs read the customer source landing folder ID as an environment variable and mount the OAuth JSON values as files.

## Cloud Run Jobs

Set `cloud_run_jobs` to deploy one operational job per client/environment/use case. The dev example creates:

```text
iceflo-mindful-oregon-test-simple-practice-ingest
iceflo-mindful-oregon-test-incomplete-note-notifications
```

Run them manually with:

```bash
gcloud run jobs execute iceflo-mindful-oregon-test-simple-practice-ingest --region <region> --wait
gcloud run jobs execute iceflo-mindful-oregon-test-incomplete-note-notifications --region <region> --wait
```

## GitHub Actions

The deployment workflow expects these GitHub repository variables:

- `GCP_PROJECT_ID`
- `GCP_REGION`
- `ARTIFACT_REGISTRY_REPOSITORY`
- `CLOUD_RUN_JOBS` as a comma-separated list of Cloud Run Job names

And these GitHub repository secrets:

- `GCP_WORKLOAD_IDENTITY_PROVIDER`
- `GCP_DEPLOY_SERVICE_ACCOUNT`

Use Workload Identity Federation for GitHub Actions instead of storing a Google service account key in GitHub.
