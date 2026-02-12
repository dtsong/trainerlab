# TrainerLab Operations Guide

This guide covers operational procedures for managing the TrainerLab production environment.

## Table of Contents

- [Environment Overview](#environment-overview)
- [Prerequisites](#prerequisites)
- [Closed Beta Smoke Test](#closed-beta-smoke-test)
- [Pipeline Management](#pipeline-management)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)
- [Database Operations](#database-operations)

## Closed Beta Smoke Test

Use `docs/CLOSED_BETA_SMOKE_TEST.md` after deploying to production or before inviting a new batch.

## Environment Overview

| Resource           | Value                                |
| ------------------ | ------------------------------------ |
| **GCP Project**    | `trainerlab-prod`                    |
| **Region**         | `us-west1`                           |
| **API Service**    | `trainerlab-api` (Cloud Run)         |
| **Database**       | Cloud SQL (PostgreSQL with pgvector) |
| **Scheduled Jobs** | Cloud Scheduler triggers pipelines   |

### Architecture

```
Cloud Scheduler → Cloud Run (trainerlab-api) → Cloud SQL
                      ↓
              External APIs:
              - LimitlessTCG (EN + JP tournaments)
              - TCGdex (card data)
              - Pokecabook (JP adoption + translations)
```

## Prerequisites

### Required Tools

```bash
# Install gcloud CLI
# macOS
brew install google-cloud-sdk

# Authenticate
gcloud auth login

# Set project
gcloud config set project trainerlab-prod
```

### Required IAM Roles

**For Production Operations** (Recommended):

- `roles/iam.serviceAccountTokenCreator` on `trainerlab-ops@trainerlab-prod.iam.gserviceaccount.com`
- `roles/logging.viewer` - View logs
- `roles/cloudscheduler.viewer` - View scheduled jobs

**For Development** (when `scheduler_auth_bypass=true`):

- `roles/run.invoker` - Invoke Cloud Run services (direct access)
- `roles/logging.viewer` - View logs

### Service Account Setup

The `trainerlab-ops` service account is used for manual operations. To get access:

1. Ask your GCP admin to grant you impersonation rights:

```bash
# Admin runs this to grant you access
gcloud iam service-accounts add-iam-policy-binding \
  trainerlab-ops@trainerlab-prod.iam.gserviceaccount.com \
  --member="user:YOUR_EMAIL@example.com" \
  --role="roles/iam.serviceAccountTokenCreator"
```

2. Or add your email to `operations_admins` in Terraform:

```hcl
# In terraform.tfvars
operations_admins = ["your.email@example.com"]
```

### Test Script Setup

```bash
# Install jq for JSON parsing
brew install jq

# Make script executable
chmod +x scripts/test-production-scrapers.sh

# Verify it works
./scripts/test-production-scrapers.sh --help
```

## Pipeline Management

### Available Pipelines

| Pipeline             | Data Source                          | Schedule (UTC) | Purpose                                 |
| -------------------- | ------------------------------------ | -------------- | --------------------------------------- |
| `discover-en`        | LimitlessTCG (official + grassroots) | `0 6 * * *`    | Discover + enqueue EN tournaments       |
| `discover-jp`        | LimitlessTCG JP City Leagues         | `0 7 * * *`    | Discover + enqueue JP tournaments (BO1) |
| `compute-meta`       | Internal DB                          | `0 8 * * *`    | Meta snapshots & deck stats             |
| `sync-cards`         | TCGdex                               | `0 3 * * 0`    | Card database sync                      |
| `sync-card-mappings` | LimitlessTCG (JP↔EN equivalents)     | `0 4 * * 0`    | JP↔EN card ID mapping for archetypes    |

### Manual Pipeline Testing

#### Read-Only Checks (No Writes)

```bash
# Verify data without triggering pipelines
./scripts/verify-pipelines.sh --verify-only

# Deep data quality checks
./scripts/verify-data.sh --group=tournaments

# Check recent Cloud Run errors
./scripts/test-production-scrapers.sh --check-logs
```

#### Pipeline Runs (Writes to Production)

```bash
# Run a single pipeline via Cloud Scheduler
./scripts/test-production-scrapers.sh --pipeline=discover-en --confirm

# Run JP mapping sync
./scripts/test-production-scrapers.sh --pipeline=sync-card-mappings --confirm

# Run all pipelines (triggered in parallel)
./scripts/test-production-scrapers.sh --all --confirm
```

**⚠️ Warning:** Cloud Scheduler jobs always run with Terraform-configured parameters
(`dry_run=false`). To change lookback days or formats, update
`terraform/modules/scheduler/main.tf`.

### Viewing Scheduled Jobs

```bash
# List all scheduled jobs
gcloud scheduler jobs list --project=trainerlab-prod

# View specific job details
gcloud scheduler jobs describe trainerlab-discover-en --location=us-west1

# View recent executions
gcloud scheduler jobs describe trainerlab-discover-en --location=us-west1 | grep lastAttemptTime
```

### Manually Triggering Scheduled Jobs

```bash
# Trigger English discovery job
gcloud scheduler jobs run trainerlab-discover-en --location=us-west1

# Trigger Japanese discovery job
gcloud scheduler jobs run trainerlab-discover-jp --location=us-west1

# Trigger card sync
gcloud scheduler jobs run trainerlab-sync-cards --location=us-west1

# Trigger card mapping sync
gcloud scheduler jobs run trainerlab-sync-card-mappings --location=us-west1

# Trigger meta computation
gcloud scheduler jobs run trainerlab-compute-meta --location=us-west1
```

**Note:** This triggers the scheduled job, which will invoke the API with production parameters (not dry-run).

## Monitoring

### Health Checks

```bash
# Quick health check
SERVICE_URL=$(gcloud run services describe trainerlab-api --region=us-west1 --format='value(status.url)')
TOKEN=$(gcloud auth print-identity-token --audiences=$SERVICE_URL)
curl -H "Authorization: Bearer $TOKEN" "$SERVICE_URL/api/v1/health"
```

**Healthy Response:**

```json
{
  "status": "healthy",
  "database": "connected",
  "version": "0.1.0"
}
```

### Cloud Logs

```bash
# Check for recent errors
./scripts/test-production-scrapers.sh --check-logs

# View real-time logs
gcloud run services logs read trainerlab-api \
  --region=us-west1 \
  --limit=50 \
  --format=json

# Filter by severity
gcloud logging read \
  "resource.type=cloud_run_revision AND severity>=ERROR" \
  --limit=20 \
  --format=json

# Filter by time range
gcloud logging read \
  "resource.type=cloud_run_revision AND timestamp>\"2024-01-01T00:00:00Z\"" \
  --limit=50
```

### Metrics & Dashboards

Access Cloud Run metrics in GCP Console:

1. Navigate to Cloud Run → `trainerlab-api`
2. Click "Metrics" tab
3. View:
   - Request count
   - Request latency
   - Container instance count
   - Error rate

### Data Verification

```bash
# Check recent tournaments
SERVICE_URL=$(gcloud run services describe trainerlab-api --region=us-west1 --format='value(status.url)')
TOKEN=$(gcloud auth print-identity-token --audiences=$SERVICE_URL)

curl -H "Authorization: Bearer $TOKEN" \
  "$SERVICE_URL/api/v1/tournaments?limit=10&sort_by=date&order=desc" | jq

# Check meta snapshots
curl -H "Authorization: Bearer $TOKEN" \
  "$SERVICE_URL/api/v1/meta/snapshots?limit=5" | jq

# Check TPCI post-major readiness (admin-only)
# (Generate an admin JWT or use existing admin tooling)
./scripts/cloud/check-tpci-readiness.sh

# Automated TPCI readiness alerts (GitHub + Discord)
# - Configure API env: READINESS_ALERT_TOKEN (random, long)
# - Configure GitHub repo secrets:
#   - READINESS_ALERT_TOKEN (same value)
#   - DISCORD_WEBHOOK_URL (Discord channel webhook URL)
# - Workflow: .github/workflows/tpci-readiness-alert.yml
# - Endpoint used by workflow: GET /api/v1/ops/readiness/tpci (Bearer token)

# Check card count
curl -H "Authorization: Bearer $TOKEN" \
  "$SERVICE_URL/api/v1/cards?limit=1" | jq '.total'
```

## Troubleshooting

### Common Issues

#### 1. Pipeline Returns No Data

**Symptoms:**

```json
{
  "success": true,
  "tournaments_saved": 0,
  "placements_saved": 0
}
```

**Possible Causes:**

- No new tournaments in the lookback period
- External API is down or rate-limiting
- Data format changed on source site

**Investigation:**

```bash
# Check Cloud Logs for HTTP errors
gcloud logging read \
  "resource.type=cloud_run_revision AND textPayload=~\"HTTP.*error\"" \
  --limit=20

# Re-run discovery pipeline
./scripts/test-production-scrapers.sh --pipeline=discover-en --confirm

# If lookback window is too short, update the scheduler job body in Terraform:
# terraform/modules/scheduler/main.tf

# Check external API directly
curl "https://play.limitlesstcg.com/tournaments/completed?game=POKEMON"
```

#### 2. Authentication Failed

**Error:**

```
ERROR: Failed to get authentication token.
```

**Solution:**

```bash
# Re-authenticate
gcloud auth login

# Verify you have the correct role
gcloud run services get-iam-policy trainerlab-api --region=us-west1

# Request access if needed (ask project owner)
gcloud run services add-iam-policy-binding trainerlab-api \
  --region=us-west1 \
  --member="user:YOUR_EMAIL@example.com" \
  --role="roles/run.invoker"
```

#### 2a. OAuth Subject Drift / Closed Beta Access Seems "Stuck"

**Symptoms:**

- User is signed in via Google OAuth on `trainerlab.io` but sees closed beta access gate
- API returns 401/403 unexpectedly even after admin grants access

**Notes:**

- The API verifies Auth.js JWTs with `NEXTAUTH_SECRET`.
- User lookup prefers `auth_provider_id` (`sub`), with a fallback by email to avoid lockouts
  if provider subject identifiers drift.

**Quick checks:**

```bash
SERVICE_URL=$(gcloud run services describe trainerlab-api --region=us-west1 --format='value(status.url)')

# /health and /health/pipeline do not require auth
curl -sS "$SERVICE_URL/api/v1/health" | jq
curl -sS "$SERVICE_URL/api/v1/health/pipeline" | jq '.status'
```

If access changes were recently granted, ensure the frontend refreshes the session/token.
In the UI, a sign-out/sign-in cycle is the most deterministic reset.

#### 3. Database Connection Failed

**Symptoms:**

```json
{
  "status": "healthy",
  "database": "error"
}
```

**Investigation:**

```bash
# Check Cloud SQL instance status
gcloud sql instances list --project=trainerlab-prod

# View Cloud SQL logs
gcloud sql operations list --instance=trainerlab-db

# Check connection from Cloud Run
gcloud run services describe trainerlab-api --region=us-west1 | grep -A 5 "cloudsql"
```

#### 4. Pipeline Timeout

**Error:**

```json
{
  "success": false,
  "error": "Pipeline execution timeout"
}
```

**Investigation:**

- Check if external API is slow
- Reduce `lookback_days` to process less data
- Check Cloud Run timeout settings (max 60 minutes for Cloud Run 2nd gen)

```bash
# Check service timeout configuration
gcloud run services describe trainerlab-api --region=us-west1 | grep timeout
```

#### 5. Rate Limiting

**Symptoms:** Errors mentioning "429" or "rate limit" in logs.

**Solutions:**

- Scrapers include built-in delays between requests
- If rate-limited, wait before retrying
- Check if external API has daily limits

### Debug Mode

To see detailed execution logs:

```bash
# Enable verbose logging
export LOGLEVEL=DEBUG

# Or modify Cloud Run service environment
gcloud run services update trainerlab-api \
  --region=us-west1 \
  --set-env-vars="LOGLEVEL=DEBUG"

# Don't forget to revert after debugging
gcloud run services update trainerlab-api \
  --region=us-west1 \
  --set-env-vars="LOGLEVEL=INFO"
```

## Database Operations

### Connecting to Cloud SQL

```bash
# Via Cloud SQL Proxy
cloud-sql-proxy trainerlab-prod:us-west1:trainerlab-db

# Then connect with psql
psql "host=127.0.0.1 port=5432 dbname=trainerlab user=trainerlab"
```

### Common Queries

```sql
-- Check recent tournament count
SELECT COUNT(*), MAX(date), MIN(date)
FROM tournaments
WHERE date >= CURRENT_DATE - INTERVAL '30 days';

-- Check deck archetype distribution
SELECT archetype, COUNT(*) as placement_count
FROM placements
JOIN tournaments t ON placements.tournament_id = t.id
WHERE t.date >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY archetype
ORDER BY placement_count DESC
LIMIT 20;

-- Check latest meta snapshot
SELECT *
FROM meta_snapshots
ORDER BY snapshot_date DESC
LIMIT 1;

-- Check card sync status
SELECT COUNT(*) as card_count, MAX(last_modified) as last_update
FROM cards;
```

### Backup & Recovery

Backups are automated via Cloud SQL:

- **Frequency:** Daily at 1 AM PT
- **Retention:** 7 days
- **Location:** Multi-regional (US)

**Restore from Backup:**

```bash
# List available backups
gcloud sql backups list --instance=trainerlab-db

# Restore to a specific backup
gcloud sql backups restore BACKUP_ID --backup-instance=trainerlab-db
```

## Emergency Procedures

### Disable Automated Scrapers

If pipelines are causing issues:

```bash
# Pause all scheduled jobs
gcloud scheduler jobs pause trainerlab-discover-en --location=us-west1
gcloud scheduler jobs pause trainerlab-discover-jp --location=us-west1
gcloud scheduler jobs pause trainerlab-compute-meta --location=us-west1
gcloud scheduler jobs pause trainerlab-sync-cards --location=us-west1
gcloud scheduler jobs pause trainerlab-sync-card-mappings --location=us-west1

# Resume when ready
gcloud scheduler jobs resume trainerlab-discover-en --location=us-west1
gcloud scheduler jobs resume trainerlab-discover-jp --location=us-west1
gcloud scheduler jobs resume trainerlab-compute-meta --location=us-west1
gcloud scheduler jobs resume trainerlab-sync-cards --location=us-west1
gcloud scheduler jobs resume trainerlab-sync-card-mappings --location=us-west1
```

### Rollback Deployment

```bash
# List revisions
gcloud run revisions list --service=trainerlab-api --region=us-west1

# Rollback to previous revision
gcloud run services update-traffic trainerlab-api \
  --region=us-west1 \
  --to-revisions=REVISION_NAME=100
```

### Scale Down Service

If API is overloaded:

```bash
# Reduce max instances
gcloud run services update trainerlab-api \
  --region=us-west1 \
  --max-instances=5

# Or scale to zero temporarily
gcloud run services update trainerlab-api \
  --region=us-west1 \
  --max-instances=0
```

## Support

For issues not covered in this guide:

1. Check Cloud Logs for detailed error messages
2. Review recent deployments in Cloud Run console
3. Consult the development team
4. Reference `/docs/SPEC.md` for system design details

## Changelog

| Date       | Change                           |
| ---------- | -------------------------------- |
| 2024-01-XX | Initial operations guide created |
