# CLIMATRIX Platform - Progress Report

**Version:** 3.1.0
**Last Updated:** 2026-01-29

---

## Current Status: PRODUCTION READY

All core features implemented and deployed to Railway.

---

## Completed Features

### Phase 1: Core GHG Accounting
- [x] User authentication (JWT)
- [x] Organization management
- [x] Reporting periods
- [x] Activity data entry (manual + import)
- [x] Emission calculations (Scope 1, 2, 3)
- [x] Reports & dashboards
- [x] Data export (CSV, JSON)

### Phase 2: CBAM (Carbon Border Adjustment Mechanism)
- [x] CBAM product registry
- [x] Installation management
- [x] Import tracking
- [x] Quarterly reports
- [x] Annual declarations
- [x] EU ETS price integration

### Phase 3: Emission Factor Governance (NEW)
- [x] Approval workflow (draft → pending → approved)
- [x] Version control with history
- [x] Audit trail (who changed what, when)
- [x] Only approved factors used in calculations
- [x] API endpoints for factor management

---

## Emission Factor Database

### Summary: 401 Approved Factors

| Scope | Category | Count | Description |
|-------|----------|-------|-------------|
| 1 | 1.1 | 15 | Stationary Combustion (fuels) |
| 1 | 1.2 | 15 | Mobile Combustion (vehicles) |
| 1 | 1.3 | 39 | Fugitive Emissions (refrigerants) |
| 2 | 2 | 78 | Purchased Electricity |
| 2 | 2.3 | 1 | District Cooling |
| 3 | 3.1 | 65 | Purchased Goods & Services |
| 3 | 3.2 | 7 | Capital Goods |
| 3 | 3.3 | 14 | Fuel & Energy (WTT) |
| 3 | 3.4 | 10 | Upstream Transportation |
| 3 | 3.5 | 48 | Waste in Operations |
| 3 | 3.6 | 17 | Business Travel |
| 3 | 3.7 | 12 | Employee Commuting |
| 3 | 3.8 | 6 | Upstream Leased Assets |
| 3 | 3.9 | 5 | Downstream Transportation |
| 3 | 3.10 | 14 | Processing of Sold Products |
| 3 | 3.11 | 8 | Use of Sold Products |
| 3 | 3.12 | 21 | End-of-Life Treatment |
| 3 | 3.13 | 11 | Downstream Leased Assets |
| 3 | 3.14 | 15 | Franchises |
| **TOTAL** | | **401** | |

### Sources
- DEFRA 2024 (UK Government GHG Conversion Factors)
- IPCC AR6 (GWP values for refrigerants)
- IEA 2024 (International grid factors)
- EPA eGRID 2024 (US grid factors)
- USEEIO 2.0 (Spend-based factors)

---

## Governance Workflow

```
DRAFT → PENDING_APPROVAL → APPROVED
                        ↘ REJECTED

APPROVED → ARCHIVED (when updated)
```

### API Endpoints

| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| GET | /api/emission-factors | All | List all factors |
| GET | /api/emission-factors/pending | Admin | Pending approvals |
| GET | /api/emission-factors/{id} | All | Get factor |
| GET | /api/emission-factors/{id}/history | All | Version history |
| POST | /api/emission-factors | Editor+ | Create factor |
| PUT | /api/emission-factors/{id} | Editor+ | Update factor |
| POST | /api/emission-factors/{id}/submit | Editor+ | Submit for approval |
| POST | /api/emission-factors/{id}/approve | Admin | Approve |
| POST | /api/emission-factors/{id}/reject | Admin | Reject |
| DELETE | /api/emission-factors/{id} | Admin | Archive |

---

## Recent Bug Fixes (2026-01-28/29)

1. **CalculationError class missing** - Added to pipeline.py
2. **Foreign key violation on supplier-specific factors** - Made emission_factor_id nullable
3. **Excel import fuel type mapping** - Fixed column mapping in parser
4. **User passwords** - Updated team user credentials

---

## Deployment

- **Platform:** Railway
- **Database:** PostgreSQL
- **Auto-deploy:** On git push to main

---

## File Structure

```
backend/
├── app/
│   ├── api/
│   │   ├── auth.py
│   │   ├── activities.py
│   │   ├── emission_factors.py    # NEW - Governance API
│   │   ├── import_data.py
│   │   ├── reports.py
│   │   └── ...
│   ├── models/
│   │   ├── core.py
│   │   ├── emission.py            # Updated - Governance fields
│   │   └── cbam.py
│   ├── services/
│   │   ├── calculation/
│   │   │   ├── pipeline.py
│   │   │   └── resolver.py        # Updated - Only approved factors
│   │   └── template_parser/
│   │       └── parser.py
│   ├── data/
│   │   └── emission_factors.py    # 401 factors
│   └── database.py
├── PROGRESS.md                     # This file
└── CORE_DOCS/
    └── SCOPE 1_2DB.md
```

---

## Next Steps (Backlog)

- [ ] Frontend UI for emission factor management
- [ ] Bulk import of emission factors
- [ ] Email notifications for approval workflow
- [ ] Factor comparison reports
- [ ] API rate limiting

---

## Contact

- **Repository:** https://github.com/luvchikavi/app-CLIMATRIX-platform
- **Production:** Railway deployment
