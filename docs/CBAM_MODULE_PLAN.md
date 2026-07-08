# CBAM Module — Build Plan (Definitive Regime)

**Status:** Draft for review by Avi
**Date:** 2026-07-09 (all regulatory claims date-stamped as of this date)
**Branch context:** feat/verification
**Scope:** Rebuild/complete the Climatrix CBAM module for the EU CBAM **definitive regime** (in force since 1 January 2026, as amended by the October 2025 "Omnibus" simplification).

---

## 1. Executive Summary

CBAM — the EU Carbon Border Adjustment Mechanism (Regulation (EU) 2023/956) — is the EU's carbon tariff. Companies that import cement, iron & steel, aluminium, fertilisers, hydrogen, or electricity into the EU must account for the CO2 emitted when those goods were produced abroad ("embedded emissions") and, from 2026, pay for those emissions by buying **CBAM certificates** priced off the EU ETS carbon price (recently in the €70–90/tCO2e range). The point is to make imported steel bear the same carbon cost as EU-made steel.

The mechanism just crossed its most important line: the **transitional period** (Oct 2023 – Dec 2025, quarterly reports, no payment) ended, and the **definitive regime** started 1 January 2026. In 2026 an EU importer above the new 50-tonne/year threshold must be (or have applied to be) an **authorised CBAM declarant**, must track every import of covered goods by CN code, mass, origin country and producing installation, and must be ready to buy certificates when sales open **1 February 2027** and file the first **annual CBAM declaration by 30 September 2027** covering all of 2026. Penalties are EU-ETS-grade: €100 per tonne of undeclared embedded emissions, and 3–5x that for importing above the threshold without authorisation.

For Climatrix clients this is a compliance product with a hard money angle: the module doesn't just produce a report, it forecasts a **cash liability** (tonnes x ETS price) and can materially reduce it (actual supplier data vs. penalised default values; deduction of carbon prices paid abroad). It also has a great top-of-funnel hook: the 50-tonne **exemption checker** answers, in one minute, the question every SME importer is asking right now — "does CBAM apply to me at all?" (~182,000 importers were just exempted; the rest have a serious obligation).

---

## 2. Regulatory Requirements (verified July 2026)

Every row is a claim we verified against a source; URLs in §10.

| # | Requirement | Detail (as of 2026-07-09) | Regime | Source |
|---|---|---|---|---|
| R1 | Covered goods | Cement, iron & steel, aluminium, fertilisers, hydrogen, electricity — defined by CN codes in Annex I of Reg. 2023/956 (incl. some downstream goods like screws/bolts) | Both | [1][2] |
| R2 | Transitional period | 1 Oct 2023 – 31 Dec 2025: quarterly CBAM reports to the Transitional Registry, no certificates. **Over.** | Transitional | [1] |
| R3 | Definitive regime | From 1 Jan 2026: financial obligation via CBAM certificates; CBAM Registry went live 1 Jan 2026 | Definitive | [1] |
| R4 | De minimis threshold | **50 t net mass/year cumulative** across iron & steel, aluminium, fertilisers, cement (NOT hydrogen or electricity). Below it: exempt from all CBAM obligations. Replaced the old €150/consignment rule. Commission reviews annually to keep ≥99% of emissions covered; monitoring flag at 90% of threshold; artificial splitting of imports prohibited | Definitive (Omnibus, Reg. (EU) 2025/2083, OJ 17 Oct 2025, in force 20 Oct 2025) | [3][4][5] |
| R5 | Authorised CBAM declarant | Importers above 50 t/yr must hold (or have applied for) authorised declarant status. Applications submitted **by 31 Mar 2026** allow provisional continued importing pending decision. Declaration filing can be delegated to an EU third party with an EORI number; responsibility stays with the declarant | Definitive | [4][6] |
| R6 | Certificate sales | Start **1 Feb 2027** on the central platform, covering 2026 imports retroactively. Price: EU ETS auction average — **quarterly average for 2026 emissions, weekly averages from 2027**. First Q1-2026 certificate price published 7 Apr 2026 | Definitive (Omnibus) | [1][4][6] |
| R7 | Annual declaration | Due **30 September** of the year following import (moved from 31 May). First one: **30 Sep 2027** for calendar-year-2026 imports, with certificate surrender | Definitive (Omnibus) | [4][6] |
| R8 | Quarterly holding rule | Declarants must hold certificates ≥ **50%** of embedded emissions of goods imported since start of the year (reduced from 80%) — practically relevant from 2027 | Definitive (Omnibus) | [3][4] |
| R9 | Embedded emissions calc | Actual installation-level values (verified) OR default values. **No limit on default-value use in the definitive phase** — but defaults carry a **markup**: 10% (2026), 20% (2027), 30% (2028+), based on avg intensity of the 10 highest-emitting exporter countries per CN code. Precursors: actual and default values may be mixed | Definitive | [4][7][8] |
| R10 | Indirect emissions | Electricity used in production counts for cement and fertilisers; for iron & steel, aluminium, hydrogen (Annex II goods of Reg. 2023/956) only direct emissions count in the definitive regime | Definitive | [2][8] |
| R11 | Verification | Actual values must be verified by an **accredited verifier** (Implementing Reg. (EU) 2025/2546 of 10 Dec 2025; accreditation framework in Delegated Reg. (EU) 2025/2551). First verification period (2026 imports) requires a physical site visit. Default values need **no** verification | Definitive | [9][10] |
| R12 | Carbon price deduction | Carbon price effectively paid in the country of origin is deductible; from 2027 Commission-published **default carbon prices** per third country may be used. Implementing act was in public consultation **13 May – 10 Jun 2026** — final rules still pending as of Jul 2026 | Definitive | [1][4] |
| R13 | Supplier/operator data | Third-country installation operators can register in the CBAM Registry ("Operators Third Countries Installations" module) and share actual emissions data that auto-populates declarants' filings | Both | [11] |
| R14 | Default values data | Definitive-period default values & benchmarks published by the Commission as Excel files on **13 Feb 2026**, per CN code and country of origin | Definitive | [1][7] |
| R15 | Penalties | €100/tCO2e for unsurrendered certificates (EU ETS-aligned, indexed); **3–5x** for importing >50 t without authorisation (reducible if overshoot ≤10%) | Definitive | [4][5] |
| R16 | Scope extension (DRAFT) | Proposal to extend CBAM to further downstream goods / >50% of ETS-sector emissions got **Council agreement June 2026** — still a proposal, not law. Do not build against it; design for extensibility | Proposal | [1] |
| R17 | Dec 2025 acts package | The Dec 2025 implementing/delegated acts (default values, calculation rules, verification, registry) are **adopted**; some published provisionally pending OJ publication at the time of the Dec 2025 announcements | Definitive | [7][8] |

**Conflict/uncertainty log (be honest in the UI about these):**
- Third-country carbon price deduction mechanics: implementing act **still draft** (consultation closed 10 Jun 2026). Ship the field, label the deduction "estimate — final rules pending".
- Scope extension to downstream goods: proposal only (R16).
- 2026 certificate pricing is quarterly-average based; exact operational details of the sales platform are new — treat forecaster output as an estimate, always.

---

## 3. Gap Analysis — Existing Code vs. Definitive Regime

### What exists (audited 2026-07-09)

**Backend** — `backend/app/models/cbam.py` (8 tables, migration `c3d4e5f6g7h8` applied), `backend/app/api/cbam.py` (~30 endpoints, registered at `/api/cbam` in `main.py`), `backend/app/services/cbam_calculator.py` (561 lines: embedded emissions, carbon-price deduction, certificate requirement, quarterly/annual aggregation), `backend/app/services/cbam_export.py` (XML/CSV/EU-format exporters), `backend/app/data/cbam_data.py` (1,018 lines of hardcoded reference data: ~63 CN entries across `CBAM_DEFAULT_VALUES`/`CBAM_PRODUCTS`, `CBAM_GRID_FACTORS`, static `EU_ETS_PRICES_2024`).

**Frontend** — `frontend/src/app/modules/cbam/page.tsx` (tabbed page with a "Beta" banner) + 5 components in `frontend/src/components/cbam/` (Dashboard, Installations, Imports, Reports, Calculator; ~1,750 lines). Module is listed in `frontend/src/lib/modules.ts` and gated to the Pro tier ("CBAM (Beta)") in `frontend/src/lib/pricing.ts`. Website (`website/src/app/pricing/page.tsx`) sells "CBAM compliance" in Pro + Enterprise.

| Piece | State | Verdict |
|---|---|---|
| Models: `CBAMProduct`, `CBAMInstallation`, `CBAMImport`, `CBAMQuarterlyReport`, `CBAMAnnualDeclaration`, `CBAMDefaultValue`, `CBAMGridFactor`, `EUETSPrice` | Rich, well-designed schema | Keep as base; needs Omnibus-era additions (§5) |
| Installations + Imports CRUD | Works against the models | Keep, extend |
| Quarterly report generation/submit/export | Functional-ish | **Obsolete** — transitional period ended 31 Dec 2025. Freeze as read-only history |
| Annual declaration endpoints | **Broken**: API reads model fields that don't exist — `imp.foreign_carbon_price_eur` (model has `carbon_price_paid_eur`), `imp.direct_see`/`indirect_see`, `report.year`/`quarter`/`total_imports`/`by_cn_code`, `declaration.year`/`gross_emissions_tco2e`/`deductions_tco2e`/`estimated_cost_eur`, `inst.sectors` (model has `sector`). These raise `AttributeError` at runtime; also `CBAMImport` create passes `foreign_carbon_price_eur=` kwarg the model doesn't define | **Rewrite** — this is the core of the definitive regime |
| Reference data (`cbam_data.py`) | Hardcoded, transitional-era default values, static 2024 ETS prices, `EUETSPrice` table never populated (`/calculate-emissions` hardcodes €80) | **Replace** with seeded DB tables from the 13 Feb 2026 Commission files + live ETS feed |
| Regulatory logic | No 50 t threshold, no default-value markup (10/20/30%), no authorised-declarant tracking, no 30 Sep deadline (model docstring says 31 May), no 50% quarterly holding rule, no verifier workflow tied to actual values | **Missing** — the whole Omnibus layer |
| Multi-tenancy | All queries scoped by `organization_id` | Good |
| Tests | **Zero CBAM tests** in `backend/tests/` | Must add with the rewrite |
| Frontend | Demo-quality tabs; no exemption checker, no cost forecaster, no declaration builder, no supplier data flow | Rebuild on the same skeleton |

**Bottom line:** ~60% of the schema is reusable; the API/calculation layer for the definitive regime must be rewritten (it's partially broken anyway), and everything Omnibus-specific (threshold, markup, deadlines, certificates) doesn't exist yet.

---

## 4. Module Design

### Personas

1. **EU importer (primary payer).** Compliance/finance manager at a company importing steel, aluminium, fertiliser, cement above 50 t/yr. Jobs: am I in scope? register as authorised declarant; log imports; chase suppliers for actual data; forecast certificate cash-out; file by 30 Sep 2027.
2. **Non-EU supplier / installation operator (data provider).** Plant manager in Turkey/India/China asked by EU customers for installation-level emissions. Jobs: compute specific embedded emissions (SEE) per product, get them verified, hand them to N customers once (ideally via the EU registry operator module — we mirror that flow).
3. **Consultant (Big-4 segment, per Data Hub vision).** Manages CBAM for several importer clients; needs multi-org overview and export-quality outputs.

### User journeys

- **J1 Exemption check (unauthenticated-friendly, lead magnet):** enter expected annual tonnage per sector (or upload import list) → verdict: exempt / near-threshold (90% monitoring flag) / in scope → CTA into the module. Handles the hydrogen/electricity carve-out (no de minimis there).
- **J2 Importer setup:** org profile (EORI, authorised-declarant status + application date, member state) → add suppliers/installations → import register (manual, CSV/Excel via Smart Import, later customs-broker feed).
- **J3 Emissions data collection:** per import line, engine picks default value (+year markup) automatically; importer requests actual SEE from the linked installation; when verified actual data arrives, liability drops — show the € delta ("actual data saves you €X").
- **J4 Cost forecasting:** running total of 2026 embedded emissions x ETS price → estimated certificate cost, quarterly 50% holding schedule from 2027, scenario slider on ETS price.
- **J5 Annual declaration:** wizard aggregates the year, applies deductions, produces the declaration data pack (and registry-shaped export) ahead of 30 Sep 2027.

### Screens

| Screen | Route | Purpose |
|---|---|---|
| CBAM Overview | `/modules/cbam` | Compliance status banner (exempt / at-risk / authorised), YTD tonnes vs 50 t gauge, emissions, forecast liability, deadline countdown (31 Mar 2026 application, 1 Feb 2027 sales, 30 Sep 2027 declaration) |
| Exemption checker | `/modules/cbam/exemption` (+ public variant on `/try`) | J1; per-sector tonnage, verdict + explanation with citations |
| Imports register | `/modules/cbam/imports` | Table + CSV/Excel upload; columns: date, CN code (typeahead), mass, origin, installation, method (default+markup vs actual), tCO2e, est. € |
| Installations & suppliers | `/modules/cbam/installations` | CRUD + data-request workflow (email link), verification status, verifier details |
| Emissions data collection | `/modules/cbam/data` | Per-installation SEE per CN code, actual vs default comparison, document upload, verification tracking |
| Cost forecaster | `/modules/cbam/forecast` | ETS price chart (weekly), liability projection, price scenarios, quarterly holding schedule, carbon-price-paid deduction (marked "rules pending") |
| Annual declaration builder | `/modules/cbam/declaration` | Wizard: completeness checks → aggregation → deductions → summary + exports |
| Reports (legacy) | `/modules/cbam/reports` | Read-only 2024–2025 quarterly history |

---

## 5. Backend Plan

### 5.1 Model changes

- **`Organization`/new `CBAMDeclarantProfile`:** EORI, member state, authorised-declarant status (`not_needed`/`planned`/`applied`/`authorised`/`rejected`), application date, authorisation number, declaration delegate.
- **`CBAMImport`:** add `foreign_carbon_price_eur` + currency (or standardize the API on the existing `carbon_price_paid_eur`), `default_markup_pct` applied, `data_request_id`, verified flag; keep provenance fields.
- **`CBAMAnnualDeclaration`:** align field names with the API (year/gross/deductions/estimated_cost — pick model names once, fix API), deadline = 30 Sep (docstring currently says 31 May), add `quarterly_holding_schedule` JSON.
- **New `CBAMDefaultValue` semantics:** add `country_code` (definitive defaults are per CN **and origin country**), `markup_applies` flag; seed from the Commission's 13 Feb 2026 Excel.
- **New `CBAMThresholdStatus`** (or computed service): YTD net mass across the four de-minimis sectors per org+year, with 90% warning state.
- **New `CBAMDataRequest`:** org → installation request for actual SEE (status: requested/received/verified/rejected), token for supplier-facing form (phase 3).
- **New `CBAMCertificateLedger`** (phase 2+): purchases, surrenders, repurchase-by-31-Oct tracking, 50% holding check.
- **`EUETSPrice`:** keep; add `price_type` (`weekly_avg`/`quarterly_avg`/`spot`) since 2026 certificates use quarterly averages and 2027+ weekly.
- One Alembic migration per phase; status/enum columns as **varchar not native PG enums** (existing prod rule).

### 5.2 Endpoints (rework of `app/api/cbam.py`)

- `GET /api/cbam/status` — compliance snapshot (threshold, declarant state, deadlines).
- `POST /api/cbam/exemption-check` — stateless checker (public-capable for /try, rate-limited).
- Installations/imports CRUD — keep, fix field mapping, add bulk import (reuse Smart Import parsing pipeline; inline in prod, no arq worker — existing rule).
- `POST /api/cbam/calculate` — rewrite: default+markup path (per CN+country+year), actual path, indirect-emissions rules per sector (R10), precursor mixing.
- `GET /api/cbam/forecast?year=&price_scenario=` — liability projection + quarterly 50% schedule.
- Annual declaration: `POST /api/cbam/declarations/{year}` (rewrite, fix broken field refs), completeness check endpoint, exports. **Drop the pretense of registry XML** until we validate against the actual CBAM Registry declaration format — current `cbam_export.py` XML is speculative; keep CSV/JSON/PDF pack first.
- Quarterly report endpoints → read-only (410/labelled legacy for generation of periods ≥2026).
- Reference: `GET /cn-codes` (move from hardcoded list to DB), `GET /ets-prices`, `GET /default-values`.
- Data requests: `POST /api/cbam/data-requests`, supplier-facing token endpoints (phase 3).

### 5.3 Calculation engine (`cbam_calculator.py` rewrite)

1. Resolve CN code → sector, indirect-emissions applicability (Annex II logic), de-minimis eligibility (not hydrogen/electricity).
2. Path A **default**: SEE(CN, origin country) x (1 + markup(year: 10/20/30%)) x mass.
3. Path B **actual**: verified SEE from installation (block "actual" without verification metadata; warn until verified), electricity route via grid factor where allowed.
4. Deduction: carbon price effectively paid (flagged estimate until R12 act finalises).
5. Certificates = ceil(net tCO2e); cost = certificates x applicable ETS average (quarterly for 2026, weekly 2027+).
6. Every result carries `assumptions[]` + `warnings[]` + source references — consistent with the verification-ready parser philosophy of the platform.
7. Full pytest suite: threshold edges (49.9/50/55 t, 10% overshoot penalty band), markup by year, sector indirect rules, deduction, rounding.

### 5.4 Data Hub integration

Recommendation: **CBAM stays a separate module** (it's an import/trade ledger, not an emissions activity category), but it plugs into the Hub in three places: (a) the org **profile layer** gains "Do you import CBAM goods into the EU?" which activates the module and drives the hub's category matrix; (b) Smart Import/parser reuses the same upload→parse→review pipeline for customs/import files; (c) hub home shows a CBAM status card. This keeps the hub as the front door without forcing CBAM data into the activity model.

---

## 6. Frontend Plan

- Keep `/modules/cbam/page.tsx` shell; convert tab state to real sub-routes (`/modules/cbam/*`) for deep-linking; keep AppShell + Beta banner until Phase 2 exit.
- New components: `ExemptionChecker` (stepper + verdict card), `ThresholdGauge`, `DeadlineTimeline`, `CostForecaster` (recharts line: ETS price + scenario band), `DeclarationWizard` (multi-step, reuse wizard patterns from setup flow), `DataRequestPanel`, `ImportUploadDialog` (reuse Smart Import components).
- Rework `CBAMImports`/`CBAMInstallations` against the fixed API contracts; TanStack Query hooks in `src/lib/api.ts` typed to the new schemas.
- Gating: `LockedModule` per pricing tier (see §9 Q2); exemption checker deliberately **outside** the gate as a lead tool (mirrors the `/try` + `website_trial` lead-gate pattern).
- Public exemption checker variant for the website/`/try` funnel — one-screen, no login, lead capture before full verdict details.

---

## 7. Data & Reference Needs

| Dataset | Source | Refresh | Notes |
|---|---|---|---|
| Annex I CN codes (definitive) | Reg. 2023/956 Annex I (consolidated post-2025/2083) | On legal change | Replace hardcoded `CBAM_PRODUCTS`; keep validity dating |
| Default values per CN x origin country (with markup base) | Commission Excel, published 13 Feb 2026 [1][7] | Commission updates | Seed script + `source_reference`; keep transitional values for history |
| Grid emission factors | Commission defaults / IEA | Annual | Only where indirect path applies |
| EU ETS certificate price | Commission-published CBAM certificate price (Q1-2026 published 7 Apr 2026); ETS auction data for live forecasting | Weekly job | Store `price_type`; forecaster can use spot as scenario |
| Third-country default carbon prices | Commission (from 2027, R12) | TBD | Act still draft — stub table |
| CBAM Registry declaration format | Commission registry docs | Watch | Don't ship XML until validated against real schema |

---

## 8. Phased Roadmap

**Phase 1 — MVP "Am I exposed and what will it cost?" (~2–3 weeks)**
Exemption checker (public + in-app), declarant profile + deadline tracking, imports register with CSV upload, rewritten calculation engine (default+markup path, sector indirect rules), cost forecaster with seeded ETS prices, fix/retire broken endpoints, seed 13-Feb-2026 default values, pytest suite. *Exit: a real importer can check exposure, log 2026 YTD imports, and see a defensible € forecast.*

**Phase 2 — Declaration readiness (~2–3 weeks)**
Actual-data path with verification metadata, carbon-price deduction (flagged), annual declaration builder + completeness checks + CSV/PDF pack, certificate ledger + 50% quarterly holding schedule, legacy quarterly reports frozen read-only. *Exit: dry-run declaration for 2026 data, months before the 30 Sep 2027 deadline.*

**Phase 3 — Supplier portal & scale (~3–4 weeks)**
Tokenized supplier data-request flow (installation operator enters SEE + documents, verifier details), multi-client consultant view, ETS price feed automation, registry-format export once schema validated, monitoring alerts (90% threshold, deadline reminders via existing email service).

Rough total: ~7–10 dev-weeks. Phase 1 is independently shippable and marketable before the conference follow-up window.

---

## 9. Open Questions for Avi

1. **First client segment:** EU importers directly, or the Big-4/consultant channel (Data Hub vision names consultants as a segment)? Changes whether multi-org views land in Phase 2 or 3.
2. **Pricing tier:** in-app the module is badged **"Beta"** and `pricing.ts` puts "CBAM (Beta)" in **Pro**; the website sells "CBAM compliance" in Pro *and* Enterprise. (Note: I found a "Beta" badge, not an "under development" badge — worth aligning wording.) Proposal: exemption checker free (lead gen), register+forecaster Pro, declaration builder + supplier portal Enterprise. Confirm?
3. **Public exemption checker on the website /try funnel** with the lead-before-results gate — yes/no?
4. **Legacy transitional data:** any real client 2024–2025 quarterly data to preserve, or can we freeze/purge demo data?
5. **Registry XML:** hold until we can validate against the real CBAM Registry declaration schema (my recommendation), or keep shipping best-effort XML?
6. **ETS price feed:** manual weekly admin entry (cheap, fine for MVP) vs automated fetch job?
7. **Does Climatrix itself take a position on verification services** (partner with accredited verifiers?) given physical site visits are mandatory for 2026 actual data?

---

## 10. References

1. European Commission, CBAM main page (regime dates, registry go-live, certificate pricing, 13 Feb 2026 default values, consultations, June 2026 scope-extension state) — https://taxation-customs.ec.europa.eu/carbon-border-adjustment-mechanism_en
2. Regulation (EU) 2023/956 (basics; Annex I goods; Annex II direct-only goods) — https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32023R0956
3. ICAP, "EU adopts simplifications of CBAM rules ahead of the compliance phase starting in 2026" — https://icapcarbonaction.com/en/news/eu-adopts-simplifications-cbam-rules-ahead-compliance-phase-starting-2026
4. Mayer Brown, "EU Adopts CBAM Simplification Regulation: 10 Key Amendments" (50 t threshold, 31 Mar 2026 provisional imports, 30 Sep deadline, 50% holding, markup defaults, repurchase by 31 Oct, penalties) — https://www.mayerbrown.com/en/insights/publications/2025/10/eu-adopts-cbam-simplification-regulation-10-key-amendments-and-challenges-ahead
5. CMS, "Regulation (EU) 2025/2083" (OJ 17 Oct 2025, in force 20 Oct 2025; ~182k importers exempt, >99% emissions retained) — https://cms.law/en/prt/news-information/amendment-to-regulation-eu-2023-956-on-simplifying-and-strengthening-the-cbam-carbon-border-adjustment-mechanism-regulation-eu-2025-2083
6. Commission news, "Officially published: Simplifications for the CBAM" (20 Oct 2025) — https://taxation-customs.ec.europa.eu/news/officially-published-simplifications-carbon-border-adjustment-mechanism-cbam-2025-10-20_en
7. Mayer Brown, "European Commission Issues CBAM Operational Rules" (17 Dec 2025 package: default values per CN x country, markup 10/20/30%, precursor mixing; downstream-extension proposal) — https://www.mayerbrown.com/en/insights/publications/2025/12/european-commission-issues-cbam-operational-rules-and-proposes-downstream-extension-of-the-cbam-scope
8. O'Melveny, "How the EU's New Default Emissions Values Under CBAM Impact US Exporters" — https://www.omm.com/insights/alerts-publications/how-the-eu-s-new-default-emissions-values-under-cbam-impact-us-exporters-what-you-need-to-know-for-2026/
9. Commission Implementing Regulation (EU) 2025/2546 of 10 Dec 2025 (verification of actual values; applies from 1 Jan 2026) — https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=OJ:L_202502546
10. Commission, CBAM verification page (accreditation framework incl. Delegated Reg. (EU) 2025/2551; updated 30 Jun 2026) — https://taxation-customs.ec.europa.eu/carbon-border-adjustment-mechanism/cbam-verification_en
11. Commission, CBAM Registry and Reporting (operators' third-country installations module) — https://taxation-customs.ec.europa.eu/carbon-border-adjustment-mechanism/cbam-registry-and-reporting_en
12. Reed Smith, "What you need to know as CBAM simplification comes into effect" — https://www.reedsmith.com/our-insights/blogs/viewpoints/102lr9t/what-you-need-to-know-as-cbam-simplification-comes-into-effect/
13. EY, "EU adopts CBAM Omnibus Regulation" — https://www.ey.com/en_gl/technical/tax-alerts/eu-adopts-cbam-omnibus-regulation
14. Clean Carbon, penalties from Jan 2026 — https://cleancarbon.ai/blog/what-are-the-penalties-for-non-compliance-with-cbam-from-january-2026/
15. CO2-IQ, "EU CBAM Emissions Data: Monitoring, Reporting & Verification" (actual vs default in definitive phase; no default-use limits) — https://co2-iq.com/en/eu-cbam-emissions

---

*Prepared by Claude Code on branch `feat/verification`. Code audit findings reference commit state at ca39e79 (main merge base). Regulatory facts verified via the sources above on 2026-07-09; items R12 and R16 are explicitly not yet final law.*
