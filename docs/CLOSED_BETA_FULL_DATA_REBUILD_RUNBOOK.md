# Closed Beta Full Data Rebuild Runbook

Purpose: execute a full non-user data reset for production closed beta when data behavior appears inconsistent.

Scope: wipe and rebuild pipeline data while preserving user-facing tables.

Preserved by `wipe-data`: `users`, `decks`, `waitlist`, `api_keys`, `api_requests`, `lab_notes`, `lab_note_revisions`, `widgets`, `widget_views`, `data_exports`.

---

## 0) Preconditions

- [ ] You have `gcloud` auth for `trainerlab-prod` and Cloud Run invoker rights.
- [ ] You can run `./tl prod health` successfully.
- [ ] You have a rollback path documented in `docs/LAUNCH_OPS_CHECKLIST.md`.
- [ ] You have posted a maintenance note in launch ops channels/issues (`#357`, `#360`).

---

## 1) Freeze schedulers and capture baseline

Set envs for this session:

```bash
export PROD_PROJECT="trainerlab-prod"
export PROD_REGION="us-west1"
export PROD_SERVICE="trainerlab-api"
```

Pause scheduler jobs to prevent concurrent writes during rebuild:

```bash
for JOB in \
  trainerlab-sync-cards \
  trainerlab-sync-jp-cards \
  trainerlab-sync-card-mappings \
  trainerlab-sync-events \
  trainerlab-discover-en \
  trainerlab-discover-jp \
  trainerlab-compute-meta \
  trainerlab-compute-evolution \
  trainerlab-translate-pokecabook \
  trainerlab-sync-jp-adoption \
  trainerlab-translate-tier-lists \
  trainerlab-monitor-card-reveals \
  trainerlab-cleanup-exports
do
  gcloud scheduler jobs pause "$JOB" --location="$PROD_REGION" --project="$PROD_PROJECT" || true
done
```

Capture pre-rebuild evidence:

```bash
./tl prod health
./tl verify data --group=tournaments
./tl verify data --group=meta
./tl verify data --group=archetype
./scripts/cloud/smoke-web-prod.sh
```

Optional safety export before wipe:

```bash
./tl prod snapshot
```

---

## 2) Build authenticated pipeline helper

Run once in your shell:

```bash
SERVICE_URL=$(gcloud run services describe "$PROD_SERVICE" \
  --project="$PROD_PROJECT" \
  --region="$PROD_REGION" \
  --format='yaml(spec.template.spec.containers[0].env)' \
  | grep -A1 'name: CLOUD_RUN_URL' | grep 'value:' | sed 's/.*value: //')

if [ -z "$SERVICE_URL" ]; then
  SERVICE_URL=$(gcloud run services describe "$PROD_SERVICE" \
    --project="$PROD_PROJECT" \
    --region="$PROD_REGION" \
    --format='value(status.url)')
fi

export SERVICE_URL
export PROD_OPS_SA="trainerlab-ops@trainerlab-prod.iam.gserviceaccount.com"
export AUTH_TOKEN=$(gcloud auth print-identity-token \
  --impersonate-service-account="$PROD_OPS_SA" \
  --include-email \
  --audiences="$SERVICE_URL")

post_pipeline() {
  local endpoint="$1"
  local payload="$2"
  curl -sS -X POST \
    "${SERVICE_URL}/api/v1/pipeline/${endpoint}" \
    -H "Authorization: Bearer ${AUTH_TOKEN}" \
    -H "Content-Type: application/json" \
    -d "${payload}"
}
```

Quick auth check:

```bash
curl -sS "${SERVICE_URL}/api/v1/health/pipeline" | jq '.status'
```

---

## 3) Execute full wipe + rebuild

### 3A) Wipe and reseed

- [ ] Dry-run wipe:

```bash
post_pipeline "wipe-data" '{"dry_run": true}' | jq .
```

- [ ] Execute wipe:

```bash
post_pipeline "wipe-data" '{"dry_run": false}' | jq .
```

- [ ] Reseed reference data:

```bash
post_pipeline "seed-data" '{"dry_run": false}' | jq .
```

### 3B) Rebuild base datasets

- [ ] Sync cards:

```bash
post_pipeline "sync-cards" '{"dry_run": false}' | jq .
```

- [ ] Sync JP-EN card mappings (full pass):

```bash
post_pipeline "sync-card-mappings" '{"dry_run": false, "recent_only": false, "lookback_sets": 20}' | jq .
```

- [ ] Sync events:

```bash
post_pipeline "sync-events" '{"dry_run": false}' | jq .
```

### 3C) Rebuild tournaments

- [ ] Discover EN tournaments:

```bash
post_pipeline "discover-en" '{"dry_run": false, "lookback_days": 120, "game_format": "standard"}' | jq .
```

- [ ] Discover JP tournaments:

```bash
post_pipeline "discover-jp" '{"dry_run": false, "lookback_days": 120}' | jq .
```

- [ ] Wait for Cloud Tasks to drain before compute steps.

Check process-tournament activity:

```bash
gcloud logging read \
  "resource.type=cloud_run_revision AND resource.labels.service_name=${PROD_SERVICE} AND httpRequest.requestUrl:\"/api/v1/pipeline/process-tournament\"" \
  --project="$PROD_PROJECT" \
  --limit=50 \
  --freshness=30m
```

### 3D) Recompute derived intelligence

- [ ] Compute meta snapshots:

```bash
post_pipeline "compute-meta" '{"dry_run": false, "lookback_days": 120}' | jq .
```

- [ ] Compute evolution/predictions/articles:

```bash
post_pipeline "compute-evolution" '{"dry_run": false}' | jq .
```

- [ ] Re-sync JP adoption rates:

```bash
post_pipeline "sync-jp-adoption" '{"dry_run": false}' | jq .
```

- [ ] Rebuild translation artifacts:

```bash
post_pipeline "translate-pokecabook" '{"dry_run": false, "lookback_days": 14}' | jq .
post_pipeline "translate-tier-lists" '{"dry_run": false}' | jq .
```

---

## 4) Conditional repair steps (only if verification fails)

If JP archetype quality is still degraded:

```bash
post_pipeline "rescrape-jp" '{"dry_run": false, "lookback_days": 120}' | jq .
```

If archetype method coverage still looks wrong, run JP reprocess loop:

```bash
CURSOR=""
while :; do
  if [ -z "$CURSOR" ]; then
    RESP=$(post_pipeline "reprocess-archetypes" '{"dry_run": false, "region": "JP", "batch_size": 500, "force": true}')
  else
    RESP=$(post_pipeline "reprocess-archetypes" "{\"dry_run\": false, \"region\": \"JP\", \"batch_size\": 500, \"force\": true, \"cursor\": \"${CURSOR}\"}")
  fi

  echo "$RESP" | jq .
  CURSOR=$(echo "$RESP" | jq -r '.next_cursor // ""')
  [ -z "$CURSOR" ] && break
done
```

---

## 5) Verification gate (must pass)

- [ ] Pipeline health:

```bash
./tl prod health
```

- [ ] Data quality:

```bash
./tl verify data --group=cards
./tl verify data --group=tournaments
./tl verify data --group=meta
./tl verify data --group=japan
./tl verify data --group=archetype
./tl verify data --group=frontend
```

- [ ] Closed-beta smoke script:

```bash
./scripts/cloud/smoke-web-prod.sh
```

- [ ] Manual auth/admin checks from `docs/CLOSED_BETA_SMOKE_TEST.md` completed and recorded.

---

## 6) Unfreeze schedulers

```bash
for JOB in \
  trainerlab-sync-cards \
  trainerlab-sync-jp-cards \
  trainerlab-sync-card-mappings \
  trainerlab-sync-events \
  trainerlab-discover-en \
  trainerlab-discover-jp \
  trainerlab-compute-meta \
  trainerlab-compute-evolution \
  trainerlab-translate-pokecabook \
  trainerlab-sync-jp-adoption \
  trainerlab-translate-tier-lists \
  trainerlab-monitor-card-reveals \
  trainerlab-cleanup-exports
do
  gcloud scheduler jobs resume "$JOB" --location="$PROD_REGION" --project="$PROD_PROJECT" || true
done
```

---

## 7) Evidence and closure

- [ ] Post command outputs and timestamps to `#357` and `#360`.
- [ ] Note any deferred failures with rationale.
- [ ] Close `#357` if all smoke checks pass.
- [ ] Close `#360` once execution-plan checklist is fully complete.
