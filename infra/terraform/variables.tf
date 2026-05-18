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
