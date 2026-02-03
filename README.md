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

| Document                                               | Description                            |
| ------------------------------------------------------ | -------------------------------------- |
| [SPEC.md](./SPEC.md)                                   | Full implementation specification      |
| [PROJECT_STATUS.md](./PROJECT_STATUS.md)               | Current project status and decisions   |
| [terraform/README.md](./terraform/README.md)           | Infrastructure documentation           |
| [docs/TRAINERLAB_BRAND.md](./docs/TRAINERLAB_BRAND.md) | Brand guide and messaging              |
| [Architecture](./docs/architecture/README.md)          | System architecture diagrams (Mermaid) |

---

## Tech Stack

- **Frontend:** Next.js 14+, TypeScript, Tailwind, shadcn/ui
- **Backend:** FastAPI, Python 3.11+
- **Database:** PostgreSQL 16 + pgvector (Cloud SQL)
- **Cache:** Redis (Memorystore)
- **Card Data:** TCGdex (self-hosted)
- **Infrastructure:** GCP (Cloud Run, managed via Terraform)

---

## Getting Started

### Prerequisites

- [Node.js 18+](https://nodejs.org/) (recommend using [nvm](https://github.com/nvm-sh/nvm))
- [pnpm 8+](https://pnpm.io/) — `npm install -g pnpm`
- [uv](https://docs.astral.sh/uv/) — `curl -LsSf https://astral.sh/uv/install.sh | sh`
- [Docker](https://www.docker.com/) (for local services)

### Quick Start

```bash
# 1. Clone and install dependencies
git clone https://github.com/dtsong/trainerlab.git
cd trainerlab
pnpm install

# 2. Setup pre-commit hooks
pre-commit install

# 3. Start local services (Postgres, Redis, TCGdex)
docker compose up -d

# 4. Setup environment files
cp .env.example .env
cp apps/api/.env.example apps/api/.env
cp apps/web/.env.example apps/web/.env.local
```

### Development

```bash
# Frontend (Next.js)
pnpm dev                    # Start dev server (apps/web)

# Backend (FastAPI)
cd apps/api
uv sync                     # Install Python dependencies
uv run uvicorn src.main:app --reload

# Run tests
pnpm --filter @trainerlab/shared-types test
cd apps/api && uv run pytest
```

### Admin Dashboard

The admin dashboard is available at `/admin` (e.g., `http://localhost:3000/admin` locally).

**Authentication:** You must be logged in via NextAuth.js. Your email must be in the whitelist defined in `apps/web/src/lib/admin.ts`.

**Pages:**

| Route                | Description                                       |
| -------------------- | ------------------------------------------------- |
| `/admin`             | Overview — tournament, card, and meta stats       |
| `/admin/tournaments` | Tournament data with placement details            |
| `/admin/meta`        | Meta snapshot analysis (region/format/BO filters) |
| `/admin/cards`       | Card database search                              |

### Tooling

| Tool   | Purpose                     | Commands                           |
| ------ | --------------------------- | ---------------------------------- |
| pnpm   | Node.js package manager     | `pnpm install`, `pnpm dev`         |
| uv     | Python package manager      | `uv sync`, `uv run pytest`         |
| ruff   | Python linting & formatting | `uv run ruff check`, `ruff format` |
| ty     | Python type checking        | `uv run ty check src`              |
| vitest | TypeScript testing          | `pnpm test`, `pnpm test:coverage`  |

### Deploy Infrastructure

```bash
cd terraform
terraform init
terraform apply -var-file=environments/dev.tfvars
```

See [terraform/README.md](./terraform/README.md) for full deployment instructions.

---

## Project Status

🟢 **Phase: Closed Beta**

- ✅ Brand and naming finalized (TrainerLab)
- ✅ Domains secured (trainerlab.io, trainerlab.org)
- ✅ Technical spec complete
- ✅ Infrastructure deployed (Terraform + GCP)
- ✅ Card database + search
- ✅ Deck builder MVP
- ✅ Meta dashboard with JP integration
- ✅ Data pipeline (Cloud Scheduler + Cloud Tasks)
- ✅ Authentication (NextAuth.js + Google OAuth)
- ⏳ Beta recruitment and soft launch

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

_TrainerLab — Do the homework. Win the tournament._
