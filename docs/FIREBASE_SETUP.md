# Firebase Setup Guide

This guide walks through setting up Firebase Authentication for TrainerLab.

## Prerequisites

- GCP account with billing enabled
- Access to GCP Console
- Project repository cloned locally

## Step 1: Create Firebase Project

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Click **Add project**
3. Enter project name: `trainerlab` (or `trainerlab-prod` for production)
4. Choose to enable Google Analytics (optional for MVP)
5. Select existing GCP project or create new
6. Click **Create project**

## Step 2: Enable Authentication

1. In Firebase Console, go to **Build > Authentication**
2. Click **Get started**
3. Under **Sign-in method** tab, enable:

### Google Provider

1. Click **Google**
2. Toggle **Enable**
3. Set project support email
4. Click **Save**

### Email/Password Provider

1. Click **Email/Password**
2. Toggle **Enable**
3. Optionally enable **Email link (passwordless sign-in)**
4. Click **Save**

## Step 3: Configure Authorized Domains

1. Go to **Authentication > Settings > Authorized domains**
2. Add the following domains:
   - `localhost` (already present)
   - `trainerlab.io`
   - `*.trainerlab.io` (for subdomains)
   - Your Cloud Run domain (e.g., `trainerlab-web-xxxxx-uc.a.run.app`)

## Step 4: Get Web App Configuration

1. Go to **Project settings** (gear icon)
2. Scroll to **Your apps** section
3. Click **Add app** > **Web** (</>)
4. Register app with nickname: `trainerlab-web`
5. Copy the Firebase config object:

```javascript
const firebaseConfig = {
  apiKey: "...",
  authDomain: "...",
  projectId: "...",
  storageBucket: "...",
  messagingSenderId: "...",
  appId: "...",
};
```

6. Add these values to `apps/web/.env.local`:

```bash
NEXT_PUBLIC_FIREBASE_API_KEY=your-api-key
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
NEXT_PUBLIC_FIREBASE_PROJECT_ID=your-project-id
```

## Step 5: Configure Backend Authentication (ADC)

Firebase Admin SDK uses [Application Default Credentials (ADC)](https://cloud.google.com/docs/authentication/application-default-credentials) - no JSON key files needed.

### Local Development

1. Install gcloud CLI if not already installed
2. Run:

```bash
gcloud auth application-default login
```

3. Set the project ID in `apps/api/.env`:

```bash
FIREBASE_PROJECT_ID=your-project-id
```

### Production (GCP Cloud Run)

Cloud Run automatically uses ADC with the service's attached IAM service account. Just ensure:

1. The Cloud Run service has a service account attached (default or custom)
2. That service account has the **Firebase Admin SDK Administrator Service Agent** role (or at minimum `firebaseauth.users.get` permission)
3. `FIREBASE_PROJECT_ID` is set in Cloud Run environment variables

## Step 6: Update Environment Files

### Frontend (`apps/web/.env.local`)

```bash
NEXT_PUBLIC_FIREBASE_API_KEY=your-api-key
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
NEXT_PUBLIC_FIREBASE_PROJECT_ID=your-project-id
```

### Backend (`apps/api/.env`)

```bash
FIREBASE_PROJECT_ID=your-project-id
```

## Verification Checklist

- [ ] Firebase project created
- [ ] Google auth provider enabled
- [ ] Email/Password auth provider enabled
- [ ] Authorized domains configured
- [ ] Web app registered
- [ ] Frontend env vars set
- [ ] `gcloud auth application-default login` run (local dev)
- [ ] Backend `FIREBASE_PROJECT_ID` set

## Security Notes

1. **Use ADC, not JSON keys** - ADC is more secure and easier to manage than downloading service account keys
2. **API keys are safe to expose** - Firebase web API keys are meant to be public; security is enforced via Firebase Security Rules and authorized domains
3. **Use environment-specific projects** - Consider separate Firebase projects for dev/staging/prod

## Next Steps

After completing this setup:

1. Implement Firebase Admin SDK in backend (#134)
2. Create auth middleware for FastAPI (#135)
3. Configure Firebase client in frontend (#137)
4. Create AuthProvider context (#138)
