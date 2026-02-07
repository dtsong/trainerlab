#!/usr/bin/env bash
set -euo pipefail

# ── TrainerLab Developer CLI ────────────────────────────────────────
# Unified entry point for all developer scripts.
# Run ./tl --help for usage.

# ── Paths ───────────────────────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPTS_DIR="$SCRIPT_DIR/scripts"
LOCAL_SCRIPTS="$SCRIPTS_DIR/local"
CLOUD_SCRIPTS="$SCRIPTS_DIR/cloud"
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
    fmt_cmd "dev"              "Start local stack (Postgres + API + web)"
    fmt_cmd "start"            "Start Postgres + API server only (no web)"
    fmt_cmd "setup"            "First-time setup (deps, Docker, migrations, seed)"
    fmt_cmd "nuke"             "Teardown all local resources for clean reinstall"
    fmt_cmd "check"            "Run all verification scripts"
    fmt_cmd "test-all"         "Run all test scripts"
    fmt_cmd "health"           "Pipeline health check (scrape, meta, archetype)"
    printf "\n"

    printf "${BOLD}${RED}PROD${RESET} — Production access (read-only)                    ${DIM}[cloud]${RESET}\n"
    fmt_cmd "prod db"          "Connect to prod DB via Cloud SQL Proxy"
    fmt_cmd "prod logs"        "Stream Cloud Run logs (--follow to tail)"
    fmt_cmd "prod trigger <p>" "Trigger pipeline dry-run (--execute for real)"
    fmt_cmd "prod health"      "Hit prod pipeline health endpoint"
    fmt_cmd "prod snapshot"    "Export prod data to local Postgres (--restore)"
    printf "\n"

    printf "${BOLD}${YELLOW}VERIFY${RESET} — Data quality & endpoint verification\n"
    fmt_cmd "verify local"     "Verify local Docker environment              [local]"
    fmt_cmd "verify data"      "Verify production data quality               [cloud]"
    fmt_cmd "verify phase3"    "Deep validate Phase 3 features               [cloud]"
    fmt_cmd "verify pipelines" "Verify Cloud Scheduler pipelines             [cloud]"
    fmt_cmd "verify all-prod"  "Run data + phase3 against production         [cloud]"
    printf "\n"

    printf "${BOLD}${YELLOW}TEST${RESET} — Subsystem testing\n"
    fmt_cmd "test jp-scrape"   "Test JP tournament scraping                  [local]"
    fmt_cmd "test production"  "Test production scrapers                     [cloud]"
    fmt_cmd "test jp-pipeline" "Validate JP archetype pipeline               [local]"
    fmt_cmd "test shadow"      "Shadow compare archetype labels              [local]"
    printf "\n"

    printf "${BOLD}${YELLOW}DATA${RESET} — Database & data management\n"
    fmt_cmd "db [args]"        "Local database access (psql)                 [local]"
    fmt_cmd "seed formats"     "Seed format configuration data               [local]"
    fmt_cmd "seed tournaments" "Seed tournament fixture data                 [local]"
    fmt_cmd "export [args]"    "Export local data for analysis               [local]"
    fmt_cmd "ingest jp"        "Deep ingest JP City League data              [local]"
    printf "\n"

    printf "${BOLD}${YELLOW}SYNC${RESET} — External data synchronization\n"
    fmt_cmd "sync cards"       "Sync card data from TCGdex                   [local]"
    fmt_cmd "sync mappings"    "Sync JP↔EN card ID mappings                  [local]"
    printf "\n"

    printf "${BOLD}${YELLOW}DOCKER${RESET} — Container maintenance\n"
    fmt_cmd "docker stats"     "Show Docker disk usage"
    fmt_cmd "docker prune"     "Remove dangling images, volumes, build cache"
    fmt_cmd "docker prune-all" "Remove ALL unused Docker resources"
    printf "\n"

    printf "${DIM}Pass --help to any command for its own usage info.${RESET}\n"
}

show_verify_help() {
    printf "${BOLD}VERIFY${RESET} — Data quality & endpoint verification\n\n"
    fmt_cmd "verify local"     "verify-local.sh      [curl, jq, docker]       [local]"
    fmt_cmd "verify data"      "verify-data.sh       [gcloud, jq, curl]       [cloud]"
    fmt_cmd "verify phase3"    "verify-phase3.sh     [gcloud, jq, curl]       [cloud]"
    fmt_cmd "verify pipelines" "verify-pipelines.sh  [gcloud, jq]             [cloud]"
    fmt_cmd "verify all-prod"  "Run data + phase3 against production          [cloud]"
    printf "\n${DIM}Example: ./tl verify local --group=cards${RESET}\n"
}

show_test_help() {
    printf "${BOLD}TEST${RESET} — Subsystem testing\n\n"
    fmt_cmd "test jp-scrape"       "test-jp-scrape.sh              [curl, jq, docker]"
    fmt_cmd "test production"      "test-production-scrapers.sh    [gcloud, jq]"
    fmt_cmd "test jp-pipeline"     "validate_jp_pipeline.py        [uv, python3]"
    fmt_cmd "test shadow"          "shadow_compare.py              [uv, python3]"
    fmt_cmd "test sprite-coverage" "sprite_coverage_report.py      [uv, python3]"
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

# ── Composite: start ────────────────────────────────────────────────

run_start() {
    require_deps docker uv

    tl_info "Starting PostgreSQL..."
    docker compose -f "$SCRIPT_DIR/docker-compose.yml" up -d db

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

    tl_info "Starting API server (uvicorn)..."
    printf "${DIM}Press Ctrl+C to stop${RESET}\n\n"

    API_PID=""

    cleanup() {
        printf "\n"
        tl_info "Shutting down..."
        [ -n "$API_PID" ] && kill "$API_PID" 2>/dev/null
        wait "$API_PID" 2>/dev/null
        tl_info "Stopping Docker services..."
        docker compose -f "$SCRIPT_DIR/docker-compose.yml" stop db
        tl_success "All services stopped"
    }
    trap cleanup INT TERM

    (cd "$API_DIR" && uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8080) &
    API_PID=$!

    wait "$API_PID" 2>/dev/null || true
}

# ── Composite: dev ──────────────────────────────────────────────────

run_dev() {
    require_deps docker uv pnpm

    tl_info "Starting PostgreSQL..."
    docker compose -f "$SCRIPT_DIR/docker-compose.yml" up -d db

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
        docker compose -f "$SCRIPT_DIR/docker-compose.yml" stop db
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

    tl_info "Starting PostgreSQL..."
    docker compose -f "$SCRIPT_DIR/docker-compose.yml" up -d db

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

        tl_info "Removing Docker volumes (postgres_data)..."
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
        run_one "verify local" "$LOCAL_SCRIPTS/verify-local.sh"
    else
        skip_one "verify local" "missing: curl/jq/docker"
    fi

    # verify data — needs gcloud, jq, curl
    if command -v gcloud >/dev/null 2>&1 && command -v jq >/dev/null 2>&1 && command -v curl >/dev/null 2>&1; then
        run_one "verify data" "$CLOUD_SCRIPTS/verify-data.sh"
    else
        skip_one "verify data" "missing: gcloud"
    fi

    # verify phase3 — needs gcloud, jq, curl (cloud-first)
    if command -v gcloud >/dev/null 2>&1 && command -v jq >/dev/null 2>&1 && command -v curl >/dev/null 2>&1; then
        run_one "verify phase3" "$CLOUD_SCRIPTS/verify-phase3.sh"
    else
        skip_one "verify phase3" "missing: gcloud/jq/curl"
    fi

    # verify pipelines — needs gcloud, jq
    if command -v gcloud >/dev/null 2>&1 && command -v jq >/dev/null 2>&1; then
        run_one "verify pipelines" "$CLOUD_SCRIPTS/verify-pipelines.sh"
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
        run_one "test jp-scrape" "$LOCAL_SCRIPTS/test-jp-scrape.sh"
    else
        skip_one "test jp-scrape" "missing: curl/jq/docker"
    fi

    # test production — needs gcloud, jq
    if command -v gcloud >/dev/null 2>&1 && command -v jq >/dev/null 2>&1; then
        run_one "test production" "$CLOUD_SCRIPTS/test-production-scrapers.sh"
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
            exec "$LOCAL_SCRIPTS/verify-local.sh" "$@"
            ;;
        data)
            require_deps gcloud jq curl
            exec "$CLOUD_SCRIPTS/verify-data.sh" "$@"
            ;;
        phase3)
            require_deps gcloud jq curl
            exec "$CLOUD_SCRIPTS/verify-phase3.sh" "$@"
            ;;
        pipelines)
            require_deps gcloud jq
            exec "$CLOUD_SCRIPTS/verify-pipelines.sh" "$@"
            ;;
        all-prod)
            require_deps gcloud jq curl
            tl_info "Running all production verification..."
            local ap_failed=0

            tl_info "=== verify data (production) ==="
            "$CLOUD_SCRIPTS/verify-data.sh" "$@" || ap_failed=1

            tl_info "=== verify phase3 (production) ==="
            "$CLOUD_SCRIPTS/verify-phase3.sh" "$@" || ap_failed=1

            if [ "$ap_failed" -gt 0 ]; then
                tl_error "One or more production checks failed"
                exit 1
            fi
            tl_success "All production checks passed"
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
            exec "$LOCAL_SCRIPTS/test-jp-scrape.sh" "$@"
            ;;
        production)
            require_deps gcloud jq
            exec "$CLOUD_SCRIPTS/test-production-scrapers.sh" "$@"
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
        sprite-coverage)
            require_deps uv python3
            cd "$API_DIR"
            exec uv run python "scripts/sprite_coverage_report.py" "$@"
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

# ── Dispatch: docker ────────────────────────────────────────

show_docker_help() {
    printf "${BOLD}DOCKER${RESET} — Container maintenance\n\n"
    fmt_cmd "docker stats"     "Show Docker disk usage (docker system df)"
    fmt_cmd "docker prune"     "Remove dangling images, unused volumes, build cache"
    fmt_cmd "docker prune-all" "Remove ALL unused Docker resources (⚠ destructive)"
    printf "\n${DIM}Example: ./tl docker prune${RESET}\n"
}

dispatch_docker() {
    local sub="${1:-}"
    [ -n "$sub" ] && shift

    case "$sub" in
        stats)
            require_deps docker
            tl_info "Docker disk usage:"
            docker system df
            ;;
        prune)
            require_deps docker
            tl_info "Pruning dangling images..."
            docker image prune -f
            tl_info "Pruning unused volumes..."
            docker volume prune -f
            tl_info "Pruning build cache..."
            docker builder prune -f
            tl_success "Prune complete"
            printf "\n"
            docker system df
            ;;
        prune-all)
            require_deps docker
            printf "${RED}${BOLD}This will remove ALL unused Docker resources:${RESET}\n"
            printf "  - All stopped containers\n"
            printf "  - All unused networks\n"
            printf "  - All unused images (not just dangling)\n"
            printf "  - All unused volumes\n"
            printf "  - All build cache\n\n"
            printf "${YELLOW}?${RESET} Proceed? [y/N] "
            read -r answer
            case "$answer" in
                [yY]|[yY][eE][sS])
                    docker system prune -a --volumes -f
                    tl_success "Full prune complete"
                    printf "\n"
                    docker system df
                    ;;
                *)
                    tl_info "Aborted"
                    ;;
            esac
            ;;
        ""|--help|-h)
            show_docker_help
            ;;
        *)
            tl_error "Unknown subcommand: docker $sub"
            printf "\n"
            show_docker_help
            exit 1
            ;;
    esac
}

# ── Dispatch: prod ─────────────────────────────────────────────────

show_prod_help() {
    printf "${BOLD}${RED}PROD${RESET} — Production access (read-only, safe defaults)\n\n"
    fmt_cmd "prod db"            "Connect to prod DB via Cloud SQL Proxy (read-only)"
    fmt_cmd "prod logs"          "Stream Cloud Run logs (add --follow to tail)"
    fmt_cmd "prod trigger <pip>" "Trigger pipeline dry-run (--execute for real run)"
    fmt_cmd "prod health"        "Hit prod /api/v1/health/pipeline endpoint"
    fmt_cmd "prod snapshot"      "Export prod tables to local Postgres (--restore)"
    printf "\n${DIM}Safety: 'prod trigger' defaults to dry-run. Use --execute for real runs.${RESET}\n"
}

# Project and Cloud Run service defaults
PROD_PROJECT="${PROD_PROJECT:-trainerlab-prod}"
PROD_REGION="${PROD_REGION:-us-west1}"
PROD_INSTANCE="${PROD_INSTANCE:-trainerlab-db}"
PROD_DB_USER="${PROD_DB_USER:-trainerlab_dev}"
PROD_SERVICE="${PROD_SERVICE:-trainerlab-api}"
PROD_OPS_SA="${PROD_OPS_SA:-trainerlab-ops@trainerlab-prod.iam.gserviceaccount.com}"

dispatch_prod() {
    local sub="${1:-}"
    [ -n "$sub" ] && shift

    case "$sub" in
        db)
            require_deps gcloud cloud-sql-proxy psql
            tl_info "Connecting to prod DB (read-only) via Cloud SQL Proxy..."
            tl_info "Starting proxy on localhost:15432..."

            # Start proxy in background
            cloud-sql-proxy "${PROD_PROJECT}:${PROD_REGION}:${PROD_INSTANCE}" \
                --port 15432 \
                --impersonate-service-account="${PROD_OPS_SA}" &
            local proxy_pid=$!
            sleep 3

            trap "kill $proxy_pid 2>/dev/null" EXIT

            tl_info "Connecting as ${PROD_DB_USER}..."
            psql "postgresql://${PROD_DB_USER}@localhost:15432/trainerlab" "$@"

            kill "$proxy_pid" 2>/dev/null
            ;;

        logs)
            require_deps gcloud
            local follow_flag=""
            for arg in "$@"; do
                case "$arg" in
                    --follow|-f) follow_flag="--tail=50" ;;
                esac
            done

            tl_info "Streaming Cloud Run logs for ${PROD_SERVICE}..."
            if [ -n "$follow_flag" ]; then
                gcloud run services logs tail "${PROD_SERVICE}" \
                    --project="${PROD_PROJECT}" \
                    --region="${PROD_REGION}"
            else
                gcloud run services logs read "${PROD_SERVICE}" \
                    --project="${PROD_PROJECT}" \
                    --region="${PROD_REGION}" \
                    --limit=100
            fi
            ;;

        trigger)
            require_deps gcloud curl jq
            local pipeline="${1:-}"
            [ -n "$pipeline" ] && shift

            if [ -z "$pipeline" ]; then
                tl_error "Usage: ./tl prod trigger <pipeline> [--execute]"
                printf "\n  Pipelines: discover-en, discover-jp, compute-meta, compute-evolution\n"
                printf "             sync-cards, sync-card-mappings, reprocess-archetypes\n"
                printf "             translate-pokecabook, translate-tier-lists\n"
                printf "             sync-jp-adoption, monitor-card-reveals\n"
                printf "\n  ${DIM}Default: dry-run. Add --execute for real run.${RESET}\n"
                exit 1
            fi

            local dry_run="true"
            for arg in "$@"; do
                case "$arg" in
                    --execute) dry_run="false" ;;
                esac
            done

            if [ "$dry_run" = "true" ]; then
                tl_info "DRY RUN: ${pipeline} (add --execute for real run)"
            else
                printf "${RED}${BOLD}EXECUTING${RESET}: ${pipeline} against production\n"
            fi

            # Get Cloud Run URL (use CLOUD_RUN_URL env var for correct audience)
            local url
            url=$(gcloud run services describe "${PROD_SERVICE}" \
                --project="${PROD_PROJECT}" \
                --region="${PROD_REGION}" \
                --format='yaml(spec.template.spec.containers[0].env)' \
                | grep -A1 'name: CLOUD_RUN_URL' | grep 'value:' \
                | sed 's/.*value: //')
            if [ -z "$url" ]; then
                # Fallback to service status URL
                url=$(gcloud run services describe "${PROD_SERVICE}" \
                    --project="${PROD_PROJECT}" \
                    --region="${PROD_REGION}" \
                    --format='value(status.url)')
            fi
            local token
            token=$(gcloud auth print-identity-token \
                --impersonate-service-account="${PROD_OPS_SA}" \
                --include-email \
                --audiences="${url}")

            curl -s -X POST \
                "${url}/api/v1/pipeline/${pipeline}" \
                -H "Authorization: Bearer ${token}" \
                -H "Content-Type: application/json" \
                -d "{\"dry_run\": ${dry_run}}" | jq .
            ;;

        health)
            require_deps gcloud curl jq
            local url
            url=$(gcloud run services describe "${PROD_SERVICE}" \
                --project="${PROD_PROJECT}" \
                --region="${PROD_REGION}" \
                --format='value(status.url)')

            tl_info "Checking prod pipeline health..."
            run_health "${url}"
            ;;

        snapshot)
            local restore=false
            for arg in "$@"; do
                case "$arg" in
                    --restore) restore=true ;;
                esac
            done

            if [ "$restore" = true ]; then
                require_deps docker psql
                exec "$CLOUD_SCRIPTS/snapshot-prod.sh" --restore
            else
                require_deps gcloud cloud-sql-proxy pg_dump
                exec "$CLOUD_SCRIPTS/snapshot-prod.sh"
            fi
            ;;

        ""|--help|-h)
            show_prod_help
            ;;
        *)
            tl_error "Unknown subcommand: prod $sub"
            printf "\n"
            show_prod_help
            exit 1
            ;;
    esac
}

# ── Health ──────────────────────────────────────────────────────────

run_health() {
    local api_url="${1:-http://localhost:8080}"

    tl_info "Checking pipeline health at ${api_url}..."

    local raw
    raw=$(curl -s -w "\n%{http_code}" "${api_url}/api/v1/health/pipeline" 2>/dev/null)
    local http_code
    http_code=$(echo "$raw" | tail -n1)
    local body
    body=$(echo "$raw" | sed '$d')

    if [ "$http_code" = "000" ]; then
        tl_error "Cannot reach API at ${api_url}"
        printf "  Start the stack with: ${GREEN}./tl start${RESET}\n"
        exit 1
    fi

    if ! command -v jq >/dev/null 2>&1; then
        tl_error "jq is required for health check output"
        exit 1
    fi

    local overall
    overall=$(echo "$body" | jq -r '.status')

    printf "\n${BOLD}Pipeline Health${RESET}\n"
    printf "────────────────────────────────────────\n"

    # Scrape
    local scrape_status
    scrape_status=$(echo "$body" | jq -r '.scrape.status')
    local scrape_days
    scrape_days=$(echo "$body" | jq -r '.scrape.days_since_scrape // "N/A"')
    local scrape_count
    scrape_count=$(echo "$body" | jq -r '.scrape.tournament_count_7d')

    case "$scrape_status" in
        ok)     printf "  ${GREEN}✓${RESET} Scrape: ${scrape_days}d ago, ${scrape_count} tournaments (7d)\n" ;;
        stale)  printf "  ${YELLOW}○${RESET} Scrape: ${scrape_days}d ago ${DIM}(stale)${RESET}\n" ;;
        *)      printf "  ${RED}✗${RESET} Scrape: ${scrape_status}\n" ;;
    esac

    # Meta
    local meta_status
    meta_status=$(echo "$body" | jq -r '.meta.status')
    local meta_age
    meta_age=$(echo "$body" | jq -r '.meta.snapshot_age_days // "N/A"')
    local meta_regions
    meta_regions=$(echo "$body" | jq -r '.meta.regions | join(", ")')

    case "$meta_status" in
        ok)     printf "  ${GREEN}✓${RESET} Meta:   ${meta_age}d old, regions: ${meta_regions}\n" ;;
        stale)  printf "  ${YELLOW}○${RESET} Meta:   ${meta_age}d old ${DIM}(stale)${RESET}\n" ;;
        *)      printf "  ${RED}✗${RESET} Meta:   ${meta_status}\n" ;;
    esac

    # Archetype
    local arch_status
    arch_status=$(echo "$body" | jq -r '.archetype.status')
    local unknown_rate
    unknown_rate=$(echo "$body" | jq -r '.archetype.unknown_rate')
    local sample_size
    sample_size=$(echo "$body" | jq -r '.archetype.sample_size')

    case "$arch_status" in
        ok)       printf "  ${GREEN}✓${RESET} Archetype: ${unknown_rate} unknown rate (${sample_size} placements)\n" ;;
        degraded) printf "  ${YELLOW}○${RESET} Archetype: ${unknown_rate} unknown rate ${DIM}(degraded)${RESET}\n" ;;
        *)        printf "  ${RED}✗${RESET} Archetype: ${unknown_rate} unknown rate ${DIM}(poor)${RESET}\n" ;;
    esac

    # Overall
    printf "\n"
    case "$overall" in
        healthy)   printf "  ${GREEN}${BOLD}Overall: healthy${RESET}\n" ;;
        degraded)  printf "  ${YELLOW}${BOLD}Overall: degraded${RESET}\n" ;;
        unhealthy) printf "  ${RED}${BOLD}Overall: unhealthy${RESET}\n" ;;
    esac
    printf "\n"

    if [ "$overall" = "unhealthy" ]; then
        exit 1
    fi
}

# ── Main ────────────────────────────────────────────────────────────

cmd="${1:-}"
[ -n "$cmd" ] && shift

case "$cmd" in
    start)     run_start ;;
    dev)       run_dev ;;
    setup)     run_setup ;;
    nuke)      run_nuke "$@" ;;
    check)     run_check ;;
    test-all)  run_test_all ;;

    health)    run_health "$@" ;;
    prod)     dispatch_prod "$@" ;;
    verify)   dispatch_verify "$@" ;;
    test)     dispatch_test "$@" ;;
    seed)     dispatch_seed "$@" ;;
    sync)     dispatch_sync "$@" ;;
    docker)   dispatch_docker "$@" ;;

    db)
        require_deps docker
        exec "$LOCAL_SCRIPTS/db-local.sh" "$@"
        ;;
    export)
        require_deps curl docker
        exec "$LOCAL_SCRIPTS/export-data.sh" "$@"
        ;;
    ingest)
        sub="${1:-}"
        [ -n "$sub" ] && shift
        case "$sub" in
            jp)
                require_deps curl jq docker
                exec "$LOCAL_SCRIPTS/ingest-jp-deep.sh" "$@"
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
