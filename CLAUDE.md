# TrainerLab

## What This Is

Competitive intelligence platform for Pokemon TCG. See full docs in Obsidian vault.

## Key Docs (Read These First)

- `/docs/SPEC.md` — Full implementation specification
- `/docs/TECHNICAL_OVERVIEW.md` — Architecture summary

## Quick Context

- Frontend: Next.js 14+, Tailwind, shadcn/ui
- Backend: FastAPI (Python)
- Database: PostgreSQL + pgvector on GCP Cloud SQL
- Card Data: TCGdex (self-hosted)
- Hosting: GCP Cloud Run via Terraform

## Tooling

### Python (apps/api)

- **uv** - Package manager and runner (`uv sync`, `uv run pytest`)
- **ruff** - Linting and formatting (`uv run ruff check`, `uv run ruff format`)
- **ty** - Type checking (`uv run ty check src`)
- **pytest** - Testing with coverage (`uv run pytest --cov`)

### TypeScript (apps/web, packages/\*)

- **pnpm** - Package manager (workspace-based)
- **Vitest** - Testing with coverage (`pnpm test:coverage`)
- **Prettier** - Formatting

### Pre-commit

Pre-commit hooks are configured for both Python and TypeScript. Run `pre-commit install` after cloning.

## Key Decisions

- TCGdex is primary card data source
- Japanese meta data needs BO1 context (tie = double loss)
- Target: competitors, coaches, creators, parents

## Testing

- All feature work must include unit tests
- Write tests before or alongside implementation (TDD preferred)
- Frontend: Vitest + React Testing Library
- Backend: pytest

## Git Workflow

- All changes must be submitted via pull request
- Direct pushes to main are not allowed
- PRs require review before merging

## Current Focus

[Update this as you work]

- Building card database + search
- Next: deck builder MVP
