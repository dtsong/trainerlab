# CI/CD & Deployment

> DevOps pipeline and infrastructure management for TrainerLab.

## Overview

TrainerLab uses GitHub Actions for continuous integration and deployment, with keyless authentication to Google Cloud via Workload Identity Federation. Infrastructure is managed declaratively using Terraform with state stored in Google Cloud Storage.

## Diagram

```mermaid
flowchart TB
    subgraph GitHub["GitHub"]
        Repo["Repository<br/>trainerlab"]
        Actions["GitHub Actions<br/>Workflows"]
        OIDC["OIDC Token<br/>JWT"]
    end

    subgraph GCPAuth["GCP Authentication"]
        WIF["Workload Identity<br/>Federation"]
        Pool["Identity Pool<br/>github-actions"]
        SA["Service Account<br/>github-actions@"]
    end

    subgraph GCPServices["GCP Services"]
        Registry["Artifact Registry<br/>trainerlab-api<br/>(10 versions)"]
        CloudRun["Cloud Run<br/>trainerlab-api"]
        Secrets["Secret Manager"]
    end

    subgraph Terraform["Terraform"]
        TFConfig["terraform/<br/>*.tf files"]
        TFState["GCS Backend<br/>trainerlab-tfstate"]
    end

    subgraph Managed["Managed Resources"]
        CloudSQL["Cloud SQL"]
        Scheduler["Cloud Scheduler"]
        VPC["VPC Network"]
        IAM["IAM Policies"]
    end

    %% CI/CD Flow
    Repo -->|"Push/PR"| Actions
    Actions -->|"Request"| OIDC
    OIDC -->|"Verify"| WIF
    WIF --> Pool
    Pool -->|"Impersonate"| SA

    %% Deployment
    SA -->|"Push Image"| Registry
    SA -->|"Deploy"| CloudRun
    Registry -->|"Pull"| CloudRun
    CloudRun --> Secrets

    %% Terraform
    TFConfig -->|"Apply"| TFState
    TFState -.->|"Manage"| Managed
    TFConfig -.->|"Define"| CloudSQL
    TFConfig -.->|"Define"| Scheduler
    TFConfig -.->|"Define"| VPC
    TFConfig -.->|"Define"| IAM

    %% Styling
    classDef github fill:#24292e,stroke:#1b1f23,color:#fff
    classDef auth fill:#fbbc04,stroke:#f9ab00,color:#000
    classDef gcp fill:#4285f4,stroke:#1a73e8,color:#fff
    classDef terraform fill:#7b42bc,stroke:#5c4ee5,color:#fff
    classDef managed fill:#34a853,stroke:#1e8e3e,color:#fff

    class Repo,Actions,OIDC github
    class WIF,Pool,SA auth
    class Registry,CloudRun,Secrets gcp
    class TFConfig,TFState terraform
    class CloudSQL,Scheduler,VPC,IAM managed
```

## Key Components

| Component                        | Description                                          |
| -------------------------------- | ---------------------------------------------------- |
| **GitHub Actions**               | CI/CD workflows for testing, building, and deploying |
| **Workload Identity Federation** | Keyless authentication from GitHub to GCP            |
| **Artifact Registry**            | Docker image storage with 10-version retention       |
| **Cloud Run**                    | Serverless container deployment                      |
| **Terraform**                    | Infrastructure as code for all GCP resources         |
| **GCS State Backend**            | Remote state storage for Terraform                   |

## Deployment Pipeline

```
1. Developer pushes to main branch
2. GitHub Actions workflow triggers
3. Tests run (Python + TypeScript)
4. Docker image built and tagged
5. OIDC token exchanged for GCP credentials
6. Image pushed to Artifact Registry
7. Cloud Run service updated
8. Health check confirms deployment
```

## Terraform Structure

| File                 | Purpose                                        |
| -------------------- | ---------------------------------------------- |
| `main.tf`            | Root module, providers, resource orchestration |
| `variables.tf`       | Input variables with defaults                  |
| `outputs.tf`         | Exported values for reference                  |
| `github_oidc.tf`     | Workload Identity Federation setup             |
| `modules/cloud_run/` | Cloud Run service configuration                |
| `modules/cloud_sql/` | PostgreSQL instance setup                      |
| `modules/scheduler/` | Pipeline job definitions                       |

## Service Accounts

| Account                 | Purpose                                 |
| ----------------------- | --------------------------------------- |
| `github-actions@`       | CI/CD deployments via Workload Identity |
| `trainerlab-api@`       | Cloud Run runtime identity              |
| `trainerlab-scheduler@` | Cloud Scheduler job execution           |
| `trainerlab-ops@`       | Manual operations and testing           |

## Notes

- Workload Identity Federation eliminates the need for long-lived service account keys
- Artifact Registry cleanup policy keeps the 10 most recent images
- Terraform state is stored in GCS with prefix-based separation by environment
- Cloud Run deployments are zero-downtime with automatic rollback on failure
- GitHub repo attribute condition restricts which repositories can authenticate
