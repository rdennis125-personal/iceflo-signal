# ICEFLO Signal Terraform

This Terraform scaffold creates the initial Google Cloud Storage bucket and prefix placeholders for ICEFLO Signal.

The storage layout mirrors `storage_sample/`:

```text
gs://<root_bucket_name>/
  landing/clients/mindful_oregon/simple_practice/incoming/
  landing/clients/mindful_oregon/simple_practice/archive/
  landing/clients/mindful_oregon/simple_practice/rejected/
  transformed/clients/mindful_oregon/simple_practice/raw/
  transformed/clients/mindful_oregon/simple_practice/normalized/
  transformed/clients/mindful_oregon/simple_practice/facts/
  transformed/clients/mindful_oregon/simple_practice/dimensions/
  transformed/clients/mindful_oregon/simple_practice/curated/
  utility/clients/mindful_oregon/simple_practice/config/
  utility/clients/mindful_oregon/simple_practice/schemas/
  utility/clients/mindful_oregon/simple_practice/templates/
  utility/clients/mindful_oregon/simple_practice/reference/
```

## Usage

```bash
terraform init
terraform plan -var-file=environments/dev.tfvars
terraform apply -var-file=environments/dev.tfvars
```

Copy `environments/dev.tfvars.example` to `environments/dev.tfvars` and set project-specific values before applying.
