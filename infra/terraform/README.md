# ICEFLO Signal Terraform

This Terraform scaffold creates the initial Google Cloud resources for ICEFLO Signal:

- Google Cloud Storage bucket and prefix placeholders.
- Artifact Registry Docker repository.
- Cloud Run runtime service account.
- Secret Manager placeholder secrets for Google Drive ingest.
- Cloud Run Job shell for scheduled ICEFLO Signal execution.

The storage layout mirrors `storage_sample/`:

```text
gs://<root_bucket_name>/
  landing/clients/mindful_oregon/simple_practice/incoming/
  landing/clients/mindful_oregon/simple_practice/archive/
  landing/clients/mindful_oregon/simple_practice/rejected/
  transformed/clients/mindful_oregon/simple_practice/raw/
  transformed/clients/mindful_oregon/simple_practice/normalized/
  transformed/clients/mindful_oregon/simple_practice/facts/
  transformed/clients/mindful_oregon/simple_practice/dimensions/
  transformed/clients/mindful_oregon/simple_practice/curated/
  utility/clients/mindful_oregon/simple_practice/config/
  utility/clients/mindful_oregon/simple_practice/schemas/
  utility/clients/mindful_oregon/simple_practice/templates/
  utility/clients/mindful_oregon/simple_practice/reference/
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
gcloud secrets versions add iceflo-mindful-oregon-drive-folder-id --data-file=drive-folder-id.txt
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
