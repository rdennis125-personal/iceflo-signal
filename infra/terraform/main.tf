locals {
  mindful_oregon_prod_data_root = var.mindful_oregon_prod_data_root != "" ? var.mindful_oregon_prod_data_root : var.mindful_oregon_test_data_root

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
    "sources/simple_practice/test/landing/incoming/",
    "sources/simple_practice/test/landing/archive/",
    "sources/simple_practice/test/landing/rejected/",
    "sources/simple_practice/prod/landing/incoming/",
    "sources/simple_practice/prod/landing/archive/",
    "sources/simple_practice/prod/landing/rejected/",
    "edw/test/raw/",
    "edw/test/normalized/",
    "edw/test/facts/",
    "edw/test/dimensions/",
    "edw/test/curated/",
    "edw/test/presentation/",
    "edw/prod/raw/",
    "edw/prod/normalized/",
    "edw/prod/facts/",
    "edw/prod/dimensions/",
    "edw/prod/curated/",
    "edw/prod/presentation/",
    "utility/test/config/",
    "utility/test/schemas/",
    "utility/test/templates/",
    "utility/test/reference/",
    "utility/prod/config/",
    "utility/prod/schemas/",
    "utility/prod/templates/",
    "utility/prod/reference/",
  ])

  secret_ids = toset([
    "iceflo-mindful-oregon-simple-practice-test-incoming-folder-id",
    "iceflo-google-oauth-client-secrets",
    "iceflo-mindful-oregon-google-token",
  ])

  cloud_run_jobs = length(var.cloud_run_jobs) > 0 ? var.cloud_run_jobs : {
    iceflo_signal = {
      name = var.cloud_run_job_name
      args = var.cloud_run_job_args
    }
  }
}

resource "google_project_service" "required" {
  for_each = var.enable_project_services ? local.project_services : toset([])

  project            = var.project_id
  service            = each.value
  disable_on_destroy = false
}

resource "google_storage_bucket" "client_data_root" {
  count = var.manage_client_data_root_bucket ? 1 : 0

  name                        = var.mindful_oregon_test_data_root
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
      matches_prefix = ["sources/simple_practice/prod/landing/archive/"]
    }

    action {
      type = "SetStorageClass"
      storage_class = "NEARLINE"
    }
  }
}

data "google_storage_bucket" "client_data_root" {
  count = var.manage_client_data_root_bucket ? 0 : 1

  name = var.mindful_oregon_test_data_root
}

resource "google_storage_bucket_object" "prefix_placeholders" {
  for_each = local.storage_prefixes

  bucket       = var.mindful_oregon_test_data_root
  name         = "${each.value}.keep"
  source       = "${path.module}/placeholders/.keep"
  content_type = "text/plain"

  depends_on = [google_storage_bucket.client_data_root]
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
  bucket = var.mindful_oregon_test_data_root
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.cloud_run_runtime.email}"

  depends_on = [google_storage_bucket.client_data_root]
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
  for_each = local.cloud_run_jobs

  name                = each.value.name
  location            = var.region
  labels              = var.labels
  deletion_protection = false

  template {
    template {
      service_account = google_service_account.cloud_run_runtime.email
      timeout         = var.cloud_run_job_timeout

      containers {
        image = var.cloud_run_image
        args  = each.value.args

        env {
          name  = "ICEFLO_MINDFUL_OREGON_TEST_DATA_ROOT"
          value = var.mindful_oregon_test_data_root
        }

        env {
          name  = "ICEFLO_MINDFUL_OREGON_PROD_DATA_ROOT"
          value = local.mindful_oregon_prod_data_root
        }

        env {
          name = "ICEFLO_MINDFUL_OREGON_SIMPLE_PRACTICE_TEST_INCOMING_FOLDER_ID"
          value_source {
            secret_key_ref {
              secret  = google_secret_manager_secret.runtime["iceflo-mindful-oregon-simple-practice-test-incoming-folder-id"].secret_id
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
