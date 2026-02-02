# Authentication

> End-to-end authentication flows for users and automated services.

## Overview

TrainerLab implements two distinct authentication flows: Firebase Authentication for end users and OIDC token verification for Cloud Scheduler pipeline jobs. Both flows validate tokens server-side before granting access to protected resources.

## User Authentication Flow

```mermaid
sequenceDiagram
    autonumber
    participant User
    participant Frontend as Next.js Frontend
    participant Firebase as Firebase Auth
    participant API as FastAPI API
    participant DB as PostgreSQL

    User->>Frontend: Navigate to /auth/login
    Frontend->>Firebase: signInWithEmailAndPassword()
    Firebase-->>Frontend: Firebase User + ID Token

    Frontend->>Frontend: Store token in AuthContext

    User->>Frontend: Access protected feature
    Frontend->>API: GET /api/v1/users/me<br/>Authorization: Bearer {idToken}

    API->>Firebase: Verify ID token
    Firebase-->>API: Decoded token (uid, email)

    API->>DB: SELECT * FROM users WHERE firebase_uid = ?
    DB-->>API: User record

    API-->>Frontend: User profile JSON
    Frontend-->>User: Display profile
```

## Service Authentication Flow (Cloud Scheduler)

```mermaid
sequenceDiagram
    autonumber
    participant Scheduler as Cloud Scheduler
    participant GCP as GCP IAM
    participant API as FastAPI API
    participant Pipeline as Pipeline Service
    participant DB as PostgreSQL

    Note over Scheduler: Cron trigger (e.g., 6 AM UTC)

    Scheduler->>GCP: Request OIDC token<br/>for trainerlab-scheduler@
    GCP-->>Scheduler: Signed JWT (OIDC token)

    Scheduler->>API: POST /api/v1/pipeline/scrape-en<br/>Authorization: Bearer {oidcToken}

    API->>GCP: Verify OIDC token signature
    GCP-->>API: Token claims (iss, aud, email)

    API->>API: Validate service account email<br/>matches SCHEDULER_SERVICE_ACCOUNT

    API->>Pipeline: Execute scrape_limitless()
    Pipeline->>DB: INSERT tournaments, placements
    DB-->>Pipeline: Success

    Pipeline-->>API: Pipeline result
    API-->>Scheduler: 200 OK + job summary
```

## Key Components

| Component              | Description                                           |
| ---------------------- | ----------------------------------------------------- |
| **Firebase Auth SDK**  | Client-side authentication in Next.js                 |
| **AuthContext**        | React context managing auth state and token           |
| **Firebase Admin SDK** | Server-side token verification in FastAPI             |
| **OIDC Token**         | Service-to-service authentication for Cloud Scheduler |
| **scheduler_auth.py**  | FastAPI dependency for validating scheduler requests  |

## Authentication Dependencies

```python
# User authentication (dependencies/auth.py)
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    # Verify Firebase ID token
    # Look up user by firebase_uid
    # Return User model

# Scheduler authentication (dependencies/scheduler_auth.py)
async def verify_scheduler_token(
    request: Request,
    settings: Settings = Depends(get_settings)
) -> bool:
    # Verify OIDC token signature
    # Check email matches scheduler SA
    # Return True or raise 401
```

## Protected Endpoints

| Endpoint             | Auth Type | Description             |
| -------------------- | --------- | ----------------------- |
| `/api/v1/users/me`   | User      | Current user profile    |
| `/api/v1/decks/*`    | User      | Deck CRUD operations    |
| `/api/v1/pipeline/*` | Scheduler | Data pipeline execution |

## Token Verification

### User ID Tokens (Firebase)

- Issued by: `https://securetoken.google.com/{project_id}`
- Verified using: Firebase Admin SDK
- Contains: `uid`, `email`, `email_verified`
- Expiry: 1 hour (auto-refreshed by client SDK)

### Service OIDC Tokens (Cloud Scheduler)

- Issued by: `https://accounts.google.com`
- Verified using: Google's public keys
- Contains: `iss`, `aud`, `email`, `exp`
- Audience: Cloud Run service URL
- Expiry: 1 hour

## Notes

- Frontend stores Firebase auth state in React Context, not localStorage
- ID tokens are automatically refreshed by Firebase SDK before expiry
- Scheduler OIDC tokens are generated fresh for each job execution
- Operations service account can also invoke pipelines for manual testing
- All authentication failures return 401 Unauthorized with minimal error details
