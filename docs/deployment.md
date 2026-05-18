# Deployment

The current scaffold runs locally. A future cloud deployment can use:

- Google Cloud Storage for landing and transformed storage zones.
- Google Cloud Run for the pipeline container.
- Google Cloud Scheduler for recurring runs.
- Google Secret Manager for credentials and environment-specific configuration.
- Google Cloud Logging for structured processing logs.

The local CLI shape is intended to map cleanly to a container entrypoint.
