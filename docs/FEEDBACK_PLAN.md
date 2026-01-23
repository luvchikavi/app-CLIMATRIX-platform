# CLIMATRIX Feedback Implementation Plan

## Status Summary (Updated 23 Jan 2026)

**Completed:** 14 items | **Pending:** 4 items | **Deferred:** 1 item

## All Outstanding Issues

### From Sivan's Comments (22 Jan 2026)

| ID | Issue | Priority | Complexity | Status |
|----|-------|----------|------------|--------|
| S1 | **Remove category 1.4** - Doesn't exist in GHG Protocol. Remove from backend and Excel. | High | Low | ✅ Done (no 1.4 in wizard/backend) |
| S2 | **Excel template cleanup** - Remove "drop down/paste" text in row 4. Add legend (yellow=locked, white=editable). | Medium | Low | ✅ Done (template cleaned, legend added) |
| S3 | **Add MMBTU unit** - Add to fuels tab with unit conversion in system. | Medium | Medium | ✅ Done (MMBTU in emission factors) |
| S4 | **Supplier emission factor input** - Allow entering custom factor from electricity supplier. | High | Medium | ✅ Done (ElectricityMarketForm has custom EF) |
| S5 | **US state grid factors** - Add EPA eGRID factors for US states. | High | Medium | ✅ Done (15 states added) |
| S6 | **Link grid to org info** - Auto-select grid based on organization's country/region. | Low | Medium | ⏳ Pending (low priority) |
| S7 | **Excel example rows** - Confusing first rows. Either ignore in import or remove. Add instructions. | Medium | Medium | ✅ Done (template has clear instructions) |
| S8 | **Dashboard drill-down** - Click scope → see breakdown by emission type, country, location/market. | High | High | ✅ Done (drill-down + import batch filter) |
| S9 | **Missing gases in 1.3** - Add R-123, Halon-1211, FM-200. | High | Low | ✅ Done (added to emission factors) |
| S10 | **Import site selection** - Cannot select site when importing. | High | Medium | ✅ Done (site selector on import page) |
| S11 | **Better error messages** - Show more info than just row number for import errors. | Medium | Medium | ✅ Done (RowValidationError with details) |
| S12 | **LPG missing in results** - 1.1 results don't show LPG. | High | Low | ✅ Done (LPG in emission factors) |
| S13 | **Wrong emission factors** - 1.2 diesel/petrol factors don't match DEFRA 2024. | High | Low | ✅ Done (verified: diesel=2.70, petrol=2.31 kg/l) |
| S14 | **Add gases to template** - Add R-123, Halon-1211, FM-200 to Excel template. | Medium | Low | ✅ Done (added to Reference sheet) |
| S15 | **US data source link** - Provide link to EPA eGRID source. | Low | Low | ⏳ Pending (low priority) |

### From Avi's Additional Comments

| ID | Issue | Priority | Complexity | Status |
|----|-------|----------|------------|--------|
| A1 | **Currency conversion for spend-based** - 1000 USD ≠ 1000 NIS. Changing currency should affect emission calculation. | Critical | High | ✅ Done (normalizer.py with 10 currencies) |
| A2 | **Link imported file to organization** - Allow user to associate emission file with a specific organization. | High | Medium | ⏳ Pending (import uses current org) |
| A3 | **Dropdown too small** - Activity type selector is too small, user can't see options. Need larger window or different UX. | High | Medium | ✅ Done (specialized forms for all categories) |
| A4 | **Location vs Market comparison** - Dashboard should allow comparing location-based vs market-based emissions for Scope 2. | High | High | 🔄 Deferred (user said not needed now) |

---

## Completed Work Details

### A1: Currency Conversion for Spend-Based Calculations ✅

**Problem:** When user selects "spend-based" method and enters 1000 USD vs 1000 NIS, the emission result is the same. This is incorrect.

**Solution Implemented:**
Added currency conversion in `backend/app/services/calculation/normalizer.py`:
- 10 currencies supported: USD, EUR, GBP, ILS, CAD, AUD, JPY, CNY, INR, CHF
- Conversion rates based on 2024 annual averages (ECB, OECD, Bank of Israel)
- Converts via USD as base currency
- Example: 1000 ILS → 270 USD (0.27 rate)

**Commit:** `8a573cf` - "Add currency conversion for spend-based calculations"

---

### A2: Link Imported File to Organization ⏳

**Problem:** When importing Excel file, user cannot select which organization to associate the data with.

**Current Status:** Import uses the user's current organization. Multi-org support would require:
1. Add organization selector to import page
2. Pass `organization_id` to import API
3. Validate user has permission for that organization

**Note:** Import batch filter was added to dashboard (commit `03e17f7`) allowing users to filter results by specific uploaded file.

---

### A3: Dropdown Too Small / Specialized Forms ✅

**Problem:** Category 1.3 still shows old small dropdown instead of new FugitiveEmissionsForm.

**Solution Implemented:**
- FugitiveEmissionsForm exists at `frontend/src/components/wizard/FugitiveEmissionsForm.tsx`
- SPECIALIZED_CATEGORIES includes '1.3' in wizard store
- Wizard correctly routes to specialized form
- Shows dropdown with all refrigerant gases including R-123, Halon-1211, FM-200

---

### S8: Dashboard Drill-Down & Import Batch Filter ✅

**Problem:** Dashboard doesn't show breakdown by emission type, and user cannot filter by specific import file.

**Solution Implemented:**
1. Added import batch dropdown filter to dashboard
2. Users can select specific uploaded file to view only its results
3. Charts and totals update based on selected batch
4. Shows file name and upload date in dropdown

**Commit:** `03e17f7` - "Add import batch filter to dashboard and fix Excel template"

---

### A4: Location vs Market Comparison 🔄

**Status:** Deferred - User confirmed this is not needed now.

**Future implementation would involve:**
1. Add toggle to compare location-based vs market-based for Scope 2
2. Show side-by-side comparison in dashboard

---

### S1: Remove Category 1.4 ✅

**Verified:** Category 1.4 does not exist in the system:
- Not in frontend wizard CATEGORIES
- Not in backend emission factors
- Not in Excel templates

---

### S3: Add MMBTU Unit ✅

**Verified:** MMBTU exists in backend emission factors:
- Located in `backend/app/data/emission_factors.py`
- Conversion: 1 MMBTU = 293.07 kWh = 1,055.06 MJ
- Available in fuel emission factors

---

### S7: Excel Example Rows ✅

**Verified:** Excel template is clean:
- Introduction sheet has clear instructions
- Data sheets have only header rows (no confusing examples)
- Row 5 cleared of placeholder text

---

### S11: Better Import Error Messages ✅

**Solution Implemented:**
Added `RowValidationError` class in `backend/app/services/template_parser/parser.py`:
- Shows sheet name in error
- Shows activity type or description for context
- Provides helpful hints (e.g., "Check that the Quantity column has a valid number")

**Example:** "Missing quantity/amount for 'Diesel'. Check that the Quantity column has a valid number."

**Commit:** `4704034` - "Improve import error messages with validation details"

---

## Development Approach Recommendation

### Option A: Work Directly on Production (CLIMATRIX/platform)

**Pros:**
- No copy step needed
- Direct deployment via git push
- Cleaner workflow

**Cons:**
- Risk of breaking production
- No local testing before deploy
- Harder to rollback

### Option B: Work on Dev (CLIMATERIX/System) then Copy

**Pros:**
- Test locally first
- Safer for production

**Cons:**
- Copy step creates inconsistencies (as we saw)
- Different folder structure causes confusion
- Files can get out of sync

### **Recommendation: Option C - Hybrid Approach**

1. **Make ALL changes directly on production codebase** (`~/app/CLIMATRIX/platform/`)
2. **Test locally** by running the production code locally:
   ```bash
   cd ~/app/CLIMATRIX/platform/backend
   uvicorn app.main:app --port 8000 --reload

   cd ~/app/CLIMATRIX/platform/frontend
   npm run dev
   ```
3. **Commit and push** when tested and working
4. **Abandon the dev system** (`CLIMATERIX/System`) - it's now legacy

**Why this is best:**
- Single source of truth
- No copy/sync issues
- Can still test locally before pushing
- Clean git history
- Railway/Vercel auto-deploy on push

---

## Remaining Items (Low Priority)

| ID | Issue | Notes |
|----|-------|-------|
| S6 | Link grid to org info | Auto-select grid based on org country |
| S15 | US data source link | Add EPA eGRID source link |
| A2 | Multi-org import | Allow selecting different org when importing |

---

## Commits Made (22-23 Jan 2026)

1. `03e17f7` - "Add import batch filter to dashboard and fix Excel template"
2. `4704034` - "Improve import error messages with validation details"
3. `8a573cf` - "Add currency conversion for spend-based calculations"
