# TrainerLab Deployment Guide

## Architecture Overview

- **Frontend**: `trainerlab.io` → Vercel (Next.js)
- **API**: `api.trainerlab.io` → GCP Cloud Run (FastAPI)
- **Database**: GCP Cloud SQL (PostgreSQL)
- **Domain**: `trainerlab.io`

## DNS Configuration

### Required DNS Records

Add the following DNS records in your domain registrar (e.g., Cloudflare, Route53):

```
Type    Name    Value                   TTL
CNAME   api     ghs.googlehosted.com    Auto
```

For the frontend (`trainerlab.io`), Vercel will provide specific DNS records during deployment (typically A and CNAME records).

### Verify DNS Propagation

```bash
# Check API subdomain
dig api.trainerlab.io

# Expected output should show:
# api.trainerlab.io.  300  IN  CNAME  ghs.googlehosted.com.
```

## API Deployment (Cloud Run)

### Prerequisites

1. Terraform installed
2. `gcloud` CLI authenticated
3. Domain ownership verified in GCP

### Deploy

```bash
cd terraform
terraform apply -var-file=environments/prod.tfvars
```

### Verify Deployment

```bash
# Check service health
curl https://api.trainerlab.io/api/v1/health

# Test with operations service account
./scripts/test-production-scrapers.sh --pipeline=discover-en --confirm
```

### Certificate Provisioning

After DNS records are configured, Cloud Run will automatically provision a managed SSL certificate. This typically takes 15-60 minutes. Check status:

```bash
gcloud run domain-mappings describe api.trainerlab.io \
  --region=us-west1 \
  --platform=managed \
  --format=json | jq '.status.conditions'
```

## Frontend Deployment (Vercel)

### Initial Setup

1. **Connect Repository**
   - Go to [vercel.com](https://vercel.com)
   - Click "Add New Project"
   - Import `dtsong/trainerlab` from GitHub

2. **Configure Build Settings**
   - Framework Preset: `Next.js`
   - Root Directory: `apps/web`
   - Build Command: `pnpm build` (default)
   - Output Directory: `.next` (default)

3. **Environment Variables**
   Add these in Vercel project settings:

   ```
   NEXT_PUBLIC_API_URL=https://api.trainerlab.io
   NEXTAUTH_URL=https://www.trainerlab.io
   NEXTAUTH_SECRET=<openssl rand -base64 32>
   AUTH_GOOGLE_ID=<google-oauth-client-id>
   AUTH_GOOGLE_SECRET=<google-oauth-client-secret>
   ```

4. **Custom Domain**
   - Go to Project Settings → Domains
   - Add `trainerlab.io` and `www.trainerlab.io`
   - Follow Vercel's DNS configuration instructions
   - Vercel will automatically provision SSL certificates

### Continuous Deployment

Vercel automatically deploys:

- **Production**: on pushes to `main` branch
- **Preview**: on pull requests

### Manual Deploy

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
cd apps/web
vercel --prod
```

## Update CORS Origins

After frontend is deployed, update CORS settings:

```bash
cd terraform
# Edit environments/prod.tfvars to ensure cors_origins includes trainerlab.io
terraform apply -var-file=environments/prod.tfvars
```

## Verification Checklist

After deployment, verify:

- [ ] DNS records configured and propagated
- [ ] API accessible at `https://api.trainerlab.io/api/v1/health`
- [ ] SSL certificate provisioned for API (check browser lock icon)
- [ ] Frontend deployed to `https://trainerlab.io`
- [ ] SSL certificate provisioned for frontend
- [ ] Frontend can communicate with API (check browser console)
- [ ] Operations script works with service account
- [ ] Scheduled jobs are running (check Cloud Scheduler)

## Troubleshooting

### API Domain Mapping Issues

If the API domain mapping fails:

```bash
# Check domain mapping status
gcloud run domain-mappings describe api.trainerlab.io \
  --region=us-west1 \
  --platform=managed

# Verify domain ownership in GCP Console
# https://console.cloud.google.com/run/domains
```

### CORS Errors

If frontend shows CORS errors:

1. Verify `cors_origins` in `terraform/environments/prod.tfvars` includes your frontend domain
2. Apply Terraform changes
3. Wait 1-2 minutes for Cloud Run to update
4. Hard refresh browser (Cmd+Shift+R)

### Certificate Provisioning Stuck

If SSL certificate provisioning is stuck:

1. Verify DNS records are correct: `dig api.trainerlab.io`
2. Check DNS propagation: `dig @8.8.8.8 api.trainerlab.io`
3. Wait 15-60 minutes for propagation
4. Check Cloud Run domain mapping status

### Frontend Build Failures

If Vercel build fails:

1. Check build logs in Vercel dashboard
2. Verify environment variables are set
3. Test build locally: `cd apps/web && pnpm build`
4. Check for TypeScript errors or missing dependencies

## Rollback

### API Rollback

```bash
# Deploy previous image
cd terraform
terraform apply -var-file=environments/prod.tfvars -var="api_image=<previous-image-uri>"
```

### Frontend Rollback

In Vercel dashboard:

1. Go to Deployments
2. Find previous successful deployment
3. Click "..." menu → "Promote to Production"

## Monitoring

- **API Logs**: GCP Console → Cloud Run → trainerlab-api → Logs
- **Frontend Logs**: Vercel Dashboard → Deployments → View Function Logs
- **Database Metrics**: GCP Console → SQL → trainerlab-db
- **Scheduled Jobs**: GCP Console → Cloud Scheduler

## Cost Estimates

Current infrastructure costs (approximate):

- Cloud Run: $5-20/month (depends on traffic)
- Cloud SQL: $7/month (db-f1-micro)
- Cloud Scheduler: $0.10/month
- Vercel: Free (Hobby plan)
- Domain: $12/year

Total: ~$15-30/month
