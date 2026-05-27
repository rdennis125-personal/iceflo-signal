output "mindful_oregon_test_data_root" {
  description = "Mindful Oregon test data root reference."
  value       = var.mindful_oregon_test_data_root
}

output "mindful_oregon_prod_data_root" {
  description = "Mindful Oregon production data root reference."
  value       = local.mindful_oregon_prod_data_root
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
  description = "Cloud Run Job names."
  value       = { for key, job in google_cloud_run_v2_job.iceflo_signal : key => job.name }
}

output "cloud_run_runtime_service_account_email" {
  description = "Runtime service account email for the Cloud Run Job."
  value       = google_service_account.cloud_run_runtime.email
}

output "secret_ids" {
  description = "Secret Manager secret IDs created for runtime configuration."
  value       = sort(tolist(local.secret_ids))
}
