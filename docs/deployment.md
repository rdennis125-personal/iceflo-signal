# Deployment

The current deployment shape uses:

- Google Drive for customer-managed source landing folders.
- A client-provided data root behind the repository factory. The first deployment uses GCS, but the application boundary also supports Google Drive and can later support Cloud SQL or another database.
- Google Cloud Run for the pipeline container.
- Google Cloud Scheduler for recurring runs.
- Google Secret Manager for credentials and environment-specific configuration.
- Google Cloud Logging for structured processing logs.

The local CLI shape is intended to map cleanly to a container entrypoint.

## Google Drive Access

The initial ingest path supports a user OAuth configuration for a client-owned Google Drive source landing folder. Local runs use environment variables to point at the landing folder ID, OAuth client secret file, and token file. Cloud deployment replaces local token files with Secret Manager values mounted into Cloud Run at runtime.

For clients that can share folders directly with a service account, the same config model supports a future `service_account` auth mode.

## Cloud Run Jobs

The first deployment uses two Cloud Run Jobs from the same image:

- `iceflo-mindful-oregon-test-simple-practice-ingest`
- `iceflo-mindful-oregon-test-incomplete-note-notifications`

The ingest job reads CSV files from the configured Google Drive landing folder and writes them into the configured client data root under:

```text
sources/simple_practice/test/landing/incoming/
```

The workflow job reads the landing copy from the configured client data root, processes incomplete-note notifications, and writes HTML and `.eml` previews back into that same client data root under:

```text
edw/test/presentation/incomplete_note_notifications/
```

## Deployment Setup Branch

The `deployment_setup` scaffold adds:

- `Dockerfile` for packaging the Python CLI as a container.
- `.github/workflows/deploy-cloud-run-job.yml` for GitHub Actions deployment.
- Terraform-managed Artifact Registry, Secret Manager placeholders, Cloud Run runtime service account, Cloud Run Jobs, and client data-root access.

Outside the codebase, configure:

1. Google Cloud project APIs, either manually or through Terraform with `enable_project_services = true`.
2. Terraform authentication using your Terraform service account.
3. Secret Manager secret versions for the Mindful Oregon source landing folder ID, OAuth client secret JSON, and OAuth token JSON.
4. GitHub repository variables for project/region/repository/job names.
5. GitHub repository secrets for Workload Identity Federation provider and deploy service account.

For a bootstrap smoke test, leave `cloud_run_jobs` empty and use the legacy `cloud_run_job_args = ["--help"]`. For the full Mindful Oregon test, set `cloud_run_jobs` as shown in `infra/terraform/environments/dev.tfvars.example`.

For GitHub Actions image deployment, set `CLOUD_RUN_JOBS` to a comma-separated list:

```text
iceflo-mindful-oregon-test-simple-practice-ingest,iceflo-mindful-oregon-test-incomplete-note-notifications
```

Run Terraform before the image deployment workflow so the jobs exist; the workflow updates the image on existing jobs and leaves Terraform-managed args, env vars, secrets, and service account settings intact.
