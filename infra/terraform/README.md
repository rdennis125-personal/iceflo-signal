# ICEFLO Signal Terraform

This Terraform scaffold creates the initial Google Cloud resources for ICEFLO Signal:

- Google Cloud Storage bucket and prefix placeholders.
- Artifact Registry Docker repository.
- Cloud Run runtime service account.
- Secret Manager placeholder secrets for Google Drive ingest.
- Cloud Run Job shell for scheduled ICEFLO Signal execution.

The storage layout mirrors the client-owned EDW structure used by `storage_sample/`:

```text
gs://<root_bucket_name>/
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
gcloud secrets versions add iceflo-mindful-oregon-test-root-folder-id --data-file=drive-folder-id.txt
gcloud secrets versions add iceflo-mindful-oregon-prod-root-folder-id --data-file=drive-folder-id.txt
gcloud secrets versions add iceflo-mindful-oregon-simple-practice-test-incoming-folder-id --data-file=drive-folder-id.txt
gcloud secrets versions add iceflo-google-oauth-client-secrets --data-file=client_secret.json
gcloud secrets versions add iceflo-mindful-oregon-google-token --data-file=mindful_oregon_token.json
```

The Cloud Run Job reads the folder ID as an environment variable and mounts the OAuth JSON values as files.

## GitHub Actions

The deployment workflow expects these GitHub repository variables:

- `GCP_PROJECT_ID`
- `GCP_REGION`
- `ARTIFACT_REGISTRY_REPOSITORY`
- `CLOUD_RUN_JOB`

And these GitHub repository secrets:

- `GCP_WORKLOAD_IDENTITY_PROVIDER`
- `GCP_DEPLOY_SERVICE_ACCOUNT`

Use Workload Identity Federation for GitHub Actions instead of storing a Google service account key in GitHub.
