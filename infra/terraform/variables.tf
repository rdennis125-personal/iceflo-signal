variable "project_id" {
  description = "Google Cloud project ID where ICEFLO Signal runtime resources are deployed."
  type        = string
}

variable "region" {
  description = "Default Google Cloud region for regional resources."
  type        = string
  default     = "us-central1"
}

variable "storage_location" {
  description = "Google Cloud Storage bucket location."
  type        = string
  default     = "US"
}

variable "mindful_oregon_test_data_root" {
  description = "Client-provided Mindful Oregon test data root for the configured repository implementation. For GCS, use a bucket name or gs:// URI."
  type        = string
}

variable "mindful_oregon_prod_data_root" {
  description = "Client-provided Mindful Oregon production data root for the configured repository implementation. For GCS, use a bucket name or gs:// URI."
  type        = string
  default     = ""
}

variable "storage_class" {
  description = "Storage class for a Terraform-created client data root bucket."
  type        = string
  default     = "STANDARD"
}

variable "labels" {
  description = "Labels to apply to managed resources."
  type        = map(string)
  default = {
    app        = "iceflo-signal"
    managed_by = "terraform"
  }
}

variable "force_destroy" {
  description = "Allow Terraform to delete a managed bucket even when objects exist. Keep false for client data roots."
  type        = bool
  default     = false
}

variable "enable_project_services" {
  description = "Enable Google Cloud APIs required by ICEFLO Signal. Set false if APIs are managed outside this Terraform."
  type        = bool
  default     = true
}

variable "artifact_registry_repository_id" {
  description = "Artifact Registry Docker repository ID for ICEFLO Signal images."
  type        = string
  default     = "iceflo-signal"
}

variable "cloud_run_runtime_service_account_id" {
  description = "Service account ID used by the Cloud Run job at runtime."
  type        = string
  default     = "iceflo-signal-runtime"
}

variable "cloud_run_job_name" {
  description = "Legacy Cloud Run Job name used when cloud_run_jobs is empty."
  type        = string
  default     = "iceflo-signal-job"
}

variable "manage_client_data_root_bucket" {
  description = "Create the GCS client data root bucket with Terraform for this deployment. Set false when the client provides an existing bucket or a non-GCS data layer."
  type        = bool
  default     = true
}

variable "cloud_run_image" {
  description = "Container image URI to deploy to the Cloud Run Job."
  type        = string
}

variable "cloud_run_job_args" {
  description = "Legacy CLI args used when cloud_run_jobs is empty."
  type        = list(string)
  default     = ["--help"]
}

variable "cloud_run_job_timeout" {
  description = "Cloud Run Job task timeout."
  type        = string
  default     = "3600s"
}

variable "cloud_run_jobs" {
  description = "Named Cloud Run Jobs to deploy from the shared ICEFLO Signal image."
  type = map(object({
    name = string
    args = list(string)
  }))
  default = {}
}
