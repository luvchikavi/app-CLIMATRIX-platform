# CLIMATRIX Deployment Guide

## Production Architecture

```
┌─────────────────┐     ┌─────────────────┐
│   Vercel         │────▶│   Railway        │
│   (Frontend)     │     │   (Backend)      │
│   climatrix.io   │     │   Railway URL    │
└─────────────────┘     └────────┬─────────┘
                                 │
                   ┌─────────────┼─────────────┐
                   │             │             │
              ┌────▼────┐  ┌────▼────┐  ┌─────▼─────┐
              │PostgreSQL│  │  Redis  │  │ S3 / R2   │
              │(Railway) │  │(Railway)│  │(Optional) │
              └──────────┘  └─────────┘  └───────────┘
```

---

## Railway Backend Deployment

### 1. Create Railway Project

1. Go to [railway.app](https://railway.app)
2. Click "New Project"
3. Name it `climatrix-prod`

### 2. Add PostgreSQL

1. Click "Add Service" → "Database" → "PostgreSQL"
2. Note the `DATABASE_URL` from the Variables tab

### 3. Add Redis

1. Click "Add Service" → "Database" → "Redis"
2. Note the `REDIS_URL` from the Variables tab

### 4. Deploy Backend

1. Click "Add Service" → "GitHub Repo"
2. Select the `climatrix` repository
3. Set root directory to `platform/backend`
4. Configure environment variables (see [Environment Variables Reference](#environment-variables-reference) below)

### 5. Initialize Database

After first deployment, use the Railway CLI:

```bash
# Run Alembic migrations
railway run alembic upgrade head

# Seed emission factors and reference data
railway run python -m app.cli db seed

# Seed Scope 3 reference data (airports, distances)
railway run python -m app.cli db seed-scope3-reference

# Create the first super-admin user (interactive prompts)
railway run python -m app.cli db create-superuser
```

### 6. Configure Custom Domain (Optional)

1. Go to Settings → Networking
2. Add custom domain: e.g. `api.climatrix.io`
3. Update DNS records as instructed

---

## Vercel Frontend Deployment

### 1. Import Project

1. Go to [vercel.com](https://vercel.com)
2. Click "Add New Project"
3. Import `climatrix` repository
4. Set root directory to `platform/frontend`

### 2. Configure Environment

```
NEXT_PUBLIC_API_URL=https://<your-railway-url>/api
```

For Google OAuth (optional):
```
NEXT_PUBLIC_GOOGLE_CLIENT_ID=<your-google-client-id>
```

### 3. Deploy

Vercel automatically deploys on push to the main branch. Preview deploys are created for PRs.

### 4. Configure Custom Domain

1. Go to Settings → Domains
2. Add `climatrix.io` (or `app.climatrix.io`)
3. Update DNS records as instructed

---

## Pre-Launch Checklist

Use this checklist before opening the platform to external users.

### Infrastructure

- [ ] Railway service is running (green status)
- [ ] PostgreSQL provisioned on Railway (not SQLite)
- [ ] Redis provisioned on Railway
- [ ] Vercel project linked to correct repo/branch
- [ ] Custom domains configured (if applicable) with SSL

### Environment Variables (Railway)

- [ ] `DATABASE_URL` — set automatically by Railway PostgreSQL add-on
- [ ] `REDIS_URL` — set automatically by Railway Redis add-on
- [ ] `SECRET_KEY` — **strong random key** (`openssl rand -hex 32`), not the default
- [ ] `ENVIRONMENT=production`
- [ ] `DEBUG=false`
- [ ] `CORS_ORIGINS_STR` — set to production frontend URL(s)
- [ ] `CORS_ALLOW_VERCEL_PREVIEWS=true` — for Vercel preview deploys
- [ ] `FRONTEND_URL` — production frontend URL (for email links)
- [ ] `GOOGLE_CLIENT_ID` — for Google OAuth (if enabled)
- [ ] `ANTHROPIC_API_KEY` — for AI features (optional)
- [ ] `SENTRY_DSN` — for error tracking (optional)
- [ ] `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `STRIPE_PUBLISHABLE_KEY` — for billing (optional)
- [ ] `STRIPE_PRICE_ID_STARTER`, `STRIPE_PRICE_ID_PROFESSIONAL`, `STRIPE_PRICE_ID_ENTERPRISE` — Stripe price IDs
- [ ] SMTP settings — for password reset emails and invitations (optional)
- [ ] S3/R2 settings — for persistent file storage (optional, `STORAGE_BACKEND=s3`)

### Environment Variables (Vercel)

- [ ] `NEXT_PUBLIC_API_URL` — points to the Railway backend URL (with `/api` suffix)
- [ ] `NEXT_PUBLIC_GOOGLE_CLIENT_ID` — matches backend `GOOGLE_CLIENT_ID`

### Database

- [ ] Alembic migrations run successfully: `railway run alembic upgrade head`
- [ ] Reference data seeded: `railway run python -m app.cli db seed`
- [ ] Emission factors present in DB (200+ entries)
- [ ] Super-admin user created: `railway run python -m app.cli db create-superuser`

### Functional Verification

- [ ] `GET /health` returns `{"status": "healthy"}` with correct version
- [ ] Frontend loads at production URL (no blank page / JS errors)
- [ ] Registration flow: new user → creates org → shows onboarding wizard
- [ ] Login flow: email/password works
- [ ] Google OAuth: "Continue with Google" completes and redirects to dashboard
- [ ] Onboarding wizard: all 6 steps complete without errors
- [ ] Dashboard: renders charts (may show "no data" for fresh accounts)
- [ ] Enter a Scope 1 activity via wizard → emission calculated → appears on dashboard
- [ ] Upload Excel template → import processed → activities created
- [ ] Reports page: all tabs load, CSV/PDF export downloads files
- [ ] Modules page: GHG active, locked modules show upgrade CTA
- [ ] Settings: org info editable, user invitations work
- [ ] CORS: no preflight errors in browser console

### Security

- [ ] `SECRET_KEY` is not the default development value
- [ ] No hardcoded passwords in source code
- [ ] Swagger docs disabled (`/docs` returns 404 in production)
- [ ] `DEBUG=false` in production
- [ ] CORS restricted to known origins (not `*`)

---

## Smoke Test Script

Run the automated smoke test against any environment:

```bash
# Against local dev
python scripts/smoke_test.py

# Against production
python scripts/smoke_test.py --base-url https://<your-railway-url>

# With specific test credentials
python scripts/smoke_test.py \
  --base-url https://<your-railway-url> \
  --email test@example.com \
  --password YourPassword123!

# Specify CORS origin to test
python scripts/smoke_test.py \
  --base-url https://<your-railway-url> \
  --origin https://climatrix.io
```

The smoke test covers:
1. Health endpoint connectivity
2. Root endpoint
3. CORS preflight headers
4. Environment detection (production vs dev)
5. Reference data availability
6. User registration + login
7. Authenticated endpoints (me, organization)
8. Emission factors seeded
9. Billing config
10. Period creation
11. Activities listing
12. Reports summary

---

## Health Checks

### Backend
```bash
curl https://<your-railway-url>/health
# Expected: {"status": "healthy", "version": "3.1.0", "environment": "production"}
```

### Frontend
Visit the production URL — should load the landing page with login/register options.

---

## Monitoring

### Railway
- View real-time logs in Railway dashboard
- Health checks configured via `railway.toml` at `/health`
- Auto-restart on failure (max 10 retries)

### Vercel
- View deployment logs in Vercel dashboard
- Analytics available in dashboard
- Sentry integration for error tracking (if `SENTRY_DSN` is configured)

---

## Rollback

### Railway
```bash
railway rollback  # Roll back to previous deployment
```

### Vercel
Go to Deployments → Select previous deployment → "Promote to Production"

---

## SSL/TLS

Both Railway and Vercel provide automatic SSL certificates for custom domains.

---

## Environment Variables Reference

### Required (Production)

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@host:5432/db` |
| `REDIS_URL` | Redis connection string | `redis://default:pass@host:6379` |
| `SECRET_KEY` | JWT signing key | `openssl rand -hex 32` |
| `ENVIRONMENT` | Deployment environment | `production` |
| `CORS_ORIGINS_STR` | Allowed frontend origins | `https://climatrix.io` |
| `FRONTEND_URL` | Frontend URL for email links | `https://climatrix.io` |

### Authentication

| Variable | Default | Description |
|----------|---------|-------------|
| `ALGORITHM` | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Access token TTL |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Refresh token TTL |
| `GOOGLE_CLIENT_ID` | _(empty)_ | Google OAuth client ID |
| `CORS_ALLOW_VERCEL_PREVIEWS` | `true` | Allow `*.vercel.app` origins |

### Optional Services

| Variable | Default | Description |
|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | _(empty)_ | Claude AI for smart extraction |
| `SENTRY_DSN` | _(empty)_ | Error tracking |
| `SMTP_HOST` | _(empty)_ | Email server for invitations/resets |
| `STORAGE_BACKEND` | `local` | `local` or `s3` for file uploads |
| `STRIPE_SECRET_KEY` | _(empty)_ | Stripe billing |

### Stripe Billing

| Variable | Description |
|----------|-------------|
| `STRIPE_SECRET_KEY` | API secret key |
| `STRIPE_PUBLISHABLE_KEY` | Client-side publishable key |
| `STRIPE_WEBHOOK_SECRET` | Webhook signature verification |
| `STRIPE_PRICE_ID_STARTER` | Starter plan price ID |
| `STRIPE_PRICE_ID_PROFESSIONAL` | Professional plan price ID |
| `STRIPE_PRICE_ID_ENTERPRISE` | Enterprise plan price ID |

### S3 / Cloudflare R2 Storage

| Variable | Default | Description |
|----------|---------|-------------|
| `S3_BUCKET_NAME` | _(empty)_ | Bucket name |
| `S3_REGION` | `auto` | AWS region or `auto` for R2 |
| `S3_ENDPOINT_URL` | _(empty)_ | Custom endpoint for R2 |
| `S3_ACCESS_KEY_ID` | _(empty)_ | Access key |
| `S3_SECRET_ACCESS_KEY` | _(empty)_ | Secret key |

### Email (SMTP)

| Variable | Default | Description |
|----------|---------|-------------|
| `SMTP_HOST` | _(empty)_ | SMTP server hostname |
| `SMTP_PORT` | `587` | SMTP port |
| `SMTP_USER` | _(empty)_ | SMTP username |
| `SMTP_PASSWORD` | _(empty)_ | SMTP password |
| `SMTP_FROM_EMAIL` | `noreply@climatrix.io` | Sender email |
| `SMTP_FROM_NAME` | `CLIMATRIX` | Sender display name |
| `SMTP_USE_TLS` | `true` | Use TLS |
| `PASSWORD_RESET_TOKEN_EXPIRE_MINUTES` | `30` | Reset token TTL |

---

## Data Migration

If migrating from an existing CLIMATRIX instance:

```bash
# On the OLD system — export data
python scripts/export_data.py --output data_export.json

# Copy the file to the new system, then import
railway run python scripts/import_data.py --input data_export.json
```
