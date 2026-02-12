#!/usr/bin/env bash
set -euo pipefail

# Checks TPCI post-major readiness signal from production API.
#
# Requires:
# - gcloud auth login
# - Admin JWT (Auth.js HS256 token) passed via AUTH_TOKEN

REGION="${REGION:-us-west1}"
SERVICE_NAME="${SERVICE_NAME:-trainerlab-api}"
PROJECT_ID="${PROJECT_ID:-trainerlab-prod}"
AUTH_TOKEN="${AUTH_TOKEN:-}"

if [ -z "$AUTH_TOKEN" ]; then
  echo "AUTH_TOKEN is required" >&2
  exit 1
fi

SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" \
  --project="$PROJECT_ID" \
  --region="$REGION" \
  --format='value(status.url)')

curl -sS \
  -H "Authorization: Bearer ${AUTH_TOKEN}" \
  "${SERVICE_URL}/api/v1/admin/readiness/tpci" |
  python3 -c "import sys,json; d=json.load(sys.stdin); print(json.dumps(d, indent=2))"
