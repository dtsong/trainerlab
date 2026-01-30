# TrainerLab

> Your competitive research lab for Pokemon TCG

**Website:** [trainerlab.io](https://trainerlab.io)

---

## What is TrainerLab?

TrainerLab is a competitive intelligence platform for Pokemon TCG. We help trainers, coaches, content creators, and families make data-driven decisions about deck building, format preparation, and the hobby.

**Key Features:**
- 🔬 **Meta Dashboard** — What's winning, where, and how it's trending
- 🇯🇵 **Japanese Format Preview** — Translated results with BO1 context
- 🃏 **Smart Deck Builder** — Inclusion rates, consistency metrics, compare to top lists
- 📊 **Format Forecasting** — Know what's coming before your opponents do

---

## Documentation

| Document | Description |
|----------|-------------|
| [SPEC.md](./SPEC.md) | Full implementation specification |
| [PROJECT_STATUS.md](./PROJECT_STATUS.md) | Current project status and decisions |
| [terraform/README.md](./terraform/README.md) | Infrastructure documentation |
| [docs/TRAINERLAB_BRAND.md](./docs/TRAINERLAB_BRAND.md) | Brand guide and messaging |

---

## Tech Stack

- **Frontend:** Next.js 14+, TypeScript, Tailwind, shadcn/ui
- **Backend:** FastAPI, Python 3.11+
- **Database:** PostgreSQL 15 + pgvector (Cloud SQL)
- **Cache:** Redis (Memorystore)
- **Card Data:** TCGdex (self-hosted)
- **Infrastructure:** GCP (Cloud Run, managed via Terraform)

---

## Getting Started

### Local Development

```bash
# Start local services (Postgres, Redis, TCGdex)
docker-compose up -d

# Frontend
cd apps/web
pnpm install
pnpm dev

# Backend
cd apps/api
poetry install
poetry run uvicorn src.main:app --reload
```

### Deploy Infrastructure

```bash
cd terraform
terraform init
terraform apply -var-file=environments/dev.tfvars
```

See [terraform/README.md](./terraform/README.md) for full deployment instructions.

---

## Project Status

🟢 **Phase: Ready for Development**

- ✅ Brand and naming finalized (TrainerLab)
- ✅ Domains secured (trainerlab.io, trainerlab.org)
- ✅ Technical spec complete
- ✅ Infrastructure as code ready (Terraform)
- ⏳ Development starting

---

## Key Differentiator

Japan plays new Pokemon TCG sets **2-3 months before international release**. Their tournament results preview your future meta — but the data is in Japanese and lacks context.

TrainerLab:
- Translates Japanese tournament data automatically
- Contextualizes BO1 vs BO3 format differences
- Explains tie rules (favors aggro in Japan)
- Gives you a **2-3 month head start** on format preparation

---

## License

TBD

---

*TrainerLab — Do the homework. Win the tournament.*
