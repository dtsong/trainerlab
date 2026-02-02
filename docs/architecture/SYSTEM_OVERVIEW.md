# System Overview

> Executive-level view of TrainerLab's cloud infrastructure and external integrations.

## Overview

TrainerLab is a competitive intelligence platform for Pokemon TCG, built on Google Cloud Platform. The system consists of a Next.js frontend, FastAPI backend, PostgreSQL database with vector search capabilities, and automated data pipelines that continuously gather tournament intelligence.

## Diagram

```mermaid
flowchart TB
    subgraph Users["Users"]
        Player["Players & Coaches"]
        Creator["Content Creators"]
    end

    subgraph Frontend["Frontend (trainerlab.io)"]
        Web["Next.js 14+<br/>App Router"]
    end

    subgraph GCP["Google Cloud Platform"]
        subgraph CloudRun["Cloud Run"]
            API["FastAPI API<br/>api.trainerlab.io"]
        end

        subgraph CloudSQL["Cloud SQL (Private VPC)"]
            DB[("PostgreSQL 16<br/>+ pgvector")]
        end

        subgraph Scheduler["Cloud Scheduler"]
            Jobs["4 Pipeline Jobs<br/>Daily/Weekly"]
        end

        subgraph Supporting["Supporting Services"]
            Secrets["Secret Manager"]
            Registry["Artifact Registry"]
        end
    end

    subgraph External["External Services"]
        Firebase["Firebase Auth"]
        Limitless["Limitless TCG<br/>Tournament Data"]
        TCGdex["TCGdex<br/>Card Data"]
    end

    subgraph CICD["CI/CD"]
        GitHub["GitHub Actions"]
        Terraform["Terraform<br/>GCS State"]
    end

    %% User flows
    Player --> Web
    Creator --> Web
    Web --> API
    Web -.->|"Auth"| Firebase

    %% API connections
    API --> DB
    API --> Secrets
    API -.->|"Verify tokens"| Firebase
    API -->|"Scrape"| Limitless
    API -->|"Sync"| TCGdex

    %% Scheduler
    Jobs -->|"OIDC Auth"| API

    %% CI/CD
    GitHub -->|"OIDC"| Registry
    GitHub -->|"Deploy"| API
    Terraform -.->|"Manage"| GCP

    %% Styling
    classDef gcp fill:#4285f4,stroke:#1a73e8,color:#fff
    classDef external fill:#34a853,stroke:#1e8e3e,color:#fff
    classDef user fill:#fbbc04,stroke:#f9ab00,color:#000
    classDef frontend fill:#ea4335,stroke:#c5221f,color:#fff

    class API,DB,Jobs,Secrets,Registry gcp
    class Firebase,Limitless,TCGdex external
    class Player,Creator user
    class Web frontend
```

## Key Components

| Component                 | Description                                                     |
| ------------------------- | --------------------------------------------------------------- |
| **Next.js Frontend**      | React-based web application with App Router, deployed to Vercel |
| **FastAPI API**           | Python backend handling business logic, deployed to Cloud Run   |
| **PostgreSQL + pgvector** | Database with vector similarity search for card embeddings      |
| **Cloud Scheduler**       | Automated pipeline execution on defined schedules               |
| **Firebase Auth**         | User authentication with ID token verification                  |
| **Artifact Registry**     | Docker image storage with 10-version retention policy           |
| **Secret Manager**        | Secure storage for database credentials and API keys            |
| **Terraform**             | Infrastructure as code with GCS state backend                   |

## Notes

- Cloud SQL is accessible only via private VPC connection from Cloud Run
- All Cloud Run services use HTTPS with managed certificates
- GitHub Actions authenticates to GCP via Workload Identity Federation (keyless)
- Scheduled jobs use OIDC tokens for authenticated API calls
