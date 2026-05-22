output "root_bucket_name" {
  description = "Root GCS bucket name."
  value       = google_storage_bucket.root.name
}

output "root_bucket_url" {
  description = "Root GCS bucket URL."
  value       = google_storage_bucket.root.url
}

output "storage_prefixes" {
  description = "ICEFLO Signal storage prefixes created as placeholders."
  value       = sort(tolist(local.storage_prefixes))
}

output "artifact_registry_repository" {
  description = "Artifact Registry Docker repository name."
  value       = google_artifact_registry_repository.containers.name
}

output "cloud_run_job_name" {
  description = "Cloud Run Job name."
  value       = google_cloud_run_v2_job.iceflo_signal.name
}

output "cloud_run_runtime_service_account_email" {
  description = "Runtime service account email for the Cloud Run Job."
  value       = google_service_account.cloud_run_runtime.email
}

output "secret_ids" {
  description = "Secret Manager secret IDs created for runtime configuration."
  value       = sort(tolist(local.secret_ids))
}
