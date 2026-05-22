locals {
  project_services = toset([
    "artifactregistry.googleapis.com",
    "cloudbuild.googleapis.com",
    "cloudscheduler.googleapis.com",
    "iam.googleapis.com",
    "run.googleapis.com",
    "secretmanager.googleapis.com",
    "storage.googleapis.com",
  ])

  storage_prefixes = toset([
    "landing/clients/mindful_oregon/simple_practice/incoming/",
    "landing/clients/mindful_oregon/simple_practice/archive/",
    "landing/clients/mindful_oregon/simple_practice/rejected/",
    "transformed/clients/mindful_oregon/simple_practice/raw/",
    "transformed/clients/mindful_oregon/simple_practice/normalized/",
    "transformed/clients/mindful_oregon/simple_practice/facts/",
    "transformed/clients/mindful_oregon/simple_practice/dimensions/",
    "transformed/clients/mindful_oregon/simple_practice/curated/",
    "utility/clients/mindful_oregon/simple_practice/config/",
    "utility/clients/mindful_oregon/simple_practice/schemas/",
    "utility/clients/mindful_oregon/simple_practice/templates/",
    "utility/clients/mindful_oregon/simple_practice/reference/",
  ])

  secret_ids = toset([
    "iceflo-mindful-oregon-drive-folder-id",
    "iceflo-google-oauth-client-secrets",
    "iceflo-mindful-oregon-google-token",
  ])
}

resource "google_project_service" "required" {
  for_each = var.enable_project_services ? local.project_services : toset([])

  project            = var.project_id
  service            = each.value
  disable_on_destroy = false
}

resource "google_storage_bucket" "root" {
  name                        = var.root_bucket_name
  location                    = var.storage_location
  storage_class               = var.storage_class
  labels                      = var.labels
  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"
  force_destroy               = var.force_destroy

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      age            = 30
      matches_prefix = ["landing/clients/mindful_oregon/simple_practice/archive/"]
    }

    action {
      type = "SetStorageClass"
      storage_class = "NEARLINE"
    }
  }
}

resource "google_storage_bucket_object" "prefix_placeholders" {
  for_each = local.storage_prefixes

  bucket       = google_storage_bucket.root.name
  name         = "${each.value}.keep"
  content      = ""
  content_type = "text/plain"
}

resource "google_artifact_registry_repository" "containers" {
  repository_id = var.artifact_registry_repository_id
  location      = var.region
  format        = "DOCKER"
  description   = "Container images for ICEFLO Signal"
  labels        = var.labels

  depends_on = [google_project_service.required]
}

resource "google_service_account" "cloud_run_runtime" {
  account_id   = var.cloud_run_runtime_service_account_id
  display_name = "ICEFLO Signal Cloud Run runtime"
  description  = "Runs ICEFLO Signal scheduled ingestion and notification jobs."
}

resource "google_storage_bucket_iam_member" "runtime_storage_object_admin" {
  bucket = google_storage_bucket.root.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.cloud_run_runtime.email}"
}

resource "google_secret_manager_secret" "runtime" {
  for_each = local.secret_ids

  secret_id = each.value
  labels    = var.labels

  replication {
    auto {}
  }

  depends_on = [google_project_service.required]
}

resource "google_secret_manager_secret_iam_member" "runtime_secret_accessor" {
  for_each = google_secret_manager_secret.runtime

  secret_id = each.value.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.cloud_run_runtime.email}"
}

resource "google_cloud_run_v2_job" "iceflo_signal" {
  name     = var.cloud_run_job_name
  location = var.region
  labels   = var.labels

  template {
    template {
      service_account = google_service_account.cloud_run_runtime.email
      timeout         = var.cloud_run_job_timeout

      containers {
        image = var.cloud_run_image
        args  = var.cloud_run_job_args

        env {
          name  = "ICEFLO_GCS_ROOT_BUCKET"
          value = google_storage_bucket.root.name
        }

        env {
          name = "ICEFLO_MINDFUL_OREGON_DRIVE_FOLDER_ID"
          value_source {
            secret_key_ref {
              secret  = google_secret_manager_secret.runtime["iceflo-mindful-oregon-drive-folder-id"].secret_id
              version = "latest"
            }
          }
        }

        env {
          name = "ICEFLO_GOOGLE_OAUTH_CLIENT_SECRETS_PATH"
          value = "/var/secrets/google/client_secret.json"
        }

        env {
          name = "ICEFLO_MINDFUL_OREGON_GOOGLE_TOKEN_PATH"
          value = "/var/secrets/google-token/mindful_oregon_token.json"
        }

        volume_mounts {
          name       = "google-oauth-secrets"
          mount_path = "/var/secrets/google"
        }

        volume_mounts {
          name       = "google-oauth-token"
          mount_path = "/var/secrets/google-token"
        }
      }

      volumes {
        name = "google-oauth-secrets"

        secret {
          secret = google_secret_manager_secret.runtime["iceflo-google-oauth-client-secrets"].secret_id

          items {
            version = "latest"
            path    = "client_secret.json"
          }
        }
      }

      volumes {
        name = "google-oauth-token"

        secret {
          secret = google_secret_manager_secret.runtime["iceflo-mindful-oregon-google-token"].secret_id

          items {
            version = "latest"
            path    = "mindful_oregon_token.json"
          }
        }
      }
    }
  }

  depends_on = [google_project_service.required]
}
