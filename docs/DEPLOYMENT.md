# CLIMATRIX Deployment Guide

## Production Architecture

```
┌─────────────────┐     ┌─────────────────┐
│   Vercel        │────▶│   Railway       │
│   (Frontend)    │     │   (Backend)     │
│   app.climatrix.io    │   api.climatrix.io
└─────────────────┘     └────────┬────────┘
                                 │
                        ┌────────┴────────┐
                        │                 │
                   ┌────▼────┐      ┌─────▼─────┐
                   │PostgreSQL│      │   Redis   │
                   │(Railway) │      │ (Railway) │
                   └──────────┘      └───────────┘
```

## Railway Backend Deployment

### 1. Create New Railway Project

1. Go to [railway.app](https://railway.app)
2. Click "New Project"
3. Name it `climatrix-prod`

### 2. Add PostgreSQL

1. Click "Add Service" → "Database" → "PostgreSQL"
2. Note the `DATABASE_URL` from Variables tab

### 3. Add Redis

1. Click "Add Service" → "Database" → "Redis"
2. Note the `REDIS_URL` from Variables tab

### 4. Deploy Backend

1. Click "Add Service" → "GitHub Repo"
2. Select `climatrix` repository
3. Set root directory to `backend`
4. Configure environment variables:

```
DATABASE_URL=<from PostgreSQL service>
REDIS_URL=<from Redis service>
SECRET_KEY=<generate with: openssl rand -hex 32>
ANTHROPIC_API_KEY=<from Anthropic console>
CORS_ORIGINS_STR=https://app.climatrix.io,https://climatrix.io
DEBUG=false
ENVIRONMENT=production
```

### 5. Run Migrations

After deployment, use Railway CLI:

```bash
railway run alembic upgrade head
railway run python -m app.cli.seed
railway run python -m app.cli.seed_scope3_reference
```

### 6. Configure Custom Domain (Optional)

1. Go to Settings → Networking
2. Add custom domain: `api.climatrix.io`
3. Update DNS records as instructed

## Vercel Frontend Deployment

### 1. Import Project

1. Go to [vercel.com](https://vercel.com)
2. Click "Add New Project"
3. Import `climatrix` repository
4. Set root directory to `frontend`

### 2. Configure Environment

```
NEXT_PUBLIC_API_URL=https://api.climatrix.io
```

### 3. Deploy

Vercel will automatically deploy on push to main branch.

### 4. Configure Custom Domain

1. Go to Settings → Domains
2. Add `app.climatrix.io`
3. Update DNS records as instructed

## Database Initialization

After first deployment:

```bash
# SSH to Railway or use Railway CLI
railway run alembic upgrade head

# Seed emission factors
railway run python -m app.cli.seed

# Seed Scope 3 reference data (airports, distances)
railway run python -m app.cli.seed_scope3_reference
```

## Data Migration from Old System

If migrating from existing CLIMATERIX instance:

```bash
# On OLD system - export data
python scripts/export_data.py --output data_export.json

# Copy file to new system

# On NEW system - import data
railway run python scripts/import_data.py --input data_export.json
```

## Health Checks

### Backend
```bash
curl https://api.climatrix.io/health
# Should return: {"status": "healthy", "version": "3.0.7"}
```

### Frontend
Visit https://app.climatrix.io - should load login page

## Monitoring

### Railway
- View logs in Railway dashboard
- Set up alerts for errors

### Vercel
- View deployment logs
- Analytics available in dashboard

## SSL/TLS

Both Railway and Vercel provide automatic SSL certificates for custom domains.

## Rollback

### Railway
```bash
railway rollback  # Roll back to previous deployment
```

### Vercel
Go to Deployments → Select previous deployment → "Promote to Production"

## Environment Variables Reference

| Variable | Required | Description |
|----------|----------|-------------|
| DATABASE_URL | Yes | PostgreSQL connection string |
| REDIS_URL | Yes | Redis connection string |
| SECRET_KEY | Yes | JWT signing key (generate with openssl) |
| ANTHROPIC_API_KEY | No | For AI features |
| CORS_ORIGINS_STR | Yes | Allowed frontend origins |
| DEBUG | No | Enable debug mode (default: false) |
| ENVIRONMENT | No | deployment environment |
