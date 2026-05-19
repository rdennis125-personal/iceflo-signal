locals {
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
