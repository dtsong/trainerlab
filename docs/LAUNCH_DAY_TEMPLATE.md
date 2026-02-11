# Launch Day Log Template

> Use this document live during launch. Duplicate it as `docs/launch-logs/LAUNCH-YYYY-MM-DD.md` for each launch event.

---

## Launch Metadata

- Date:
- Launch window start (timezone):
- Launch window end (timezone):
- Environment: `production`
- Launch commander:
- Web on-call:
- API on-call:
- Communications owner:
- Support triage owner:

---

## Release Context

- Target commit SHA:
- Previous stable SHA:
- Primary changes in this launch:
  1.
  2.
  3.
- Linked PR(s):
- Linked issue(s):

---

## Pre-Launch Checklist (T-24h to T-1h)

- [ ] CI green on target SHA
- [ ] Deploy workflows healthy
- [ ] `GET /api/v1/health` returns healthy
- [ ] `GET /api/v1/health/pipeline` returns healthy
- [ ] Web smoke checks pass (`/`, `/meta`, `/cards`, `/decks`, `/creator`)
- [ ] OG routes return `200`
- [ ] Rollback plan confirmed

Notes:

---

## Go/No-Go Decision

- Decision time:
- Decision: `GO` / `NO-GO`
- Decision owner:
- Rationale:
- Risks accepted:

---

## Timeline (Live Log)

| Time (TZ) | Event | Owner | Status | Notes |
| --------- | ----- | ----- | ------ | ----- |
|           |       |       |        |       |
|           |       |       |        |       |
|           |       |       |        |       |

---

## Metric Snapshots

### Baseline (Before Launch)

- API error rate:
- API p95 latency:
- Web client error rate:
- Pipeline health:
- Active users / requests per minute:

### +15m

- API error rate:
- API p95 latency:
- Web client error rate:
- Pipeline health:
- Active users / requests per minute:

### +60m

- API error rate:
- API p95 latency:
- Web client error rate:
- Pipeline health:
- Active users / requests per minute:

### +4h

- API error rate:
- API p95 latency:
- Web client error rate:
- Pipeline health:
- Active users / requests per minute:

---

## Incident Log

| Start Time | Severity | Symptom | Scope | Mitigation | Owner | End Time | Follow-up Issue |
| ---------- | -------- | ------- | ----- | ---------- | ----- | -------- | --------------- |
|            |          |         |       |            |       |          |                 |
|            |          |         |       |            |       |          |                 |

---

## Communications Log

| Time (TZ) | Channel | Message Summary | Posted By | Link |
| --------- | ------- | --------------- | --------- | ---- |
|           |         |                 |           |      |
|           |         |                 |           |      |

---

## User Feedback Triage

| Time | Source | Feedback | Impact | Action | Owner | Ticket |
| ---- | ------ | -------- | ------ | ------ | ----- | ------ |
|      |        |          |        |        |       |        |
|      |        |          |        |        |       |        |

---

## Rollback Section (Fill only if used)

- Rollback triggered: `Yes` / `No`
- Trigger time:
- Trigger reason:
- Rolled back to SHA:
- Services rolled back:
  - [ ] Web
  - [ ] API
  - [ ] Other:
- Verification checks after rollback:
  - [ ] Health endpoints good
  - [ ] Core routes good
  - [ ] Error rate recovered

---

## End-of-Day Summary

- Launch result: `Successful` / `Partially successful` / `Rolled back`
- Top wins:
  1.
  2.
  3.
- Top issues:
  1.
  2.
  3.
- Immediate next actions (24h):
  1.
  2.
  3.
- Planned post-launch review date:

---

## Post-Launch Action Items

| Priority | Action | Owner | Due Date | Ticket |
| -------- | ------ | ----- | -------- | ------ |
| P0       |        |       |          |        |
| P1       |        |       |          |        |
| P2       |        |       |          |        |
