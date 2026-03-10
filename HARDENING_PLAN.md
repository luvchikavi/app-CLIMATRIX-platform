# CLIMATRIX Platform Hardening Plan

> Branch: `fix/platform-hardening`
> Created: 2026-03-11
> Rules: All changes on branch, existing auth untouched, this file tracks progress.

---

## Phase 1 — Critical (Security & Production)

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1.1 | Add rate limiting to login, register, password reset, import endpoints | DONE | slowapi, configurable limits per endpoint |
| 1.2 | Validate SECRET_KEY is not the default in production | DONE | RuntimeError in prod/staging, warning in dev |
| 1.3 | Add file upload size limits to import endpoints | DONE | 50 MB default, configurable, 413 on exceed |

## Phase 2 — High (Architecture & Reliability)

| # | Task | Status | Notes |
|---|------|--------|-------|
| 2.1 | Add Next.js middleware for route protection | DONE | Cookie flag + middleware redirect, existing auth untouched |
| 2.2 | Fix N+1 queries in reports endpoint (use selectinload) | SKIPPED | Already uses explicit JOINs, no N+1 issue |
| 2.3 | Simplify token management (single source of truth) | DONE | Removed duplicate auth_token localStorage, Zustand is single source |
| 2.4 | Fix API base URL mismatch (.env.example vs api.ts default) | DONE | Both now default to localhost:8000/api |

## Phase 3 — Medium (Code Quality & UX)

| # | Task | Status | Notes |
|---|------|--------|-------|
| 3.1 | Refactor large router files (reports.py, import_data.py) into services | TODO | Maintainability |
| 3.2 | Persist onboarding completion in backend | TODO | Survives localStorage clear |
| 3.3 | Code-split recharts (lazy load on dashboard/reports only) | TODO | Bundle size |
| 3.4 | Improve accessibility (ARIA labels, focus management on modals) | TODO | A11y compliance |

## Phase 4 — Infrastructure (from original Phase 3)

| # | Task | Status | Notes |
|---|------|--------|-------|
| 4.1 | S3/R2 file storage migration | TODO | Move from local uploads/ |
| 4.2 | Alembic migration chain finalization | TODO | Clean migration history |
| 4.3 | Stripe billing configuration | TODO | Payment integration |
| 4.4 | Add CI/CD pipeline (GitHub Actions) | TODO | Automated tests + deploy |
| 4.5 | Deployment audit | TODO | Final production checklist |

---

## Changelog

| Date | Task | Description |
|------|------|-------------|
| 2026-03-11 | 1.1 | Rate limiting via slowapi: login/register 10/5 per min, password reset 5/min, imports 20/min. Redis in prod, in-memory dev. |
| 2026-03-11 | 1.2 | SECRET_KEY validation: RuntimeError on startup if default key used in production/staging. Warning in dev. |
| 2026-03-11 | 1.3 | File upload size limit: 50 MB default (configurable via MAX_UPLOAD_SIZE_MB). Returns 413 on exceed. Applied to all 9 import endpoints. |
| 2026-03-11 | 2.1 | Next.js middleware: cookie flag `climatrix_auth` set on login/register, middleware redirects to `/` if missing on protected routes. |
| 2026-03-11 | 2.2 | SKIPPED: Reports already use explicit JOINs (select Activity, Emission).join()), no N+1 issue found. |
| 2026-03-11 | 2.3 | Token simplified: removed duplicate `auth_token` localStorage from ApiClient. Zustand `auth-storage` is now the single source of truth, synced via TokenSync + onRehydrate. |
| 2026-03-11 | 2.4 | API base URL aligned: api.ts default and .env.example both point to `http://localhost:8000/api`. |
