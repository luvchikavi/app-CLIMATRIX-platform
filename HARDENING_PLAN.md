# CLIMATRIX Platform Hardening Plan

> Branch: `fix/platform-hardening`
> Created: 2026-03-11
> Rules: All changes on branch, existing auth untouched, this file tracks progress.

---

## Deployment Architecture

| Environment | Provider | Trigger |
|-------------|----------|---------|
| Production backend | **Railway** (Nixpacks) | Push to `main` → auto-deploy |
| Production frontend | **Vercel** | Push to `main` → auto-deploy |
| Preview frontend | **Vercel** | Push to any branch → preview deploy |
| CI (tests/lint) | **GitHub Actions** | Push + PR → run checks |

---

## Phase 1 — Critical (Security & Production)

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1.1 | Add rate limiting to auth and import endpoints | DONE | slowapi, configurable limits per endpoint |
| 1.2 | Validate SECRET_KEY is not default in production | DONE | RuntimeError in prod/staging, warning in dev |
| 1.3 | Add file upload size limits to import endpoints | DONE | 50 MB default, configurable, 413 on exceed |

## Phase 2 — High (Architecture & Reliability)

| # | Task | Status | Notes |
|---|------|--------|-------|
| 2.1 | Next.js middleware for route protection | DONE | Cookie flag + middleware redirect |
| 2.2 | Fix N+1 queries in reports endpoint | SKIPPED | Already uses explicit JOINs |
| 2.3 | Simplify token management | DONE | Removed duplicate localStorage, single source |
| 2.4 | Fix API base URL mismatch | DONE | Both default to localhost:8000/api |

## Phase 3 — Medium (Code Quality & UX)

| # | Task | Status | Notes |
|---|------|--------|-------|
| 3.1 | Refactor large router files into services | DEFERRED | High-risk, better done incrementally |
| 3.2 | Persist onboarding completion in backend | DONE | New User.onboarding_completed field + PATCH endpoint + migration |
| 3.3 | Code-split recharts | SKIPPED | Only used in 3 pages, Next.js auto code-splits per page |
| 3.4 | Improve accessibility (modals) | DONE | role="dialog" aria-modal aria-label on 9 modals across 6 files |

## Phase 4 — Infrastructure

| # | Task | Status | Notes |
|---|------|--------|-------|
| 4.1 | S3/R2 file storage | READY | Code complete, needs credentials in env vars |
| 4.2 | Alembic migration chain | DONE | Clean linear chain of 13+1 migrations |
| 4.3 | Stripe billing | READY | Code complete, needs Stripe keys + webhook setup |
| 4.4 | GitHub Actions CI pipeline | DONE | 4 jobs: backend lint+test, frontend lint+build |
| 4.5 | Deployment audit | DONE | See checklist below |

---

## Deployment Audit Checklist

### Backend (Railway)
- [x] Auto-deploy on push to main
- [x] Health check at /health
- [x] Auto-restart on failure (max 10 retries)
- [x] Migrations run before server start (migrate.py + alembic upgrade head)
- [x] SECRET_KEY validated on startup (1.2)
- [x] Rate limiting on sensitive endpoints (1.1)
- [x] File upload size limits (1.3)
- [ ] Set ENVIRONMENT=production in Railway env vars
- [ ] Set unique SECRET_KEY in Railway env vars
- [ ] Configure Redis URL for rate limiting + task queue
- [ ] Configure S3/R2 credentials for file storage (4.1)
- [ ] Configure Stripe keys + webhook (4.3)
- [ ] Configure SMTP for email (password reset, invitations)

### Frontend (Vercel)
- [x] Auto-deploy on push to main
- [x] Preview deploys on branches
- [x] Sentry integration for error tracking
- [x] Route protection via middleware (2.1)
- [x] NEXT_PUBLIC_API_URL points to Railway backend
- [ ] Verify NEXT_PUBLIC_GOOGLE_CLIENT_ID is set

### CI/CD (GitHub Actions)
- [x] Backend linting (ruff + black)
- [x] Backend tests (29 tests, in-memory SQLite)
- [x] Frontend linting (eslint)
- [x] Frontend build + TypeScript check

---

## Changelog

| Date | Task | Description |
|------|------|-------------|
| 2026-03-11 | 1.1 | Rate limiting via slowapi: login 10/min, register 5/min, password reset 5/min, imports 20/min |
| 2026-03-11 | 1.2 | SECRET_KEY validation: RuntimeError in production, warning in dev |
| 2026-03-11 | 1.3 | File upload size limit: 50 MB default, 413 on exceed, all 9 import endpoints |
| 2026-03-11 | 2.1 | Next.js middleware: cookie flag on login, redirect unauthenticated users |
| 2026-03-11 | 2.2 | SKIPPED: Reports already use explicit JOINs |
| 2026-03-11 | 2.3 | Token simplified: removed duplicate localStorage, Zustand is single source |
| 2026-03-11 | 2.4 | API base URL aligned to localhost:8000/api |
| 2026-03-11 | 3.2 | Onboarding persisted: User.onboarding_completed field + PATCH /auth/me/onboarding-complete + Alembic migration |
| 2026-03-11 | 3.3 | SKIPPED: recharts only in 3 pages, Next.js auto code-splits |
| 2026-03-11 | 3.4 | Accessibility: role="dialog" aria-modal="true" aria-label on 9 modals in 6 files |
| 2026-03-11 | 4.2 | Alembic: clean chain of 14 migrations confirmed |
| 2026-03-11 | 4.4 | GitHub Actions CI: 4 parallel jobs (lint+test+build) |
| 2026-03-11 | 4.1 | READY: S3/R2 storage code complete, needs env credentials |
| 2026-03-11 | 4.3 | READY: Stripe billing code complete, needs keys + webhook |
| 2026-03-11 | 4.5 | Deployment audit: checklist documented above |
