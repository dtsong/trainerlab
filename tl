#!/usr/bin/env bash
set -euo pipefail

# ── TrainerLab Developer CLI ────────────────────────────────────────
# Unified entry point for all developer scripts.
# Run ./tl --help for usage.

# ── Paths ───────────────────────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPTS_DIR="$SCRIPT_DIR/scripts"
API_DIR="$SCRIPT_DIR/apps/api"

# ── Colors ──────────────────────────────────────────────────────────

if [ -t 1 ]; then
    BOLD='\033[1m'
    DIM='\033[2m'
    CYAN='\033[36m'
    GREEN='\033[32m'
    YELLOW='\033[33m'
    RED='\033[31m'
    RESET='\033[0m'
else
    BOLD='' DIM='' CYAN='' GREEN='' YELLOW='' RED='' RESET=''
fi

# ── Utilities ───────────────────────────────────────────────────────

tl_info()    { printf "${CYAN}▸${RESET} %s\n" "$1"; }
tl_success() { printf "${GREEN}✓${RESET} %s\n" "$1"; }
tl_error()   { printf "${RED}✗${RESET} %s\n" "$1" >&2; }

require_deps() {
    local missing=""
    for dep in "$@"; do
        if ! command -v "$dep" >/dev/null 2>&1; then
            missing="$missing $dep"
        fi
    done
    if [ -n "$missing" ]; then
        tl_error "Missing dependencies:${missing}"
        printf "  Install with your package manager (e.g. brew install%s)\n" "$missing" >&2
        exit 1
    fi
}

# ── Help ────────────────────────────────────────────────────────────

fmt_cmd() {
    # fmt_cmd "command" "description"
    printf "  ${GREEN}%-24s${RESET} %s\n" "$1" "$2"
}

show_help() {
    printf "${BOLD}TrainerLab Developer CLI${RESET}\n"
    printf "\n"
    printf "${DIM}Usage:${RESET}  ./tl <command> [subcommand] [args...]\n"
    printf "\n"

    printf "${BOLD}${CYAN}WORKFLOW${RESET} — Composite runners\n"
    fmt_cmd "dev"              "Start full local stack (Docker + API + web)"
    fmt_cmd "setup"            "First-time setup (deps, Docker, migrations, seed)"
    fmt_cmd "nuke"             "Teardown all local resources for clean reinstall"
    fmt_cmd "check"            "Run all verification scripts"
    fmt_cmd "test-all"         "Run all test scripts"
    printf "\n"

    printf "${BOLD}${YELLOW}VERIFY${RESET} — Data quality & endpoint verification\n"
    fmt_cmd "verify local"     "Verify local Docker environment"
    fmt_cmd "verify data"      "Verify production data quality"
    fmt_cmd "verify phase3"    "Deep validate Phase 3 features"
    fmt_cmd "verify pipelines" "Verify Cloud Scheduler pipelines"
    printf "\n"

    printf "${BOLD}${YELLOW}TEST${RESET} — Subsystem testing\n"
    fmt_cmd "test jp-scrape"   "Test JP tournament scraping"
    fmt_cmd "test production"  "Test production scrapers"
    fmt_cmd "test jp-pipeline" "Validate JP archetype pipeline"
    fmt_cmd "test shadow"      "Shadow compare archetype labels"
    printf "\n"

    printf "${BOLD}${YELLOW}DATA${RESET} — Database & data management\n"
    fmt_cmd "db [args]"        "Local database access (psql)"
    fmt_cmd "seed formats"     "Seed format configuration data"
    fmt_cmd "seed tournaments" "Seed tournament fixture data"
    fmt_cmd "export [args]"    "Export local data for analysis"
    printf "\n"

    printf "${BOLD}${YELLOW}SYNC${RESET} — External data synchronization\n"
    fmt_cmd "sync cards"       "Sync card data from TCGdex"
    fmt_cmd "sync mappings"    "Sync JP↔EN card ID mappings"
    fmt_cmd "ingest jp"        "Deep ingest JP City League data"
    printf "\n"

    printf "${DIM}Pass --help to any command for its own usage info.${RESET}\n"
}

show_verify_help() {
    printf "${BOLD}VERIFY${RESET} — Data quality & endpoint verification\n\n"
    fmt_cmd "verify local"     "verify-local.sh          [curl, jq, docker]"
    fmt_cmd "verify data"      "verify-data.sh           [gcloud, jq, curl]"
    fmt_cmd "verify phase3"    "verify-phase3.sh         [curl, jq]"
    fmt_cmd "verify pipelines" "verify-pipelines.sh      [gcloud, jq]"
    printf "\n${DIM}Example: ./tl verify local --group=cards${RESET}\n"
}

show_test_help() {
    printf "${BOLD}TEST${RESET} — Subsystem testing\n\n"
    fmt_cmd "test jp-scrape"   "test-jp-scrape.sh              [curl, jq, docker]"
    fmt_cmd "test production"  "test-production-scrapers.sh    [gcloud, jq]"
    fmt_cmd "test jp-pipeline" "validate_jp_pipeline.py        [uv, python3]"
    fmt_cmd "test shadow"      "shadow_compare.py              [uv, python3]"
    printf "\n${DIM}Example: ./tl test jp-pipeline --verbose${RESET}\n"
}

show_seed_help() {
    printf "${BOLD}SEED${RESET} — Seed data from fixtures\n\n"
    fmt_cmd "seed formats"     "seed-formats.py          [uv, python3]"
    fmt_cmd "seed tournaments" "seed-tournaments.py      [uv, python3]"
    printf "\n${DIM}Example: ./tl seed formats --dry-run${RESET}\n"
}

show_sync_help() {
    printf "${BOLD}SYNC${RESET} — External data synchronization\n\n"
    fmt_cmd "sync cards"    "sync-cards.py            [uv, python3]"
    fmt_cmd "sync mappings" "sync-card-mappings.py    [uv, python3]"
    printf "\n${DIM}Example: ./tl sync cards --dry-run${RESET}\n"
}

# ── Composite: dev ──────────────────────────────────────────────────

run_dev() {
    require_deps docker uv pnpm

    tl_info "Starting Docker services (db, redis, tcgdex)..."
    docker compose -f "$SCRIPT_DIR/docker-compose.yml" up -d db redis tcgdex

    tl_info "Waiting for database..."
    local retries=30
    while ! docker compose -f "$SCRIPT_DIR/docker-compose.yml" exec -T db pg_isready -U postgres >/dev/null 2>&1; do
        retries=$((retries - 1))
        if [ "$retries" -le 0 ]; then
            tl_error "Database failed to become ready"
            exit 1
        fi
        sleep 1
    done
    tl_success "Database ready"

    tl_info "Starting API server (uvicorn) and web dev server (next)..."
    printf "${DIM}Press Ctrl+C to stop all services${RESET}\n\n"

    # Track child PIDs for cleanup
    API_PID=""
    WEB_PID=""

    cleanup() {
        printf "\n"
        tl_info "Shutting down..."
        [ -n "$API_PID" ] && kill "$API_PID" 2>/dev/null
        [ -n "$WEB_PID" ] && kill "$WEB_PID" 2>/dev/null
        wait "$API_PID" 2>/dev/null
        wait "$WEB_PID" 2>/dev/null
        tl_info "Stopping Docker services..."
        docker compose -f "$SCRIPT_DIR/docker-compose.yml" stop db redis tcgdex
        tl_success "All services stopped"
    }
    trap cleanup INT TERM

    (cd "$API_DIR" && uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8080) &
    API_PID=$!

    (cd "$SCRIPT_DIR" && pnpm --filter @trainerlab/web dev) &
    WEB_PID=$!

    # Wait for both (Ctrl+C triggers cleanup via trap)
    wait "$API_PID" "$WEB_PID" 2>/dev/null || true
}

# ── Composite: setup ────────────────────────────────────────────────

run_setup() {
    require_deps docker uv pnpm

    tl_info "Installing Python dependencies..."
    (cd "$API_DIR" && uv sync)
    tl_success "Python dependencies installed"

    tl_info "Installing Node.js dependencies..."
    (cd "$SCRIPT_DIR" && pnpm install)
    tl_success "Node.js dependencies installed"

    tl_info "Starting Docker services..."
    docker compose -f "$SCRIPT_DIR/docker-compose.yml" up -d db redis tcgdex

    tl_info "Waiting for database..."
    local retries=30
    while ! docker compose -f "$SCRIPT_DIR/docker-compose.yml" exec -T db pg_isready -U postgres >/dev/null 2>&1; do
        retries=$((retries - 1))
        if [ "$retries" -le 0 ]; then
            tl_error "Database failed to become ready"
            exit 1
        fi
        sleep 1
    done
    tl_success "Database ready"

    tl_info "Running database migrations..."
    (cd "$API_DIR" && uv run alembic upgrade head)
    tl_success "Migrations complete"

    tl_info "Seeding format data..."
    (cd "$API_DIR" && uv run "scripts/seed-formats.py")
    tl_success "Formats seeded"

    tl_info "Seeding tournament data..."
    (cd "$API_DIR" && uv run "scripts/seed-tournaments.py")
    tl_success "Tournaments seeded"

    printf "\n"
    tl_success "Setup complete! Run ${GREEN}./tl dev${RESET} to start the dev stack."
}

# ── Composite: nuke ─────────────────────────────────────────────────

run_nuke() {
    local mode="${1:-}"

    show_nuke_help() {
        printf "${BOLD}NUKE${RESET} — Teardown local resources\n\n"
        fmt_cmd "nuke"         "Interactive teardown (prompts before each step)"
        fmt_cmd "nuke all"     "Remove everything without prompting"
        fmt_cmd "nuke docker"  "Remove Docker containers, volumes, and images"
        fmt_cmd "nuke deps"    "Remove installed dependencies (.venv, node_modules)"
        fmt_cmd "nuke cache"   "Remove build/lint caches (.next, __pycache__, etc.)"
        printf "\n${DIM}Run ./tl setup afterwards to reinstall everything.${RESET}\n"
    }

    confirm() {
        local prompt="$1"
        printf "${YELLOW}?${RESET} %s [y/N] " "$prompt"
        read -r answer
        case "$answer" in
            [yY]|[yY][eE][sS]) return 0 ;;
            *) return 1 ;;
        esac
    }

    nuke_docker() {
        tl_info "Stopping and removing Docker containers..."
        docker compose -f "$SCRIPT_DIR/docker-compose.yml" down --remove-orphans 2>/dev/null || true

        tl_info "Removing Docker volumes (postgres_data, redis_data)..."
        docker compose -f "$SCRIPT_DIR/docker-compose.yml" down -v 2>/dev/null || true

        tl_success "Docker resources removed"
    }

    nuke_deps() {
        tl_info "Removing Python virtual environment..."
        rm -rf "$API_DIR/.venv"

        tl_info "Removing node_modules..."
        rm -rf "$SCRIPT_DIR/node_modules"
        rm -rf "$SCRIPT_DIR/apps/web/node_modules"
        rm -rf "$SCRIPT_DIR/packages/shared-types/node_modules"

        tl_success "Dependencies removed"
    }

    nuke_cache() {
        tl_info "Removing build and cache artifacts..."
        rm -rf "$SCRIPT_DIR/apps/web/.next"
        rm -rf "$SCRIPT_DIR/apps/web/.turbo"
        rm -rf "$API_DIR/.ruff_cache"
        rm -rf "$API_DIR/.pytest_cache"
        find "$API_DIR" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
        find "$API_DIR" -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true

        tl_success "Caches removed"
    }

    case "$mode" in
        all)
            printf "${RED}${BOLD}This will remove ALL local resources:${RESET}\n"
            printf "  - Docker containers, volumes, and images\n"
            printf "  - Python .venv and all node_modules\n"
            printf "  - Build caches (.next, __pycache__, .ruff_cache, etc.)\n\n"
            if confirm "Proceed with full teardown?"; then
                nuke_docker
                nuke_deps
                nuke_cache
                printf "\n"
                tl_success "Full teardown complete. Run ${GREEN}./tl setup${RESET} to reinstall."
            else
                tl_info "Aborted"
            fi
            ;;
        docker)
            nuke_docker
            ;;
        deps)
            nuke_deps
            ;;
        cache)
            nuke_cache
            ;;
        --help|-h)
            show_nuke_help
            ;;
        "")
            # Interactive mode — prompt for each category
            printf "${BOLD}Interactive teardown${RESET} ${DIM}(select what to remove)${RESET}\n\n"

            local did_something=false

            if confirm "Remove Docker containers and volumes?"; then
                nuke_docker
                did_something=true
            fi

            if confirm "Remove dependencies (.venv, node_modules)?"; then
                nuke_deps
                did_something=true
            fi

            if confirm "Remove build caches (.next, __pycache__, etc.)?"; then
                nuke_cache
                did_something=true
            fi

            printf "\n"
            if [ "$did_something" = true ]; then
                tl_success "Teardown complete. Run ${GREEN}./tl setup${RESET} to reinstall."
            else
                tl_info "Nothing removed"
            fi
            ;;
        *)
            tl_error "Unknown option: nuke $mode"
            printf "\n"
            show_nuke_help
            exit 1
            ;;
    esac
}

# ── Composite: check ────────────────────────────────────────────────

run_check() {
    local passed=0
    local failed=0
    local skipped=0
    local results=""

    run_one() {
        local label="$1"
        shift
        tl_info "Running: $label"
        if "$@" ; then
            passed=$((passed + 1))
            results="${results}\n  ${GREEN}✓${RESET} ${label}"
        else
            failed=$((failed + 1))
            results="${results}\n  ${RED}✗${RESET} ${label}"
        fi
    }

    skip_one() {
        local label="$1"
        local reason="$2"
        skipped=$((skipped + 1))
        results="${results}\n  ${YELLOW}○${RESET} ${label} ${DIM}(${reason})${RESET}"
    }

    # verify local — needs curl, jq, docker
    if command -v curl >/dev/null 2>&1 && command -v jq >/dev/null 2>&1 && command -v docker >/dev/null 2>&1; then
        run_one "verify local" "$SCRIPTS_DIR/verify-local.sh"
    else
        skip_one "verify local" "missing: curl/jq/docker"
    fi

    # verify data — needs gcloud, jq, curl
    if command -v gcloud >/dev/null 2>&1 && command -v jq >/dev/null 2>&1 && command -v curl >/dev/null 2>&1; then
        run_one "verify data" "$SCRIPTS_DIR/verify-data.sh"
    else
        skip_one "verify data" "missing: gcloud"
    fi

    # verify phase3 — needs curl, jq
    if command -v curl >/dev/null 2>&1 && command -v jq >/dev/null 2>&1; then
        run_one "verify phase3" "$SCRIPTS_DIR/verify-phase3.sh"
    else
        skip_one "verify phase3" "missing: curl/jq"
    fi

    # verify pipelines — needs gcloud, jq
    if command -v gcloud >/dev/null 2>&1 && command -v jq >/dev/null 2>&1; then
        run_one "verify pipelines" "$SCRIPTS_DIR/verify-pipelines.sh"
    else
        skip_one "verify pipelines" "missing: gcloud"
    fi

    printf "\n${BOLD}Results:${RESET}"
    printf "$results\n"
    printf "\n  ${passed} passed, ${failed} failed, ${skipped} skipped\n"

    [ "$failed" -gt 0 ] && exit 1
    return 0
}

# ── Composite: test-all ─────────────────────────────────────────────

run_test_all() {
    local passed=0
    local failed=0
    local skipped=0
    local results=""

    run_one() {
        local label="$1"
        shift
        tl_info "Running: $label"
        if "$@" ; then
            passed=$((passed + 1))
            results="${results}\n  ${GREEN}✓${RESET} ${label}"
        else
            failed=$((failed + 1))
            results="${results}\n  ${RED}✗${RESET} ${label}"
        fi
    }

    skip_one() {
        local label="$1"
        local reason="$2"
        skipped=$((skipped + 1))
        results="${results}\n  ${YELLOW}○${RESET} ${label} ${DIM}(${reason})${RESET}"
    }

    # test jp-scrape — needs curl, jq, docker
    if command -v curl >/dev/null 2>&1 && command -v jq >/dev/null 2>&1 && command -v docker >/dev/null 2>&1; then
        run_one "test jp-scrape" "$SCRIPTS_DIR/test-jp-scrape.sh"
    else
        skip_one "test jp-scrape" "missing: curl/jq/docker"
    fi

    # test production — needs gcloud, jq
    if command -v gcloud >/dev/null 2>&1 && command -v jq >/dev/null 2>&1; then
        run_one "test production" "$SCRIPTS_DIR/test-production-scrapers.sh"
    else
        skip_one "test production" "missing: gcloud"
    fi

    # test jp-pipeline — needs uv, python3
    if command -v uv >/dev/null 2>&1 && command -v python3 >/dev/null 2>&1; then
        run_one "test jp-pipeline" bash -c "cd '$API_DIR' && uv run python scripts/validate_jp_pipeline.py"
    else
        skip_one "test jp-pipeline" "missing: uv/python3"
    fi

    # test shadow — needs uv, python3
    if command -v uv >/dev/null 2>&1 && command -v python3 >/dev/null 2>&1; then
        run_one "test shadow" bash -c "cd '$API_DIR' && uv run python scripts/shadow_compare.py"
    else
        skip_one "test shadow" "missing: uv/python3"
    fi

    printf "\n${BOLD}Results:${RESET}"
    printf "$results\n"
    printf "\n  ${passed} passed, ${failed} failed, ${skipped} skipped\n"

    [ "$failed" -gt 0 ] && exit 1
    return 0
}

# ── Dispatch: verify ────────────────────────────────────────────────

dispatch_verify() {
    local sub="${1:-}"
    [ -n "$sub" ] && shift

    case "$sub" in
        local)
            require_deps curl jq docker
            exec "$SCRIPTS_DIR/verify-local.sh" "$@"
            ;;
        data)
            require_deps gcloud jq curl
            exec "$SCRIPTS_DIR/verify-data.sh" "$@"
            ;;
        phase3)
            require_deps curl jq
            exec "$SCRIPTS_DIR/verify-phase3.sh" "$@"
            ;;
        pipelines)
            require_deps gcloud jq
            exec "$SCRIPTS_DIR/verify-pipelines.sh" "$@"
            ;;
        ""|--help|-h)
            show_verify_help
            ;;
        *)
            tl_error "Unknown subcommand: verify $sub"
            printf "\n"
            show_verify_help
            exit 1
            ;;
    esac
}

# ── Dispatch: test ──────────────────────────────────────────────────

dispatch_test() {
    local sub="${1:-}"
    [ -n "$sub" ] && shift

    case "$sub" in
        jp-scrape)
            require_deps curl jq docker
            exec "$SCRIPTS_DIR/test-jp-scrape.sh" "$@"
            ;;
        production)
            require_deps gcloud jq
            exec "$SCRIPTS_DIR/test-production-scrapers.sh" "$@"
            ;;
        jp-pipeline)
            require_deps uv python3
            cd "$API_DIR"
            exec uv run python "scripts/validate_jp_pipeline.py" "$@"
            ;;
        shadow)
            require_deps uv python3
            cd "$API_DIR"
            exec uv run python "scripts/shadow_compare.py" "$@"
            ;;
        ""|--help|-h)
            show_test_help
            ;;
        *)
            tl_error "Unknown subcommand: test $sub"
            printf "\n"
            show_test_help
            exit 1
            ;;
    esac
}

# ── Dispatch: seed ──────────────────────────────────────────────────

dispatch_seed() {
    local sub="${1:-}"
    [ -n "$sub" ] && shift

    case "$sub" in
        formats)
            require_deps uv python3
            cd "$API_DIR"
            exec uv run "scripts/seed-formats.py" "$@"
            ;;
        tournaments)
            require_deps uv python3
            cd "$API_DIR"
            exec uv run "scripts/seed-tournaments.py" "$@"
            ;;
        ""|--help|-h)
            show_seed_help
            ;;
        *)
            tl_error "Unknown subcommand: seed $sub"
            printf "\n"
            show_seed_help
            exit 1
            ;;
    esac
}

# ── Dispatch: sync ──────────────────────────────────────────────────

dispatch_sync() {
    local sub="${1:-}"
    [ -n "$sub" ] && shift

    case "$sub" in
        cards)
            require_deps uv python3
            cd "$API_DIR"
            exec uv run "scripts/sync-cards.py" "$@"
            ;;
        mappings)
            require_deps uv python3
            cd "$API_DIR"
            exec uv run "scripts/sync-card-mappings.py" "$@"
            ;;
        ""|--help|-h)
            show_sync_help
            ;;
        *)
            tl_error "Unknown subcommand: sync $sub"
            printf "\n"
            show_sync_help
            exit 1
            ;;
    esac
}

# ── Main ────────────────────────────────────────────────────────────

cmd="${1:-}"
[ -n "$cmd" ] && shift

case "$cmd" in
    dev)       run_dev ;;
    setup)     run_setup ;;
    nuke)      run_nuke "$@" ;;
    check)     run_check ;;
    test-all)  run_test_all ;;

    verify)   dispatch_verify "$@" ;;
    test)     dispatch_test "$@" ;;
    seed)     dispatch_seed "$@" ;;
    sync)     dispatch_sync "$@" ;;

    db)
        require_deps docker
        exec "$SCRIPTS_DIR/db-local.sh" "$@"
        ;;
    export)
        require_deps curl docker
        exec "$SCRIPTS_DIR/export-data.sh" "$@"
        ;;
    ingest)
        sub="${1:-}"
        [ -n "$sub" ] && shift
        case "$sub" in
            jp)
                require_deps curl jq docker
                exec "$SCRIPTS_DIR/ingest-jp-deep.sh" "$@"
                ;;
            ""|--help|-h)
                printf "${BOLD}INGEST${RESET} — Data ingestion\n\n"
                fmt_cmd "ingest jp" "ingest-jp-deep.sh       [curl, jq, docker]"
                printf "\n${DIM}Example: ./tl ingest jp --limit 5${RESET}\n"
                ;;
            *)
                tl_error "Unknown subcommand: ingest $sub"
                exit 1
                ;;
        esac
        ;;

    ""|--help|-h|help)
        show_help
        ;;
    *)
        tl_error "Unknown command: $cmd"
        printf "\n"
        show_help
        exit 1
        ;;
esac
