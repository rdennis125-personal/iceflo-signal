# ICEFLO Signal Terraform

This Terraform scaffold creates the initial Google Cloud Storage bucket and prefix placeholders for ICEFLO Signal.

The storage layout mirrors `storage_sample/`:

```text
gs://<root_bucket_name>/
  landing/incoming/
  landing/archive/
  landing/rejected/
  transformed/raw/
  transformed/normalized/
  transformed/facts/
  transformed/dimensions/
  transformed/curated/
  utility/config/
  utility/schemas/
  utility/templates/
  utility/reference/
```

## Usage

```bash
terraform init
terraform plan -var-file=environments/dev.tfvars
terraform apply -var-file=environments/dev.tfvars
```

Copy `environments/dev.tfvars.example` to `environments/dev.tfvars` and set project-specific values before applying.
