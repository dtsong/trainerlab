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

## Key Decisions
- TCGdex is primary card data source
- Japanese meta data needs BO1 context (tie = double loss)
- Target: competitors, coaches, creators, parents

## Current Focus
[Update this as you work]
- Building card database + search
- Next: deck builder MVP
