# Deployment

The current scaffold runs locally. A future cloud deployment can use:

- Google Cloud Storage for landing and transformed storage zones.
- Google Cloud Run for the pipeline container.
- Google Cloud Scheduler for recurring runs.
- Google Secret Manager for credentials and environment-specific configuration.
- Google Cloud Logging for structured processing logs.

The local CLI shape is intended to map cleanly to a container entrypoint.

## Google Drive Access

The initial ingest path supports a user OAuth configuration for a client-shared Google Drive folder. Local runs use environment variables to point at the folder ID, OAuth client secret file, and token file. Cloud deployment should replace local token files with managed secrets and mount or inject the values at runtime.

For clients that can share folders directly with a service account, the same config model supports a future `service_account` auth mode.

## Deployment Setup Branch

The `deployment_setup` scaffold adds:

- `Dockerfile` for packaging the Python CLI as a container.
- `.github/workflows/deploy-cloud-run-job.yml` for GitHub Actions deployment.
- Terraform-managed Artifact Registry, Secret Manager placeholders, Cloud Run runtime service account, and Cloud Run Job.

Outside the codebase, configure:

1. Google Cloud project APIs, either manually or through Terraform with `enable_project_services = true`.
2. Terraform authentication using your Terraform service account.
3. Secret Manager secret versions for the Mindful Oregon Drive folder ID, OAuth client secret JSON, and OAuth token JSON.
4. GitHub repository variables for project/region/repository/job names.
5. GitHub repository secrets for Workload Identity Federation provider and deploy service account.

The first Cloud Run Job can safely use `cloud_run_job_args = ["--help"]` as a bootstrap smoke test. After the cloud storage ingest path is wired end-to-end, update the job args to run the scheduled ingest workflow.
