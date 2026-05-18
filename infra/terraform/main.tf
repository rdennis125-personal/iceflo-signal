locals {
  storage_prefixes = toset([
    "landing/incoming/",
    "landing/archive/",
    "landing/rejected/",
    "transformed/raw/",
    "transformed/normalized/",
    "transformed/facts/",
    "transformed/dimensions/",
    "transformed/curated/",
    "utility/config/",
    "utility/schemas/",
    "utility/templates/",
    "utility/reference/",
  ])
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
      matches_prefix = ["landing/archive/"]
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
