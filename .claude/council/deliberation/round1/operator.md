# Operator Position — Data Pipeline Infrastructure Overhaul

## Core Recommendation

Add request timeout configuration to Cloud Run (currently defaulting to 300s), implement structured logging with Cloud Logging for pipeline observability, and design a phased reprocessing strategy that leverages Cloud Tasks rate limiting to avoid cost spikes during the historical data wipe/re-scrape operation.

**Key argument:**

The current infrastructure is production-ready for incremental pipeline operations but lacks critical operational safeguards for the planned full data reprocess. Cloud Run has a 300-second default request timeout which works for current pipelines but creates a hidden failure mode for bulk operations. More critically, we have no operational visibility into data quality issues like the Cinderace sprite misidentification. The logging setup uses basic stdout capture without structured fields for querying, making post-mortems reactive rather than proactive. For a safe full reprocess, we need explicit timeout configuration in Terraform (not relying on GCP defaults), structured logging with pipeline-specific fields (tournament_id, sprite_detected, card_mapping_confidence), and Cloud Tasks rate limit tuning to prevent cost overruns when re-scraping thousands of tournaments. The Cloud Tasks queue is already configured at 0.5 tasks/second (conservative for new data), but bulk reprocessing needs separate throttling controls.

## Reprocessing Strategy — Phased Rollout

### Phase 1: Safety Infrastructure (1 day)

- Add explicit `timeout_seconds = 600` to Cloud Run Terraform module
- Implement structured logging service with JSON fields for Cloud Logging
- Create `/api/v1/pipeline/reprocess-bulk` endpoint with progress tracking
- Add database migration for `reprocessing_batch` table (tracks progress, enables resume on failure)

### Phase 2: Pilot Reprocess (1 day)

- Reprocess 1 month of JP tournaments (estimate 200-300 tournaments)
- Monitor Cloud Run request durations, memory usage, Cloud SQL connection pool saturation
- Verify sprite extraction, card mapping accuracy on known-good data
- Validate Cloud Tasks deduplication prevents double-processing

### Phase 3: Full Reprocess (3 days, automated)

- Wipe tournaments table (keep backups in Cloud SQL automated backups, 14-day retention)
- Enqueue all historical tournaments via Cloud Tasks (estimate 3000-5000 tournaments)
- At 0.5 tasks/sec, full reprocess completes in 100-167 minutes per 3000 tournaments
- Monitor queue depth, error rate, Cloud Run instance scaling

### Phase 4: Validation (1 day)

- Compare archetype shares before/after reprocess (expect differences due to Cinderace fix)
- Audit sprite extraction coverage (target: >95% of JP decks have sprites extracted)
- Run meta computation for last 90 days, verify consistency

### Cost Estimate for Full Reprocess

- Cloud Run: 3000 tournaments × 30s avg processing time = 25 CPU-hours at $0.00002400/vCPU-second = $2.16
- Cloud SQL: Negligible (existing instance, queries are lightweight)
- Cloud Tasks: 3000 tasks × $0.40 per million = $0.0012
- **Total reprocess cost: ~$2.20** (assuming no errors requiring retries)

## Pipeline Monitoring — Detect Cinderace-Class Failures

### Critical Metrics to Instrument

1. **Sprite extraction success rate** (per region, per tournament)
   - Alert if JP extraction rate <90% for any tournament batch
   - Log sprite URLs for manual review in Cloud Storage
2. **Card mapping confidence** (JP to EN ID mapping)
   - Track `unmatched_cards_count` per tournament
   - Alert if >10% of cards in a deck have no EN mapping
3. **Archetype classification drift** (detect sudden meta shifts that might be data quality issues)
   - Compare daily archetype shares to 7-day rolling average
   - Alert if any archetype moves >15 percentage points in one day (likely data issue, not meta shift)
4. **Pipeline execution time** (detect performance regressions)
   - P50, P95, P99 durations for `discover-en`, `discover-jp`, `process-tournament`, `compute-meta`
   - Alert if P95 exceeds expected duration by 2x

### Implementation Approach

- Add `StructuredLogger` service wrapping Python logging with JSON formatter
- Key fields: `pipeline`, `tournament_id`, `region`, `sprite_count`, `unmatched_cards`, `duration_ms`
- Cloud Logging auto-indexes JSON fields, enabling queries like:
  ```
  resource.type="cloud_run_revision"
  jsonPayload.pipeline="process-tournament"
  jsonPayload.sprite_count=0
  jsonPayload.region="JP"
  ```
- Set up Cloud Monitoring alerts on log-based metrics (e.g., "sprite extraction failures >10 in 5 minutes")

### Data Quality Dashboard (Cloud Monitoring)

Create custom dashboard with:

- Sprite extraction rate by region (last 24h, last 7d)
- Card mapping coverage (% of cards with EN IDs)
- Pipeline error rate (errors per 1000 tournaments)
- Cloud Run instance count, request latency, memory utilization
- Cloud SQL connection pool usage (prevent connection exhaustion during bulk operations)

## Cost Optimization Opportunities

### Current Monthly Costs (Estimated Based on Infrastructure)

- **Cloud Run**: db-f1-micro (0.6 GB RAM, 1 shared vCPU), min_instances=1 for prod
  - Idle cost: 1 instance × 24h × 30 days × $0.00002400/vCPU-second = $62/month (baseline)
  - Request cost: Estimate 10k requests/day × 0.5s avg = 5k vCPU-seconds/day = $3.60/month
  - **Total Cloud Run: ~$65/month**
- **Cloud SQL**: db-f1-micro (0.6 GB RAM), 10 GB SSD, regional HA disabled (ZONAL in prod per config)
  - Instance: $7.67/month
  - Storage: 10 GB × $0.17/GB-month = $1.70/month
  - Backups: 14 days × ~5 GB avg × $0.08/GB-month = $5.60/month
  - **Total Cloud SQL: ~$15/month**
- **Cloud Scheduler**: 10 jobs × $0.10/job-month = $1/month
- **Cloud Tasks**: 3k tasks/month (daily discover operations) × $0.40/million = $0.0012/month (negligible)
- **Artifact Registry**: 10 images × ~500 MB avg = 5 GB × $0.10/GB-month = $0.50/month
- **Cloud Storage (exports bucket)**: Negligible (24-hour lifecycle, <1 GB avg)
- **Secret Manager**: 3 secrets × $0.06/secret-month = $0.18/month
- **Estimated Total: $80-85/month**

### Optimization Recommendations

1. **Cloud Run min_instances=0 in prod** (currently min_instances=1)
   - Saves $62/month idle cost
   - Trade-off: Cold start latency 3-5 seconds for first request after idle
   - Recommendation: Accept cold starts for beta, set min_instances=1 when user base >100 DAU
2. **Cloud SQL ZONAL → REGIONAL HA** (already correctly configured as ZONAL in prod, good choice)
   - REGIONAL HA would cost 2.4x more ($18/month → $43/month)
   - Current setup is cost-appropriate for beta
3. **Artifact Registry image retention** (already configured: keep 10 images)
   - Good balance between rollback capability and storage cost
4. **Cloud SQL disk autoresize** (enabled, good)
   - No action needed, but monitor disk growth during reprocess
5. **Consider Cloud SQL connection pooling in Cloud Run**
   - FastAPI/SQLAlchemy already has connection pooling via `async_session_factory`
   - Current setup is optimal (no external pooler needed for this scale)

### Cost Optimization Score: 8/10

- The infrastructure is already well-optimized for beta scale
- Only actionable item: Reduce min_instances=1 → min_instances=0 to save $62/month (75% cost reduction)
- Wait to scale up until traffic justifies it

## Security Review

### Current Security Posture: Strong

1. **IAM & Service Accounts**: Well-architected
   - Separate service accounts for API, Scheduler, Operations (principle of least privilege)
   - Operations SA requires explicit impersonation (good for audit trail)
   - Workload Identity Federation for GitHub Actions (no long-lived keys, excellent)
2. **Networking**: Private by default
   - Cloud SQL private IP only, no public exposure
   - Cloud Run Direct VPC Egress to private ranges only (good, avoids VPC Connector cost)
3. **Secrets Management**: Proper use of Secret Manager
   - DB password, NextAuth secret, Anthropic API key all in Secret Manager
   - Secrets mounted as env vars (standard pattern, acceptable for Cloud Run)
4. **Container Security**: Multi-stage Dockerfile with non-root user
   - Non-root user `appuser:10001` (good)
   - Multi-stage build minimizes attack surface
5. **API Security**: Rate limiting, security headers
   - Slowapi rate limiter configured (good)
   - Security headers middleware (X-Content-Type-Options, X-Frame-Options, HSTS in prod)
6. **Authentication**: OIDC tokens for inter-service auth
   - Cloud Scheduler uses OIDC tokens to invoke Cloud Run (good, no static tokens)
   - Cloud Tasks uses OIDC tokens for process endpoint (good)

### Security Gaps to Address

1. **Missing: Anthropic API key not populated in Secret Manager**
   - `google_secret_manager_secret.anthropic_api_key` is created but version not set
   - Action: Manually set secret value via `gcloud` or Console
   - **Risk: High** — Evolution pipeline will fail silently without this key
2. **Missing: Structured audit logging for admin operations**
   - Admin router exists but no Cloud Logging audit trail for sensitive operations
   - Action: Add `@audit_log` decorator for card edits, user management
3. **Missing: API key rotation strategy**
   - Anthropic API key has no rotation policy
   - Action: Document manual rotation procedure (regenerate key, update Secret Manager)
4. **API Documentation exposed in production** (currently disabled, good)
   - `/docs` and `/redoc` are disabled unless `is_development=True` (correct)
5. **No Web Application Firewall (WAF)**
   - Cloud Armor is not configured
   - For beta, this is acceptable (Cloud Run has basic DDoS protection)
   - Add Cloud Armor when moving to general availability

### Security Action Items (Priority Order)

1. **Critical**: Populate Anthropic API key in Secret Manager (blocks Evolution pipeline)
2. **High**: Add structured audit logging for admin operations
3. **Medium**: Document secret rotation procedures in runbook
4. **Low**: Evaluate Cloud Armor for GA launch

## Scaling Considerations

### Current Capacity

- **Cloud Run**: max_instances=10, 1 CPU, 1 GB RAM per instance
  - Theoretical max throughput: 10 instances × 50 concurrent requests/instance = 500 concurrent requests
  - With 0.5s avg request duration: 500 req/sec = 43M requests/day
  - **Current scale is overkill for beta** (expecting <10k requests/day)
- **Cloud SQL**: db-f1-micro, max_connections=100
  - Each Cloud Run instance uses SQLAlchemy async pool (default pool_size=5)
  - Max Cloud Run instances: 10 × 5 connections = 50 connections
  - **Connection pool is safe** (50 < 100 max connections)
- **Cloud Tasks**: Queue rate limit 0.5 tasks/sec, max_concurrent=2
  - **This is the bottleneck for bulk reprocessing** (intentionally conservative)
  - Daily scraping is fine (discover 50 new tournaments, process over 100 seconds)
  - Bulk reprocess of 3000 tournaments takes 100 minutes (acceptable for one-time operation)

### Scaling Triggers (When to Upgrade)

1. **Cloud Run CPU throttling >10%**
   - Symptom: P95 latency increases, CPU throttling logs in Cloud Monitoring
   - Action: Increase `cpu = "2"` in Terraform (doubles cost per request)
2. **Cloud SQL connection pool exhaustion**
   - Symptom: `FATAL: remaining connection slots are reserved` errors in logs
   - Action: Upgrade to db-g1-small (1 vCPU, max_connections=500, cost increase $70/month)
3. **Cloud Tasks queue depth >100 tasks for >10 minutes**
   - Symptom: Discovery enqueues faster than processing consumes
   - Action: Increase `max_dispatches_per_second = 1.0` and `max_concurrent_dispatches = 5`
4. **Cloud Run max_instances hit (instance count = 10 for >5 minutes)**
   - Symptom: Requests queuing, increased latency
   - Action: Increase `max_instances = 20` (costs scale linearly with traffic, acceptable)

### Expanded Scraping + Analysis Impact

- **Current daily pipeline**: 50 new tournaments discovered, 50 processed (100 seconds total via Cloud Tasks)
- **With Limitless sprite extraction**: Processing time increases from 30s → 45s per tournament (50% increase)
  - Cloud Tasks queue depth increases, but still well below capacity
- **With three analysis levels**: `compute-meta` (8 AM) and `compute-evolution` (9 AM) are independent
  - No impact on scraping throughput
  - Evolution pipeline is I/O bound (Claude API calls), not CPU bound
  - Cloud Run autoscaling handles this naturally

### Scaling Recommendation: No Changes Needed for Expanded Scope

The current infrastructure scales gracefully for the planned pipeline overhaul. Cloud Tasks rate limiting (0.5 tasks/sec) is the intentional throttle to prevent Limitless rate limiting, not an infrastructure bottleneck.

## Risks If Ignored

- **Silent data quality failures**: Without structured logging for sprite extraction and card mapping, we won't detect Cinderace-class issues until users report them weeks later. The reprocessing effort is wasted if we can't validate correctness.
- **Cost overruns from retry storms**: If the reprocessing fails midway (e.g., Cloud SQL connection exhaustion), Cloud Tasks will retry failed tasks exponentially. Without a `reprocessing_batch` table to track progress, we risk double-processing and wasting Cloud Run compute costs.
- **Production downtime from timeout misconfigurations**: Relying on GCP's default 300s timeout is operational debt. If a future pipeline exceeds 5 minutes (e.g., AI-powered meta analysis), it will fail silently with HTTP 504. Explicit Terraform configuration makes timeouts a first-class infrastructure concern.

## Dependencies on Other Agents' Domains

### Architect

- **Database schema**: Need `reprocessing_batch` table design for bulk operation progress tracking
- **Sprite storage strategy**: Where do we store extracted sprite URLs? Add `deck_sprites` table or embed in JSON column?
- **Card mapping confidence scores**: Should `card_mappings` table include a `confidence` float field for monitoring?

### Craftsman

- **Structured logging service**: Implement `StructuredLogger` wrapper with pipeline-specific fields
- **Reprocess endpoint**: Implement `/api/v1/pipeline/reprocess-bulk` with progress API
- **Sprite extraction monitoring**: Add `log_sprite_extraction_result(tournament_id, sprite_count)` calls in scraping service

### Scientist

- **Data quality metrics**: Define thresholds for sprite extraction rate (>90%), card mapping coverage (>95%)
- **Archetype drift detection**: What is the statistical threshold for "unlikely meta shift" (likely data issue)?
- **Validation queries**: SQL queries to compare before/after archetype shares, detect anomalies

### Investigator

- **Limitless rate limiting**: Confirm scraping rate limits (currently assuming 0.5 req/sec is safe)
- **Sprite URL format**: Document Limitless sprite URL patterns for extraction validation
- **Historical data volume**: Confirm estimate of 3000-5000 tournaments for cost/time projections
