# TrainerLab - Project Status

> Last updated: January 2026

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

| Document                     | Description                              | Location                                     |
| ---------------------------- | ---------------------------------------- | -------------------------------------------- |
| **SPEC.md**                  | Full implementation spec for Claude Code | `/SPEC.md`                                   |
| **Terraform**                | Complete GCP infrastructure as code      | `/terraform/`                                |
| **Brand Guide**              | TrainerLab brand, voice, messaging       | `/docs/TRAINERLAB_BRAND.md`                  |
| **Japanese Research**        | Data sources, translation strategy       | `/docs/research/JAPANESE_META_RESEARCH.md`   |
| **Card Data Infrastructure** | TCGdex evaluation, data pipeline         | `/docs/research/CARD_DATA_INFRASTRUCTURE.md` |

---

## Key Decisions Made

| Decision             | Choice                                  | Rationale                                                          |
| -------------------- | --------------------------------------- | ------------------------------------------------------------------ |
| **Card Data Source** | TCGdex (self-hosted)                    | Active maintenance, 14 languages including Japanese, self-hostable |
| **Hosting**          | GCP (Cloud Run, Cloud SQL, Memorystore) | Familiarity, Terraform support, scalable                           |
| **Frontend**         | Next.js 14+                             | SSR, good DX, App Router                                           |
| **Backend**          | FastAPI (Python)                        | Type-safe, good for data work                                      |
| **Database**         | PostgreSQL 15 + pgvector                | Managed via Cloud SQL, vector search for semantic                  |
| **Auth**             | Firebase Auth or Supabase               | TBD - both integrate well                                          |

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
| Card Database      | P0       | Search with Japanese names, semantic search  |
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

### Immediate

1. [ ] Set up GCP project
2. [ ] Run Terraform bootstrap (state bucket)
3. [ ] Run Terraform apply (infrastructure)
4. [ ] Initialize code repository
5. [ ] Hand SPEC.md to Claude Code to begin development

### Short-term

1. [ ] Build card database + search
2. [ ] Build deck builder MVP
3. [ ] Build meta dashboard
4. [ ] Add Japanese data integration
5. [ ] Deploy to Cloud Run

### Launch Prep

1. [ ] Landing page with email capture
2. [ ] Beta user recruitment (Reddit, Discord)
3. [ ] Content: "Introducing TrainerLab" post
4. [ ] Soft launch to competitive community

---

## Repository Structure

```
trainerlab/
├── SPEC.md                      # Implementation spec
├── README.md
├── docker-compose.yml
├── cloudbuild.yaml
│
├── apps/
│   ├── web/                     # Next.js frontend
│   └── api/                     # FastAPI backend
│
├── terraform/                   # GCP infrastructure
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   ├── bootstrap/
│   └── environments/
│
└── docs/
    ├── TRAINERLAB_BRAND.md
    └── research/
        ├── JAPANESE_META_RESEARCH.md
        └── CARD_DATA_INFRASTRUCTURE.md
```

---

_TrainerLab — Your competitive research lab_
