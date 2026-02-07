#!/usr/bin/env bash
set -euo pipefail

# ── Snapshot Prod → Local ────────────────────────────────────────────
# Export pipeline-relevant tables from prod via Cloud SQL Proxy,
# then optionally import into local Docker Postgres.
#
# Usage:
#   ./tl prod snapshot           # Export to /tmp/trainerlab-snapshot/
#   ./tl prod snapshot --restore # Import snapshot into local Docker DB

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"
SNAPSHOT_DIR="/tmp/trainerlab-snapshot"

# Colors
if [ -t 1 ]; then
    BOLD='\033[1m' DIM='\033[2m' CYAN='\033[36m'
    GREEN='\033[32m' YELLOW='\033[33m' RED='\033[31m' RESET='\033[0m'
else
    BOLD='' DIM='' CYAN='' GREEN='' YELLOW='' RED='' RESET=''
fi

info()    { printf "${CYAN}▸${RESET} %s\n" "$1"; }
success() { printf "${GREEN}✓${RESET} %s\n" "$1"; }
error()   { printf "${RED}✗${RESET} %s\n" "$1" >&2; }

# Prod connection settings (via Cloud SQL Proxy)
PROD_PROJECT="${PROD_PROJECT:-trainerlab-prod}"
PROD_REGION="${PROD_REGION:-us-west1}"
PROD_INSTANCE="${PROD_INSTANCE:-trainerlab-db}"
PROD_DB_USER="${PROD_DB_USER:-trainerlab_dev}"
PROD_OPS_SA="${PROD_OPS_SA:-trainerlab-ops@trainerlab-prod.iam.gserviceaccount.com}"
PROXY_PORT=15433

# Pipeline-relevant tables (excludes PII: users, api_keys, api_requests, data_exports)
TABLES=(
    tournaments
    tournament_placements
    meta_snapshots
    cards
    sets
    archetype_sprites
    card_id_mappings
    format_configs
)

do_export() {
    mkdir -p "$SNAPSHOT_DIR"
    info "Starting Cloud SQL Proxy on port ${PROXY_PORT}..."

    cloud-sql-proxy "${PROD_PROJECT}:${PROD_REGION}:${PROD_INSTANCE}" \
        --port "${PROXY_PORT}" \
        --impersonate-service-account="${PROD_OPS_SA}" &
    local proxy_pid=$!
    sleep 3

    cleanup() { kill "$proxy_pid" 2>/dev/null || true; }
    trap cleanup EXIT

    info "Exporting ${#TABLES[@]} tables to ${SNAPSHOT_DIR}..."

    for table in "${TABLES[@]}"; do
        info "Dumping ${table}..."
        pg_dump "postgresql://${PROD_DB_USER}@localhost:${PROXY_PORT}/trainerlab" \
            --table="public.${table}" \
            --data-only \
            --no-owner \
            --no-privileges \
            --format=custom \
            -f "${SNAPSHOT_DIR}/${table}.dump" 2>/dev/null || {
                error "Failed to dump ${table} (table may not exist)"
                continue
            }
        success "Exported ${table}"
    done

    kill "$proxy_pid" 2>/dev/null || true
    trap - EXIT

    success "Snapshot complete: ${SNAPSHOT_DIR}/"
    printf "  ${DIM}Run './tl prod snapshot --restore' to import into local DB${RESET}\n"
}

do_restore() {
    if [ ! -d "$SNAPSHOT_DIR" ]; then
        error "No snapshot found at ${SNAPSHOT_DIR}/"
        printf "  Run './tl prod snapshot' first to export prod data\n"
        exit 1
    fi

    info "Restoring snapshot to local Docker Postgres..."

    # Check Docker Postgres is running
    if ! docker compose -f "$ROOT_DIR/docker-compose.yml" exec -T db pg_isready -U postgres >/dev/null 2>&1; then
        error "Local Postgres not running. Start with: ./tl start"
        exit 1
    fi

    for table in "${TABLES[@]}"; do
        local dump_file="${SNAPSHOT_DIR}/${table}.dump"
        if [ ! -f "$dump_file" ]; then
            printf "  ${YELLOW}○${RESET} Skipping ${table} (no dump file)\n"
            continue
        fi

        info "Restoring ${table}..."
        # Truncate first, then restore
        docker compose -f "$ROOT_DIR/docker-compose.yml" exec -T db \
            psql -U postgres -d trainerlab -c "TRUNCATE TABLE public.${table} CASCADE;" 2>/dev/null || true

        docker compose -f "$ROOT_DIR/docker-compose.yml" exec -T db \
            pg_restore -U postgres -d trainerlab \
            --data-only \
            --no-owner \
            --no-privileges \
            --disable-triggers < "$dump_file" 2>/dev/null || {
                error "Failed to restore ${table}"
                continue
            }
        success "Restored ${table}"
    done

    success "Snapshot restore complete"
}

# Parse args
case "${1:-}" in
    --restore)
        do_restore
        ;;
    --help|-h)
        printf "${BOLD}snapshot-prod.sh${RESET} — Export/import prod data\n\n"
        printf "  ${GREEN}snapshot-prod.sh${RESET}           Export prod tables via Cloud SQL Proxy\n"
        printf "  ${GREEN}snapshot-prod.sh --restore${RESET} Import snapshot into local Docker DB\n"
        printf "\n  Tables: ${TABLES[*]}\n"
        printf "  ${DIM}Excludes PII tables: users, api_keys, api_requests, data_exports${RESET}\n"
        ;;
    *)
        do_export
        ;;
esac
