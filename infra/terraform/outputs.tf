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
