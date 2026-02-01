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

## Step 5: Create Service Account for Backend

1. Go to **Project settings > Service accounts**
2. Click **Generate new private key**
3. Download the JSON file
4. **IMPORTANT:** Never commit this file to git

### Local Development

Save the JSON file as `firebase-service-account.json` in a secure location and set:

```bash
# In apps/api/.env
GOOGLE_APPLICATION_CREDENTIALS=/path/to/firebase-service-account.json
FIREBASE_PROJECT_ID=your-project-id
```

### Production (GCP Cloud Run)

1. Store the service account JSON in **Secret Manager**
2. Mount as a secret in Cloud Run
3. Set `GOOGLE_APPLICATION_CREDENTIALS` to the mount path

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
GOOGLE_APPLICATION_CREDENTIALS=/path/to/firebase-service-account.json
```

## Verification Checklist

- [ ] Firebase project created
- [ ] Google auth provider enabled
- [ ] Email/Password auth provider enabled
- [ ] Authorized domains configured
- [ ] Web app registered
- [ ] Frontend env vars set
- [ ] Service account JSON downloaded
- [ ] Backend env vars set
- [ ] Service account JSON added to `.gitignore`

## Security Notes

1. **Never commit service account JSON** - it grants admin access to your Firebase project
2. **API keys are safe to expose** - Firebase web API keys are meant to be public; security is enforced via Firebase Security Rules and authorized domains
3. **Use environment-specific projects** - Consider separate Firebase projects for dev/staging/prod

## Next Steps

After completing this setup:

1. Implement Firebase Admin SDK in backend (#134)
2. Create auth middleware for FastAPI (#135)
3. Configure Firebase client in frontend (#137)
4. Create AuthProvider context (#138)
