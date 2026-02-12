# TrainerLab Launch Ops Checklist

> Purpose: day-of-launch operational runbook for TrainerLab.

---

## 1) Pre-Launch (T-24h to T-1h)

- [ ] Confirm `main` is green in GitHub Actions (`CI`, deploy workflows, health checks)
- [ ] Confirm production endpoints return healthy responses:
  - [ ] `https://api.trainerlab.io/api/v1/health`
  - [ ] `https://api.trainerlab.io/api/v1/health/pipeline`
  - [ ] `https://www.trainerlab.io`
- [ ] Verify key user journeys manually:
  - [ ] `/meta`, `/meta/official`, `/meta/grassroots`
  - [ ] `/meta/japan`, `/meta/japan/official`, `/meta/japan/grassroots`
  - [ ] `/cards`, `/decks`, `/creator` (auth-gated)
- [ ] Verify OG image routes:
  - [ ] `/api/og/meta.png`
  - [ ] `/api/og/lab-notes/{slug}.png`
  - [ ] `/api/og/evolution/{slug}.png`
  - [ ] `/api/og/archetypes/{id}.png`
  - [ ] `/api/og/w_{id}.png`
- [ ] Confirm Cloud Run latest revisions are healthy (web/api/tcgdex)
- [ ] Confirm Cloud SQL storage headroom and connection metrics are normal
- [ ] Confirm Redis (Memorystore) availability and error rate baseline
- [ ] Verify env vars and secrets are present in prod (no placeholder values)
- [ ] Validate rollback target (last known good commit SHA): `7072884`

---

## 2) Launch Window (T-0)

- [ ] Announce launch in selected channels (Discord, Reddit, X, newsletter)
- [ ] Pin status/FAQ link for known launch limitations
- [ ] Start active monitoring window (first 2-4 hours)
- [ ] Monitor error signals every 10-15 minutes:
  - [ ] API 5xx rate
  - [ ] API p95 latency
  - [ ] Web error logs / client exceptions
  - [ ] Pipeline health job status
- [ ] Validate first real user flows:
  - [ ] Sign-in works
  - [ ] Deck save/load works
  - [ ] Creator dashboard renders for creator account
  - [ ] Widget embed renders on `/embed/{id}`

---

## 3) Incident Response (If Needed)

### Severity Guide

- `SEV-1`: Site/API unavailable, auth broken, data corruption risk
- `SEV-2`: Core workflows degraded for many users
- `SEV-3`: Non-critical regressions, cosmetic issues

### Immediate Actions

- [ ] Assign incident lead
- [ ] Open incident channel/thread with timestamp and owner
- [ ] Capture failing endpoint, error signature, and scope
- [ ] Decide mitigation path:
  - [ ] Feature flag / route disable
  - [ ] Roll forward hotfix
  - [ ] Roll back to last known good SHA
- [ ] Post user-facing status update (if SEV-1/SEV-2)
- [ ] Confirm recovery and monitor for 30 minutes after mitigation

---

## 4) Rollback Plan

- [ ] Identify target SHA: `________________`
- [ ] Deploy previous web revision (Vercel rollback)
- [ ] Deploy previous API revision (Cloud Run rollback)
- [ ] Re-run smoke checks (`/`, `/meta`, `/cards`, `/decks`, `/api/v1/health`)
- [ ] Announce rollback completion and next ETA

---

## 5) First 24 Hours After Launch

- [ ] Gather top support issues and cluster by root cause
- [ ] Triage and label launch bugs (`sev-1`, `sev-2`, `sev-3`)
- [ ] Review performance and cost deltas vs baseline
- [ ] Check creator feature adoption:
  - [ ] widgets created
  - [ ] exports created
  - [ ] API keys created
- [ ] Check meta feature adoption:
  - [ ] visits to official/grassroots track pages
  - [ ] JP page engagement
- [ ] Publish internal launch day recap

---

## 6) First 7 Days

- [ ] Daily check of reliability metrics (errors, latency, deploy success)
- [ ] Daily backlog grooming for launch feedback
- [ ] Prioritize top 3 quality-of-life improvements
- [ ] Draft "Week 1 Launch Results" report

---

## 7) Ownership

- Launch commander: `dtsong`
- Web on-call: `dtsong`
- API on-call: `dtsong`
- Communications owner: `dtsong`
- Support triage owner: `dtsong`

---

## 8) Useful Commands

```bash
# CI / workflow status
gh run list --limit 20

# Trigger health check
gh workflow run pipeline-health.yml

# Check open issues
gh issue list --state open --limit 100

# Quick smoke checks
curl -s https://api.trainerlab.io/api/v1/health
curl -s https://api.trainerlab.io/api/v1/health/pipeline
curl -s -o /dev/null -w "%{http_code}\n" https://www.trainerlab.io/meta/official
```
