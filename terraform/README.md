# TrainerLab Terraform Infrastructure

This directory contains Terraform configuration for TrainerLab's GCP infrastructure.

## Architecture

```
Terraform manages:
├── Service Accounts (API, Scheduler, Operations)
├── IAM Bindings & Permissions
├── Cloud SQL (PostgreSQL + pgvector)
├── Cloud Run Service (configuration only)
├── Cloud Scheduler Jobs
├── Artifact Registry
└── Secrets Manager

GitHub Actions manages:
└── Cloud Run Deployments (image updates)
```

## Deployment Pattern

### Infrastructure Changes (Terraform)

Use Terraform for:

- Creating/modifying service accounts
- Changing IAM permissions
- Database configuration changes
- Environment variable updates
- Resource scaling limits
- Networking configuration

```bash
cd terraform
terraform plan
terraform apply
```

### Application Deployments (CI/CD)

GitHub Actions automatically deploys on push to `main`:

1. Builds Docker image with commit SHA tag
2. Pushes to Artifact Registry
3. Runs database migrations
4. Deploys to Cloud Run using image digest

**Important:** CI/CD bypasses Terraform for image deployments to enable fast, safe rollouts without infrastructure drift.

## Configuration

### Initial Setup

**Quick Start (all defaults):**

```bash
cd terraform
terraform init
terraform plan  # Works immediately with defaults!
```

**Custom Configuration:**

1. Copy the example variables file:

   ```bash
   cp terraform.tfvars.example terraform.tfvars
   ```

2. Edit `terraform.tfvars` to override defaults:
   - `operations_admins` - Add your email for manual testing access
   - Other optional overrides as needed

3. Apply:
   ```bash
   terraform plan
   terraform apply
   ```

### Variables

**All variables have defaults** - you only need to override what you need.

| Variable            | Description                          | Default                                |
| ------------------- | ------------------------------------ | -------------------------------------- |
| `project_id`        | GCP project ID                       | `trainerlab-prod`                      |
| `region`            | GCP region                           | `us-west1`                             |
| `environment`       | Environment name                     | `prod`                                 |
| `api_image`         | Docker image URI                     | Computed from project (uses `:latest`) |
| `operations_admins` | Emails allowed to impersonate ops SA | `[]`                                   |
| `db_tier`           | Cloud SQL machine type               | `db-f1-micro`                          |
| `db_disk_size`      | Cloud SQL disk size (GB)             | `10`                                   |
| `cors_origins`      | Allowed CORS origins                 | `trainerlab.app` domains               |
| `tcgdex_url`        | TCGdex API endpoint                  | `https://api.tcgdex.net/v2`            |
| `timezone`          | Scheduler timezone                   | `America/New_York`                     |
| `scheduler_paused`  | Pause scheduler jobs                 | `false`                                |
| `github_repo`       | GitHub repo for OIDC                 | `dtsong/trainerlab`                    |
| `custom_domain`     | Custom domain for API                | `""` (none)                            |

### API Image Handling

The `api_image` variable has smart defaults:

**Default (no value provided):**

```
us-west1-docker.pkg.dev/trainerlab-prod/trainerlab-api/api:latest
```

**CI/CD Override:**

```
us-west1-docker.pkg.dev/trainerlab-prod/trainerlab-api/api@sha256:abc123...
```

**Manual Override (if needed):**

```hcl
# terraform.tfvars
api_image = "us-west1-docker.pkg.dev/trainerlab-prod/trainerlab-api/api:v1.2.3"
```

## State Management

Terraform state is stored in GCS:

- **Bucket:** `trainerlab-tfstate-1d22e2f5`
- **Prefix:** `trainerlab-prod/app`

State is managed by the foundation layer and shared across the team.

## Modules

### `cloud_run`

Configures Cloud Run service with:

- Container image
- Environment variables
- Secret mounting
- IAM permissions
- VPC connector

### `cloud_sql`

Provisions PostgreSQL with:

- pgvector extension
- Private IP networking
- Automated backups
- User/database setup

### `scheduler`

Creates Cloud Scheduler jobs for:

- Daily tournament scraping (EN, JP)
- Daily meta computation
- Weekly card sync

## Common Operations

### Update Environment Variables

1. Edit `terraform/main.tf` → `module "api"` → `env_vars`
2. Apply changes:
   ```bash
   terraform apply
   ```

### Add Operations Team Member

1. Edit `terraform.tfvars`:

   ```hcl
   operations_admins = [
     "existing@example.com",
     "new.member@example.com",
   ]
   ```

2. Apply:

   ```bash
   terraform apply
   ```

3. New member can now run:
   ```bash
   ./scripts/test-production-scrapers.sh --use-service-account
   ```

### Scale Database

1. Edit `terraform.tfvars`:

   ```hcl
   db_tier = "db-custom-2-8192"  # 2 vCPU, 8GB RAM
   db_disk_size = 50              # 50GB SSD
   ```

2. Apply:
   ```bash
   terraform apply
   ```

### Pause Schedulers (Emergency)

```bash
# Via Terraform
terraform apply -var="scheduler_paused=true"

# Or via gcloud (faster)
gcloud scheduler jobs pause trainerlab-discover-en --location=us-west1
```

## Troubleshooting

### "api_image" Prompts for Input

If you see:

```
var.api_image
  Docker image for the API

  Enter a value:
```

**Cause:** Old Terraform cache before the default was added.

**Fix:**

```bash
rm -rf .terraform/
terraform init
terraform plan  # Should work without prompting
```

### State Lock Error

**Cause:** Concurrent Terraform runs or stale lock.

**Fix:**

```bash
# Wait for other operations to complete, or force unlock:
terraform force-unlock <LOCK_ID>
```

### Drift Detection

**Cause:** CI/CD deployed a different image than Terraform expects.

**Fix:** This is expected! CI/CD manages images, Terraform manages infrastructure.

```bash
# Refresh state to match reality
terraform refresh

# Or ignore image changes in plan
terraform plan -var="api_image=$(gcloud run services describe trainerlab-api --region=us-west1 --format='value(spec.template.spec.containers[0].image)')"
```

## Security

- Service accounts follow principle of least privilege
- Secrets stored in Secret Manager (not in Terraform state)
- Database password auto-generated and rotated via Terraform
- Operations SA requires explicit impersonation grants
- All IAM changes audited via Cloud Logging

## Further Reading

- [GCP Cloud Run Docs](https://cloud.google.com/run/docs)
- [Terraform Google Provider](https://registry.terraform.io/providers/hashicorp/google/latest/docs)
- [OPERATIONS.md](../docs/OPERATIONS.md) - Running manual operations
