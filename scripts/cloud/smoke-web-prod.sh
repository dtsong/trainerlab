#!/usr/bin/env bash
set -euo pipefail

# Smoke test for the production web + API endpoints.
#
# Safe by default: only performs GET/HEAD checks.
# To test the closed-beta waitlist form (writes production data), you must pass
# --confirm-waitlist and provide --email.

WEB_URL="https://www.trainerlab.io"
API_URL="https://api.trainerlab.io"

CONFIRM_WAITLIST="false"
WAITLIST_EMAIL=""
WAITLIST_NOTE=""

usage() {
  cat <<'EOF'
Usage:
  ./scripts/cloud/smoke-web-prod.sh [options]

Options:
  --web-url=URL           Web base URL (default: https://www.trainerlab.io)
  --api-url=URL           API base URL (default: https://api.trainerlab.io)
  --confirm-waitlist      Enable waitlist POST test (WRITES production data)
  --email=EMAIL           Email used for waitlist POST test (required with --confirm-waitlist)
  --note=TEXT             Optional note for waitlist POST test
  -h, --help              Show this help

Examples:
  ./scripts/cloud/smoke-web-prod.sh

  # Write test (creates/updates waitlist entry in prod)
  ./scripts/cloud/smoke-web-prod.sh --confirm-waitlist --email="smoke+$(date +%s)@example.com" --note="cli smoke test"
EOF
}

for arg in "$@"; do
  case "$arg" in
    --web-url=*) WEB_URL="${arg#*=}" ;;
    --api-url=*) API_URL="${arg#*=}" ;;
    --confirm-waitlist) CONFIRM_WAITLIST="true" ;;
    --email=*) WAITLIST_EMAIL="${arg#*=}" ;;
    --note=*) WAITLIST_NOTE="${arg#*=}" ;;
    -h|--help) usage; exit 0 ;;
    *)
      echo "Unknown argument: $arg" >&2
      usage
      exit 2
      ;;
  esac
done

status_code() {
  # shellcheck disable=SC2312
  curl -sS -o /dev/null -w "%{http_code}" "$1"
}

header_location() {
  curl -sS -I "$1" | tr -d '\r' | awk -F': ' 'tolower($1)=="location" {print $2; exit}'
}

json_get() {
  curl -sS "$1"
}

echo "Smoke test: web=${WEB_URL} api=${API_URL}"

echo "[web] / => $(status_code "${WEB_URL}/")"
echo "[web] /lab-notes => $(status_code "${WEB_URL}/lab-notes")"
echo "[web] /closed-beta => $(status_code "${WEB_URL}/closed-beta")"
echo "[web] /investigate => $(status_code "${WEB_URL}/investigate")"

META_CODE="$(status_code "${WEB_URL}/meta")"
META_LOC="$(header_location "${WEB_URL}/meta" || true)"
echo "[web] /meta (logged out) => ${META_CODE} location=${META_LOC:-<none>}"

echo "[api] /api/v1/health => $(json_get "${API_URL}/api/v1/health")"
echo "[api] /api/v1/health/pipeline => $(json_get "${API_URL}/api/v1/health/pipeline")"

if [[ "$CONFIRM_WAITLIST" == "true" ]]; then
  if [[ -z "$WAITLIST_EMAIL" ]]; then
    echo "--email is required with --confirm-waitlist" >&2
    exit 2
  fi

  echo "[web] POST /api/waitlist (WRITES prod): email=${WAITLIST_EMAIL}"

  WAITLIST_BODY="{\"email\":\"${WAITLIST_EMAIL}\",\"note\":\"${WAITLIST_NOTE}\",\"intent\":\"both\",\"source\":\"smoke_web_prod_script\"}"

  POST_CODE_1="$(
    curl -sS -o /dev/null -w "%{http_code}" \
      -X POST "${WEB_URL}/api/waitlist" \
      -H "Content-Type: application/json" \
      --data "$WAITLIST_BODY"
  )"
  echo "[web] POST /api/waitlist => ${POST_CODE_1}"

  POST_CODE_2="$(
    curl -sS -o /dev/null -w "%{http_code}" \
      -X POST "${WEB_URL}/api/waitlist" \
      -H "Content-Type: application/json" \
      --data "$WAITLIST_BODY"
  )"
  echo "[web] POST /api/waitlist (repeat) => ${POST_CODE_2}"
fi

echo "Done."
