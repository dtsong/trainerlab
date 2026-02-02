# TrainerLab Operations Guide

This guide covers operational procedures for managing the TrainerLab production environment.

## Table of Contents

- [Environment Overview](#environment-overview)
- [Prerequisites](#prerequisites)
- [Scraper Management](#scraper-management)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)
- [Database Operations](#database-operations)

## Environment Overview

| Resource           | Value                                |
| ------------------ | ------------------------------------ |
| **GCP Project**    | `trainerlab-prod`                    |
| **Region**         | `us-west1`                           |
| **API Service**    | `trainerlab-api` (Cloud Run)         |
| **Database**       | Cloud SQL (PostgreSQL with pgvector) |
| **Scheduled Jobs** | Cloud Scheduler triggers scrapers    |

### Architecture

```
Cloud Scheduler → Cloud Run (trainerlab-api) → Cloud SQL
                      ↓
              External APIs:
              - LimitlessTCG (EN tournaments)
              - Pokémon Card Lab (JP tournaments)
              - TCGdex (card data)
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

- `roles/run.invoker` - Invoke Cloud Run services
- `roles/logging.viewer` - View logs
- `roles/cloudscheduler.viewer` - View scheduled jobs

### Test Script Setup

```bash
# Install jq for JSON parsing
brew install jq

# Make script executable
chmod +x scripts/test-production-scrapers.sh

# Verify it works
./scripts/test-production-scrapers.sh --help
```

## Scraper Management

### Available Scrapers

| Pipeline       | Data Source      | Schedule           | Purpose                     |
| -------------- | ---------------- | ------------------ | --------------------------- |
| `scrape-en`    | LimitlessTCG     | Daily 2 AM PT      | English tournament data     |
| `scrape-jp`    | Pokémon Card Lab | Daily 3 AM PT      | Japanese tournament data    |
| `compute-meta` | Internal DB      | Daily 4 AM PT      | Meta snapshots & deck stats |
| `sync-cards`   | TCGdex           | Weekly Sun 1 AM PT | Card database sync          |

### Manual Scraper Testing

#### Safe Dry-Run (Recommended First Step)

```bash
# Test English scraper without writing data
./scripts/test-production-scrapers.sh --pipeline=scrape-en

# Test all scrapers in dry-run mode
./scripts/test-production-scrapers.sh --all

# Test with custom lookback period
./scripts/test-production-scrapers.sh --pipeline=scrape-en --lookback-days=14

# Test specific format
./scripts/test-production-scrapers.sh --pipeline=scrape-en --format=standard
```

#### Live Runs (Writes to Database)

```bash
# Live run with verification
./scripts/test-production-scrapers.sh --pipeline=scrape-en --no-dry-run --verify

# Live run with custom parameters
./scripts/test-production-scrapers.sh \
  --pipeline=scrape-en \
  --no-dry-run \
  --lookback-days=3 \
  --format=standard \
  --verify
```

**⚠️ Live Run Warning:** The script will show a 5-second warning before executing live runs. Press Ctrl+C to cancel.

### Pipeline Parameters

#### Scrape Pipelines (`scrape-en`, `scrape-jp`)

```json
{
  "dry_run": true, // false to write data
  "lookback_days": 7, // How far back to scrape
  "game_format": "all" // "standard", "expanded", or "all"
}
```

**Expected Response:**

```json
{
  "success": true,
  "tournaments_saved": 12,
  "placements_saved": 384,
  "errors": [],
  "message": "Pipeline completed successfully"
}
```

#### Compute Meta Pipeline

```json
{
  "dry_run": true,
  "lookback_days": 30, // Window for meta calculation
  "snapshot_date": null // Optional: specific date (YYYY-MM-DD)
}
```

**Expected Response:**

```json
{
  "success": true,
  "snapshots_saved": 2, // One per format (standard, expanded)
  "errors": [],
  "message": "Meta computation completed"
}
```

#### Sync Cards Pipeline

```json
{
  "dry_run": true
}
```

**Expected Response:**

```json
{
  "success": true,
  "cards_synced": 1234,
  "sets_synced": 45,
  "errors": [],
  "message": "Card sync completed"
}
```

### Viewing Scheduled Jobs

```bash
# List all scheduled jobs
gcloud scheduler jobs list --project=trainerlab-prod

# View specific job details
gcloud scheduler jobs describe scrape-en-daily --location=us-west1

# View recent executions
gcloud scheduler jobs describe scrape-en-daily --location=us-west1 | grep lastAttemptTime
```

### Manually Triggering Scheduled Jobs

```bash
# Trigger English scraper job
gcloud scheduler jobs run scrape-en-daily --location=us-west1

# Trigger Japanese scraper job
gcloud scheduler jobs run scrape-jp-daily --location=us-west1

# Trigger meta computation
gcloud scheduler jobs run compute-meta-daily --location=us-west1
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

# Check card count
curl -H "Authorization: Bearer $TOKEN" \
  "$SERVICE_URL/api/v1/cards?limit=1" | jq '.total'
```

## Troubleshooting

### Common Issues

#### 1. Scraper Returns No Data

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

# Try with longer lookback period
./scripts/test-production-scrapers.sh --pipeline=scrape-en --lookback-days=30

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

If scrapers are causing issues:

```bash
# Pause all scheduled jobs
gcloud scheduler jobs pause scrape-en-daily --location=us-west1
gcloud scheduler jobs pause scrape-jp-daily --location=us-west1
gcloud scheduler jobs pause compute-meta-daily --location=us-west1

# Resume when ready
gcloud scheduler jobs resume scrape-en-daily --location=us-west1
gcloud scheduler jobs resume scrape-jp-daily --location=us-west1
gcloud scheduler jobs resume compute-meta-daily --location=us-west1
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
