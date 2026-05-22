variable "project_id" {
  description = "Google Cloud project ID where ICEFLO Signal storage will be created."
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

variable "root_bucket_name" {
  description = "Globally unique root GCS bucket name for ICEFLO Signal storage."
  type        = string
}

variable "storage_class" {
  description = "Storage class for the root GCS bucket."
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
  description = "Allow Terraform to delete the bucket even when objects exist. Keep false for shared or production environments."
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
  description = "Cloud Run Job name for scheduled ICEFLO Signal work."
  type        = string
  default     = "iceflo-signal-job"
}

variable "cloud_run_image" {
  description = "Container image URI to deploy to the Cloud Run Job."
  type        = string
}

variable "cloud_run_job_args" {
  description = "Default CLI args for the Cloud Run Job container."
  type        = list(string)
  default     = ["--help"]
}

variable "cloud_run_job_timeout" {
  description = "Cloud Run Job task timeout."
  type        = string
  default     = "3600s"
}
