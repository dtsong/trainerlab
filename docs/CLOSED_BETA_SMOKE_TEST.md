# Closed Beta Production Smoke Test

Purpose: quick, repeatable checks after deploying to production (or before inviting a batch of users).

This is intentionally small. If you need full launch readiness, use `docs/LAUNCH_OPS_CHECKLIST.md`.

## 0) Preconditions

- [ ] You can sign in with an admin account.
- [ ] Production env vars/secrets are set:
  - [ ] API Cloud Run: `ADMIN_EMAILS` includes your admin email
  - [ ] API Cloud Run: `NEXTAUTH_SECRET` matches Vercel `NEXTAUTH_SECRET`
  - [ ] API Cloud Run: `READINESS_ALERT_TOKEN` set (if using readiness alerts)

## 1) Public Web

- [ ] Home loads: `https://www.trainerlab.io/`
- [ ] Lab notes load (public): `https://www.trainerlab.io/lab-notes`
- [ ] Closed beta request page loads: `https://www.trainerlab.io/closed-beta`
- [ ] Investigate hub loads (public): `https://www.trainerlab.io/investigate`
- [ ] Submit request form (email + optional note)
  - [ ] Returns success message
  - [ ] Submitting the same email again still returns success (privacy-safe)

Tip: you can automate the non-auth checks with `./scripts/cloud/smoke-web-prod.sh`.

## 2) Auth + Access Gate

- [ ] Sign in via Google: `https://www.trainerlab.io/auth/login`
- [ ] As a non-invited account, visit a gated route (example): `https://www.trainerlab.io/meta`
  - [ ] Closed beta gate appears
  - [ ] "Refresh Access" does not break the page
  - [ ] "Request Access" links to `/closed-beta`

## 3) Admin: Grants + Audit

- [ ] Admin access page loads: `https://www.trainerlab.io/admin/access`
- [ ] Create a pre-login invite (beta): grant access by email
  - [ ] Pending invite appears in the list
- [ ] Revoke an invite (beta): revoke access by email
  - [ ] Pending invite updates accordingly
- [ ] Audit log page loads: `https://www.trainerlab.io/admin/audit`
  - [ ] Grant/revoke actions show up as audit events

## 4) Invited User End-to-End

- [ ] Grant beta access to a fresh email that has never logged in
- [ ] Sign in as that email
- [ ] Visit a gated route (example): `/meta`
  - [ ] Access is granted (no gate)
- [ ] Revoke beta access for that email
- [ ] Refresh and revisit a gated route
  - [ ] Access is removed (gate appears)

## 5) API Health + Ops

- [ ] API health:
  - [ ] `https://api.trainerlab.io/api/v1/health`
  - [ ] `https://api.trainerlab.io/api/v1/health/pipeline`
- [ ] Meta endpoint works for an invited user (example): `GET /api/v1/meta/snapshots?limit=1`

## 6) Readiness Alerts (Optional)

- [ ] GitHub Actions workflow exists: `.github/workflows/tpci-readiness-alert.yml`
- [ ] Repo secrets configured:
  - [ ] `READINESS_ALERT_TOKEN` (must match Cloud Run secret)
  - [ ] `DISCORD_WEBHOOK_URL` (if using Discord)
  - [ ] `PRODUCTION_API_URL` variable or secret (defaults to `https://api.trainerlab.io`)
- [ ] Labels exist in repo (for issue creation): `ops`, `alerts`

Notes:

- If `READINESS_ALERT_TOKEN` is not configured, the workflow now exits as `skipped` with a warning instead of failing.
- Configure `READINESS_ALERT_TOKEN` to actively query `/api/v1/ops/readiness/tpci` and raise alerts.

## 7) If Something Fails

- [ ] Check Cloud Run logs for `trainerlab-api`
- [ ] Check Vercel function logs for the web app
- [ ] Re-run the smallest possible check that reproduces the failure
- [ ] Roll back (see `docs/DEPLOYMENT.md`)
