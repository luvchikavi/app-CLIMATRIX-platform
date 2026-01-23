# CLIMATRIX Task List - Ordered by Priority

## Legend
- **FE** = Frontend (Next.js/React)
- **BE** = Backend (FastAPI/Python)
- **DB** = Database (seed data, migrations)
- **XL** = Excel templates

---

## CRITICAL PRIORITY

### Task 1: Fix Specialized Forms Not Deploying (Scope 1 & 2)
**Type:** FE
**Issue:** Categories 1.1, 1.2, 1.3, 2.1, 2.2, 2.3 still show old small dropdown instead of new specialized forms
**Root Cause:** Vercel may not have deployed, or wizard routing is broken
**Fix:** Debug wizard routing, verify SPECIALIZED_CATEGORIES, ensure forms are imported correctly
**Files:** `frontend/src/components/wizard/index.tsx`, `frontend/src/stores/wizard.ts`

---

### Task 2: Currency Conversion for Spend-Based Calculations
**Type:** BE + FE
**Issue:** 1000 USD and 1000 NIS give same emission result - should be different
**Fix:**
- BE: Add currency conversion when calculating spend-based emissions (convert to USD first)
- FE: Ensure currency is passed to API
**Files:**
- `backend/app/api/activities.py`
- `backend/app/services/calculations.py` (if exists)
- `frontend/src/components/wizard/*Form.tsx` (spend-based forms)

---

### Task 3: Dashboard - Location vs Market Comparison for Scope 2
**Type:** FE + BE
**Issue:** No way to compare location-based vs market-based emissions in dashboard
**Fix:**
- BE: Add API endpoint that returns Scope 2 data grouped by method (location/market)
- FE: Add comparison chart/table to dashboard
**Files:**
- `backend/app/api/reports.py`
- `frontend/src/app/dashboard/page.tsx`
- `frontend/src/components/dashboard/` (new component)

---

### Task 4: Dashboard Drill-Down by Emission Type
**Type:** FE + BE
**Issue:** Clicking on scope should show breakdown (Scope 1 → petrol, diesel, gases; Scope 2 → by country)
**Fix:**
- BE: Add endpoint for emission breakdown by activity_key
- FE: Enhance drill-down modal with proper grouping
**Files:**
- `backend/app/api/reports.py`
- `frontend/src/app/dashboard/page.tsx`
- `frontend/src/components/dashboard/CategoryBreakdown.tsx`

---

### Task 5: Link Imported File to Organization
**Type:** FE + BE
**Issue:** User cannot select which organization to associate imported data with
**Fix:**
- FE: Add organization dropdown to import page
- BE: Accept organization_id parameter in import API
**Files:**
- `frontend/src/app/import/page.tsx`
- `backend/app/api/import_data.py`

---

### Task 6: Import Site Selection Not Working
**Type:** FE + BE
**Issue:** Cannot select site when importing activities
**Fix:** Debug import page, ensure site selector works and passes site_id to API
**Files:**
- `frontend/src/app/import/page.tsx`
- `backend/app/api/import_data.py`

---

### Task 7: Remove Category 1.4
**Type:** FE + BE + DB + XL
**Issue:** Category 1.4 doesn't exist in GHG Protocol
**Fix:**
- FE: Remove from CATEGORIES in wizard store
- BE: Remove any 1.4 references
- DB: Remove any 1.4 emission factors
- XL: Remove from Excel templates
**Files:**
- `frontend/src/stores/wizard.ts`
- `backend/app/data/emission_factors.py`
- Excel templates in `climetrix_v3_files/`

---

### Task 8: Verify Emission Factors Match DEFRA 2024
**Type:** DB
**Issue:** 1.2 diesel/petrol factors may not match DEFRA 2024
**Fix:** Compare current factors with DEFRA 2024 source, update if wrong
**Files:**
- `backend/app/data/emission_factors.py`
- `backend/app/modules/scope_1_2/emission_factors.py`

---

### Task 9: Verify LPG Shows in Results
**Type:** BE
**Issue:** 1.1 results don't show LPG entries
**Fix:** Debug calculation/reporting logic to ensure LPG activities are included
**Files:**
- `backend/app/api/reports.py`
- `backend/app/api/activities.py`

---

## HIGH PRIORITY

### Task 10: Add MMBTU Unit with Conversion
**Type:** BE + DB + FE
**Issue:** MMBTU unit missing from fuels tab
**Fix:**
- DB: Add MMBTU to unit conversions (1 MMBTU = 293.07 kWh)
- BE: Ensure unit conversion logic handles MMBTU
- FE: Add MMBTU option to fuel forms
**Files:**
- `backend/app/data/unit_conversions.py`
- `frontend/src/components/wizard/StationaryCombustionForm.tsx`

---

### Task 11: Better Import Error Messages
**Type:** BE + FE
**Issue:** Errors show only row number, hard to find issues
**Fix:**
- BE: Return detailed error info (row, column, expected value, actual value)
- FE: Display errors in readable format with context
**Files:**
- `backend/app/api/import_data.py`
- `frontend/src/app/import/page.tsx`

---

### Task 12: Excel Example Rows Handling
**Type:** BE + XL
**Issue:** First rows are examples, confusing. System reads them as data.
**Fix:**
- Option A: BE skips rows where description contains "example"
- Option B: Remove example rows from template, add instructions
**Files:**
- `backend/app/api/import_data.py`
- Excel templates

---

### Task 13: Excel Template Legend
**Type:** XL
**Issue:** Missing legend explaining yellow=locked, white=editable
**Fix:** Add legend row to each tab and instructions sheet
**Files:** Excel templates in `climetrix_v3_files/`

---

### Task 14: Supplier Emission Factor Input Verification
**Type:** FE
**Issue:** Need to verify custom supplier factor input works in Electricity Market form
**Fix:** Test and fix if needed
**Files:** `frontend/src/components/wizard/ElectricityMarketForm.tsx`

---

## MEDIUM PRIORITY

### Task 15: Add Missing Gases to Excel Template
**Type:** XL
**Issue:** R-123, Halon-1211, FM-200 missing from Excel template dropdown
**Fix:** Add to Excel template's 1.3 tab dropdown list
**Files:** Excel templates

---

### Task 16: Link Grid Selection to Organization Info
**Type:** FE
**Issue:** Grid region could auto-select based on organization's country
**Fix:** Read org's default_region and pre-select matching grid
**Files:**
- `frontend/src/components/wizard/ElectricityLocationForm.tsx`
- `frontend/src/hooks/useEmissions.ts`

---

### Task 17: Add EPA eGRID Source Link
**Type:** FE
**Issue:** Should show link to EPA source for US grid factors
**Fix:** Add info tooltip/link in ElectricityLocationForm for US states
**Files:** `frontend/src/components/wizard/ElectricityLocationForm.tsx`

---

## Summary Table

| # | Task | Type | Priority |
|---|------|------|----------|
| 1 | Fix Specialized Forms Not Deploying | FE | Critical |
| 2 | Currency Conversion for Spend-Based | BE+FE | Critical |
| 3 | Dashboard Location vs Market Comparison | FE+BE | Critical |
| 4 | Dashboard Drill-Down by Emission Type | FE+BE | Critical |
| 5 | Link Imported File to Organization | FE+BE | Critical |
| 6 | Import Site Selection Not Working | FE+BE | Critical |
| 7 | Remove Category 1.4 | FE+BE+DB+XL | Critical |
| 8 | Verify Emission Factors Match DEFRA 2024 | DB | Critical |
| 9 | Verify LPG Shows in Results | BE | Critical |
| 10 | Add MMBTU Unit with Conversion | BE+DB+FE | High |
| 11 | Better Import Error Messages | BE+FE | High |
| 12 | Excel Example Rows Handling | BE+XL | High |
| 13 | Excel Template Legend | XL | High |
| 14 | Supplier Emission Factor Verification | FE | High |
| 15 | Add Missing Gases to Excel Template | XL | Medium |
| 16 | Link Grid Selection to Org Info | FE | Medium |
| 17 | Add EPA eGRID Source Link | FE | Medium |

---

## Work Order

**Phase 1 - Critical (Tasks 1-9)**
Start with Task 1 (forms not working) since it blocks testing other features.

**Phase 2 - High (Tasks 10-14)**
After critical issues fixed.

**Phase 3 - Medium (Tasks 15-17)**
Polish and enhancements.
