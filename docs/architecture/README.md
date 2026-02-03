# TrainerLab Architecture

> Mermaid diagrams illustrating TrainerLab's cloud infrastructure and component interactions.

## Diagrams

| Diagram                                       | Description                                      |
| --------------------------------------------- | ------------------------------------------------ |
| [System Overview](./SYSTEM_OVERVIEW.md)       | Executive-level view of the entire platform      |
| [Data Pipeline](./DATA_PIPELINE.md)           | Automated data ingestion and processing system   |
| [Application Layers](./APPLICATION_LAYERS.md) | Internal architecture and separation of concerns |
| [CI/CD & Deployment](./CI_CD_DEPLOYMENT.md)   | DevOps pipeline and infrastructure management    |
| [Authentication](./AUTHENTICATION.md)         | End-to-end authentication flows                  |

## Quick Reference

### Infrastructure

- **Frontend:** Next.js 14+ on Vercel (trainerlab.io)
- **Backend:** FastAPI on GCP Cloud Run (api.trainerlab.io)
- **Database:** PostgreSQL 16 + pgvector on Cloud SQL
- **IaC:** Terraform with GCS state backend

### External Services

- **Google OAuth:** User authentication via NextAuth.js
- **Limitless TCG:** Tournament data source
- **TCGdex:** Card data source

### Scheduled Jobs

| Job          | Schedule        | Purpose                       |
| ------------ | --------------- | ----------------------------- |
| discover-en  | Daily 6 AM UTC  | Discover English tournaments  |
| discover-jp  | Daily 7 AM UTC  | Discover Japanese tournaments |
| compute-meta | Daily 8 AM UTC  | Meta snapshot generation      |
| sync-cards   | Sunday 3 AM UTC | Card database sync            |

---

_These diagrams are designed to render in GitHub, VS Code (with Mermaid extension), or any Mermaid-compatible viewer._
