# Mindful Oregon Internal Onboarding Playbook

This playbook is for ICEFLO Signal operators onboarding Mindful Oregon. It covers what ICEFLO configures, deploys, and validates. Customer-facing requests belong in `mindful_oregon_customer_onboarding.md`.

## Operating Model

- ICEFLO hosts the runtime core in the ICEFLO Google Cloud project.
- Mindful Oregon owns the operational data layer and source landing folders.
- The application accesses data through repository implementations selected by client config.
- Secrets are stored in ICEFLO-controlled Google Secret Manager for this deployment.
- No real PHI, production exports, OAuth tokens, or client secrets are committed to git.

## Current Mindful Oregon Test Shape

```text
Source landing: customer-provided Google Drive folder
Client data root: GCS bucket configured as mindful_oregon_test_data_root
Runtime: ICEFLO Cloud Run Jobs
Delivery: Gmail API using configured sender and recipient
```

Logical data-root layout:

```text
{mindful_oregon_data_root}
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
  /utility
    /test
      /config
      /schemas
      /templates
      /reference
```

## ICEFLO Setup Checklist

1. Confirm the client key and environment.

```text
client_key: mindful_oregon
environment: test
source_system: simple_practice
workflow: incomplete_note_notifications
```

2. Configure the client package.

Files:

```text
config/clients/mindful_oregon/client.json
config/clients/mindful_oregon/data_layers.json
config/clients/mindful_oregon/ingest_sources.json
config/clients/mindful_oregon/workflows.json
config/clients/mindful_oregon/simple_practice/export_definitions.json
config/clients/mindful_oregon/simple_practice/privacy_rules.json
```

Verify:

- `data_layers.json` points `mindful_oregon_test_data_root` at the selected repository type.
- `ingest_sources.json` points SimplePractice ingest at the customer-provided Drive folder secret.
- `workflows.json` has a configured sender and recipient for test delivery.
- Template content stays under client-maintainable template files, not Python code.

3. Configure Terraform variables.

Use `infra/terraform/environments/dev.tfvars` locally in the deployment workspace. Do not commit it.

Minimum Mindful Oregon values:

```hcl
mindful_oregon_test_data_root = "client-provided-or-dev-test-root"
mindful_oregon_prod_data_root = "client-provided-or-dev-prod-root"
manage_client_data_root_bucket = true
```

For real client-owned GCS, set `manage_client_data_root_bucket = false` and use the existing client bucket name. For Drive-backed or future database-backed roots, the client config and repository factory should define the backend contract instead of assuming a bucket.

4. Confirm required Google Cloud APIs.

Required for the current test:

- Artifact Registry API
- Cloud Build API
- Cloud Run Admin API
- Cloud Scheduler API
- Gmail API
- Google Drive API
- IAM API
- Secret Manager API
- Cloud Storage API when using GCS data roots

5. Create or update Secret Manager secret versions.

Current secrets:

```text
iceflo-google-oauth-client-secrets
iceflo-mindful-oregon-google-token
iceflo-mindful-oregon-simple-practice-test-incoming-folder-id
```

The OAuth token must include:

```text
https://www.googleapis.com/auth/drive
https://www.googleapis.com/auth/gmail.send
```

6. Deploy infrastructure.

From the Codespace or deployment shell:

```bash
cd /workspaces/iceflo-signal/infra/terraform
terraform init
terraform plan -var-file=environments/dev.tfvars
terraform apply -var-file=environments/dev.tfvars
```

7. Build and deploy the application image.

Use the branch image tag or the approved release tag. Update both Cloud Run Jobs to that image.

```bash
IMAGE="us-west1-docker.pkg.dev/iceflo-signal/iceflo-signal/iceflo-signal:send-incomplete-note-emails"

gcloud auth configure-docker us-west1-docker.pkg.dev --quiet
docker build --tag "$IMAGE" .
docker push "$IMAGE"

gcloud run jobs update iceflo-mindful-oregon-test-simple-practice-ingest \
  --image "$IMAGE" \
  --region us-west1

gcloud run jobs update iceflo-mindful-oregon-test-incomplete-note-notifications \
  --image "$IMAGE" \
  --region us-west1
```

8. Run the test flow.

```bash
gcloud run jobs execute iceflo-mindful-oregon-test-simple-practice-ingest \
  --region us-west1 \
  --wait

gcloud run jobs execute iceflo-mindful-oregon-test-incomplete-note-notifications \
  --region us-west1 \
  --wait
```

9. Validate results.

Confirm:

- The ingest job downloaded expected CSV files from the SimplePractice landing folder.
- The client data root contains the copied landing file under `sources/simple_practice/test/landing/incoming`.
- The workflow writes HTML and `.eml` outputs under `edw/test/presentation/incomplete_note_notifications`.
- Client names in presentation output are obfuscated.
- Test emails are received by the configured recipient.
- Cloud Logging has a successful execution record for both jobs.

## Go-Live Readiness

Before production:

- Replace test sender and recipient values with approved production values.
- Add provider-level recipient mappings when the customer provides them.
- Add a send audit log for message IDs, recipients, workflow run IDs, and timestamps.
- Add idempotency protection to prevent accidental duplicate sends for the same export.
- Decide whether the OAuth app remains in test mode for limited operators or enters Google production verification.
- Configure Cloud Scheduler only after the manual run path is stable.
