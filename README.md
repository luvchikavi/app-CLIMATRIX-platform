# CLIMATRIX

Professional GHG emissions accounting and carbon management platform.

## Overview

CLIMATRIX is a comprehensive carbon accounting platform that helps organizations measure, track, and report their greenhouse gas emissions across all scopes (1, 2, and 3).

## Architecture

```
platform/
├── backend/          # FastAPI backend (Python)
│   ├── app/          # Application code
│   │   ├── api/      # API endpoints
│   │   ├── models/   # Database models
│   │   ├── modules/  # Scope 1, 2, 3 calculations
│   │   ├── services/ # Business logic
│   │   ├── data/     # Emission factors, reference data
│   │   └── cli/      # CLI tools & seeding
│   └── alembic/      # Database migrations
│
├── frontend/         # Next.js frontend (React/TypeScript)
│   ├── src/
│   │   ├── app/      # Next.js pages
│   │   ├── components/ # UI components
│   │   ├── stores/   # Zustand state
│   │   ├── hooks/    # React hooks
│   │   └── lib/      # Utilities
│   └── public/       # Static assets
│
└── docs/             # Documentation
```

## Tech Stack

### Backend
- **Framework**: FastAPI 0.115
- **ORM**: SQLModel + SQLAlchemy
- **Database**: PostgreSQL (production), SQLite (development)
- **Task Queue**: Redis + custom worker
- **AI**: Claude API for intelligent data extraction

### Frontend
- **Framework**: Next.js 16
- **UI Library**: React 19
- **Styling**: Tailwind CSS 4
- **State**: Zustand
- **Data Fetching**: TanStack Query

## Quick Start

### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
# Edit .env with your settings

# Run migrations
alembic upgrade head

# Seed reference data
python -m app.cli.seed
python -m app.cli.seed_scope3_reference

# Start development server
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Copy environment file
cp .env.example .env.local
# Edit .env.local with your settings

# Start development server
npm run dev
```

Visit http://localhost:3000

## Environment Variables

See `.env.example` files in each directory for required configuration.

## Key Features

- **Scope 1 Emissions**: Stationary combustion, mobile combustion, refrigerants, process emissions
- **Scope 2 Emissions**: Location-based and market-based electricity calculations
- **Scope 3 Emissions**: All 15 categories including business travel, employee commuting, purchased goods
- **Excel Import**: Bulk data upload with intelligent column mapping
- **AI-Powered Extraction**: Claude AI for automated data extraction from invoices
- **Reports**: GHG inventory reports, emission summaries, category breakdowns

## API Documentation

When running locally, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Deployment

See [DEPLOYMENT.md](docs/DEPLOYMENT.md) for production deployment instructions.

## License

Proprietary - All rights reserved.
