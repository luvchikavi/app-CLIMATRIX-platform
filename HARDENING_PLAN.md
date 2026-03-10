# CLIMATRIX Platform Hardening Plan

> Branch: `fix/platform-hardening`
> Created: 2026-03-11
> Rules: All changes on branch, existing auth untouched, this file tracks progress.

---

## Phase 1 — Critical (Security & Production)

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1.1 | Add rate limiting to login, register, password reset, import endpoints | TODO | Protect against brute force |
| 1.2 | Validate SECRET_KEY is not the default in production | TODO | Fail-fast on startup |
| 1.3 | Add file upload size limits to import endpoints | TODO | Prevent abuse |

## Phase 2 — High (Architecture & Reliability)

| # | Task | Status | Notes |
|---|------|--------|-------|
| 2.1 | Add Next.js middleware for route protection | TODO | Replace useEffect auth checks |
| 2.2 | Fix N+1 queries in reports endpoint (use selectinload) | TODO | Performance |
| 2.3 | Simplify token management (single source of truth) | TODO | Remove dual-storage |
| 2.4 | Fix API base URL mismatch (.env.example vs api.ts default) | TODO | Developer experience |

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
| | | |
