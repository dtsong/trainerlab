# TrainerLab - Project Status

> Last updated: February 2026

---

## Brand

| Item                 | Status                                                                             |
| -------------------- | ---------------------------------------------------------------------------------- |
| **Name**             | TrainerLab ✅                                                                      |
| **Domain (primary)** | trainerlab.io ✅ Secured                                                           |
| **Domain (backup)**  | trainerlab.org ✅ Secured                                                          |
| **Tagline**          | "Your competitive research lab"                                                    |
| **Positioning**      | Competitive intelligence for Pokemon TCG trainers, coaches, creators, and families |

---

## Documentation Complete

| Document                     | Description                              | Location                          |
| ---------------------------- | ---------------------------------------- | --------------------------------- |
| **SPEC.md**                  | Full implementation spec for Claude Code | `/docs/SPEC.md`                   |
| **Terraform**                | Complete GCP infrastructure as code      | `/terraform/`                     |
| **Brand Guide**              | TrainerLab brand, voice, messaging       | `/docs/TRAINERLAB_BRAND.md`       |
| **Japanese Research**        | Data sources, translation strategy       | `/docs/JAPANESE_META_RESEARCH.md` |
| **Card Data Infrastructure** | TCGdex evaluation, data pipeline         | `/docs/PLATFORM_EXPLORATION.md`   |

---

## Key Decisions Made

| Decision             | Choice                                  | Rationale                                                           |
| -------------------- | --------------------------------------- | ------------------------------------------------------------------- |
| **Card Data Source** | TCGdex (self-hosted)                    | Active maintenance, 14 languages including Japanese, self-hostable  |
| **Hosting**          | GCP (Cloud Run, Cloud SQL, Memorystore) | Familiarity, Terraform support, scalable                            |
| **Frontend**         | Next.js 14+                             | SSR, good DX, App Router                                            |
| **Backend**          | FastAPI (Python)                        | Type-safe, good for data work                                       |
| **Database**         | PostgreSQL 16 + pgvector                | Managed via Cloud SQL, vector similarity search for card embeddings |
| **Auth**             | NextAuth.js + Google OAuth              | HS256 JWT shared between frontend and backend                       |

---

## Target Audiences

1. **Competitors** — Tournament prep, deck building, format understanding
2. **Coaches** — Teaching tools, data for students
3. **Content Creators** — Research acceleration for articles/videos
4. **Parents** — Understanding the hobby, helping kids improve

---

## Key Differentiator

**Japanese Meta Integration**

- Japan plays new sets 2-3 months before international release
- We translate and contextualize their tournament data
- Critical context: BO1 format, tie = double loss rule (favors aggro)
- Users get a format preview before opponents

---

## MVP Features

| Feature            | Priority | Description                                  |
| ------------------ | -------- | -------------------------------------------- |
| Card Database      | P0       | Search with Japanese names, fuzzy matching   |
| Deck Builder       | P0       | Build, save, export with inclusion rates     |
| Meta Dashboard     | P0       | Archetype shares, trends, regional breakdown |
| Japanese Meta View | P0       | Translated results with BO1 context          |
| User Auth          | P0       | Basic login, save decks                      |

---

## Technical Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        TrainerLab                            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Cloud Run (Next.js)  ←→  Cloud Run (FastAPI)               │
│         ↓                        ↓                          │
│    Cloud CDN              ┌──────┴──────┐                   │
│                           ↓             ↓                   │
│                    Cloud SQL      Memorystore               │
│                   (Postgres)       (Redis)                  │
│                           ↑                                 │
│                    Cloud Run (TCGdex)                       │
│                                                              │
│  Secret Manager │ Cloud Build │ Cloud Scheduler             │
└─────────────────────────────────────────────────────────────┘
```

---

## Estimated Costs

| Environment | Monthly  |
| ----------- | -------- |
| Development | $50-100  |
| Production  | $150-250 |

---

## Next Steps

### Completed

1. [x] Set up GCP project
2. [x] Run Terraform bootstrap (state bucket)
3. [x] Run Terraform apply (infrastructure)
4. [x] Initialize code repository
5. [x] Build card database + search
6. [x] Build deck builder MVP
7. [x] Build meta dashboard
8. [x] Add Japanese data integration
9. [x] Deploy to Cloud Run
10. [x] Landing page with email capture

### In Progress

1. [ ] Beta user recruitment (Reddit, Discord)
2. [ ] Content: "Introducing TrainerLab" post
3. [ ] Soft launch to competitive community

### Launch Readiness Gaps (Feb 2026)

1. [ ] Pipeline health workflow environment variable/fallback hardening
2. [ ] Dedicated official vs grassroots analysis tracks (UX + routing)
3. [ ] Creator surfaces pending: OG image generation and creator dashboard

---

## Repository Structure

```
trainerlab/
├── README.md
├── docker-compose.yml
│
├── apps/
│   ├── web/                     # Next.js frontend
│   └── api/                     # FastAPI backend
│
├── packages/
│   └── shared-types/            # Shared TypeScript types
│
├── terraform/                   # GCP infrastructure
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   └── environments/
│
└── docs/
    ├── SPEC.md                  # Implementation spec
    ├── CODEMAP.md               # Codebase structure quick reference
    ├── PROJECT_STATUS.md
    ├── TRAINERLAB_BRAND.md
    ├── architecture/            # System architecture diagrams
    │   ├── README.md
    │   ├── SYSTEM_OVERVIEW.md
    │   ├── DATA_PIPELINE.md
    │   ├── APPLICATION_LAYERS.md
    │   ├── AUTHENTICATION.md
    │   └── CI_CD_DEPLOYMENT.md
    └── research/
        ├── JAPANESE_META_RESEARCH.md
        └── CARD_DATA_INFRASTRUCTURE.md
```

---

_TrainerLab — Your competitive research lab_
