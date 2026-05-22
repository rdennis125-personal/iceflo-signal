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
