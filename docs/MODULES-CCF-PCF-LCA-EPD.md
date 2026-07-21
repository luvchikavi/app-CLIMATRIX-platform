# CCF · PCF · LCA · EPD — Regulatory Review & Implementation Design

**Date:** 2026-07-21 · **Status:** APPROVED — Avi locked all 4 decisions 2026-07-21 (see §5.3); Phase A (CCF completion) in build
**Author:** Claude (research session) · **Companion docs:** AUDIT-PARTNERS-RESEARCH.md, GOING-LIVE-PLAN.md

---

## 0. Executive summary

The four requested tools are not four equal builds — they form a **dependency chain** that
reuses Climatrix's existing calculation engine at every step:

| Tool | What it is | Governing standards | Build reality |
|------|-----------|---------------------|---------------|
| **CCF** | Corporate Carbon Footprint (org-level Scopes 1-3) | GHG Protocol Corporate Standard, ISO 14064-1:2018, ESRS E1/VSME | **Climatrix already IS this.** A gap-closing + packaging sprint, not a new module. |
| **PCF** | Product Carbon Footprint (per-product cradle-to-gate) | ISO 14067:2018, GHG Protocol Product Standard, **PACT Methodology v3**, EU Battery Reg | New Product/BOM layer on top of the existing factor library + calc engine. |
| **LCA** | Life Cycle Assessment (multi-impact, full lifecycle) | ISO 14040/14044:2006, EF 3.1 impact method, EN 15804 indicator set | Heaviest lift. Recommend a **streamlined LCA engine** (process tree + characterization factors), NOT a research-grade matrix solver. |
| **EPD** | Environmental Product Declaration (published, verified doc) | ISO 14025, **EN 15804+A2**, PCRs, ECO Platform guidelines | A document-generation + verification-workflow layer on top of LCA. We can *prepare* EPDs; a program operator publishes them. Reuses the verifier portal. |

**Build order that falls out of the dependencies:** CCF-completion → PCF → LCA-lite → EPD.
This is consistent with the approved module order (verifier ✓ → CBAM GA → PCAF → SBTi →
LCA/EPD last) — PCF is the one newcomer and slots naturally before LCA/EPD because EPD
needs the LCA engine and LCA-lite needs the product model PCF introduces.

**The one strategic decision that gates everything downstream:** LCI background-database
licensing (§5.4). Everything else is engineering.

---

## 1. CCF — Corporate Carbon Footprint

### 1.1 Regulatory & protocol landscape (verified July 2026)

- **GHG Protocol Corporate Standard** (2004, Scope 2 Guidance 2015) — the de-facto global
  method. **Currently under revision:** full draft of the 3rd edition due **mid-2026** for
  public consultation, final publication expected **end-2027**. ISO technical-community
  members joined the GHGP working groups Q1 2026, so ISO 14064-1 and GHGP are converging.
  → Design consequence: keep methodology text data-driven (we already do, via the
  methodology registry) so the 2027 edition is a content update, not a code change.
- **ISO 14064-1:2018** — what our reports + verifier portal already target. Six-category
  structure (not 3 scopes) for ISO-style reporting; verification under ISO 14064-3 (remote
  allowed per 14064-5:2026 — already researched in AUDIT-PARTNERS-RESEARCH.md).
- **CSRD post-Omnibus** (Directive (EU) 2026/470, in force 19 Mar 2026): scope cut ~90% —
  only companies with **1,000+ employees AND €450M+ turnover** must report; ESRS datapoints
  cut ~61% (1,073 → ~320); revised ESRS adopted mid-2026. **VSME** becomes the
  Commission-adopted *voluntary* standard for everyone below the threshold in 2026.
  → Market consequence: the mid-market (our ICP) reports **voluntarily via VSME** or under
  supply-chain pressure — exactly the teaser→Starter→Professional funnel. VSME's ~100
  datapoints (11 disclosures) are a tractable export target.
- **Israel:** voluntary GHG reporting mechanism (MoEP), ISO 14064 verification via SII —
  already covered by the verifier-partner research.

### 1.2 Gap analysis vs current platform

Already live: Scopes 1-3 activity capture, Smart Import, derived-quantity engine, factor
library with region precedence, ISO 14064-style report, methodology page, verifier portal,
audit trail. What a self-respecting "CCF module" still lacks:

1. **Consolidation approach** — org setting: `operational_control | financial_control |
   equity_share` (GHGP requirement; today implicit operational control). One org column +
   report disclosure line. Equity-share % per Site if we go deep (defer).
2. **Base year + recalculation policy** — org fields `base_year`,
   `recalculation_threshold_pct` (typical 5%), report section stating the policy; a
   base-year comparison strip on the dashboard. The recalc endpoint already exists.
3. **Scope-3 completeness screening** — a 15-category matrix view (relevant / not relevant
   / measured / excluded + justification per category). GHGP requires *screening* all 15,
   not measuring all 15. This is a small model (`Scope3Screening` per period) + a hub
   panel, and it directly feeds the data-hub vision (category matrix = hub home).
4. **Exports**: ESRS E1 datapoint export (post-Omnibus reduced set) + VSME basic-module
   export. Both are mappings from data we already hold → new export formats in the
   existing reports lane.
5. **Uncertainty / data-quality tiers** — we already carry confidence bands (g/a/r) from
   Smart Import; surface them as a data-quality statement per GHGP (percent of inventory
   by tier). No new capture needed — aggregation + disclosure only.

### 1.3 Verdict

**Effort: 1-2 sessions.** No new engine. Position "CCF" as a named module on /modules and
the marketing site ("full GHG Protocol / ISO 14064-1 corporate footprint") — today we
under-sell it by not naming it. Items 1-2-3 are the substance; 4-5 are polish.

---

## 2. PCF — Product Carbon Footprint

### 2.1 Regulatory & protocol landscape (verified July 2026)

- **ISO 14067:2018** — the PCF quantification standard (partial LCA, GWP only, per
  ISO 14040/44 principles). Functional/declared unit, cradle-to-gate or cradle-to-grave.
- **GHG Protocol Product Standard** (2011) — same family, more reporting-oriented.
- **PACT (WBCSD) Methodology v3 + Data Exchange Protocol v3.0.x** — THE interoperability
  layer: prescriptive cross-sector calc rules + a machine-readable PCF data model and REST
  API for supplier→buyer exchange. Cradle-to-gate is the standard B2B boundary.
  → This is the export format to implement. A "PACT-conformant PCF JSON" is what buyers'
  procurement systems ingest; conformance is testable against the published spec.
- **EU Battery Regulation 2023/1542** — the first *mandatory* PCF anywhere: EV batteries
  (declarations since Feb 2025), **rechargeable industrial batteries >2 kWh from
  18 Feb 2026**, performance classes Aug 2026, max thresholds Feb 2028, QR-code access
  Feb 2027. Third-party verified, per model + per plant.
  → A concrete, dated wedge for PCF sales — but only if we target battery/industrial OEMs.
- **CBAM** (already ours): embedded emissions per tonne of good **is a cradle-to-gate PCF
  variant**. Our `cbam_calculator` already does product-level intensity math.
- **ESPR / Digital Product Passport** — PCF datapoints land in DPPs from ~2027+ category
  by category; PACT-format data is the feeder. Watch, don't build.

### 2.2 The algorithm

```
PCF(product) [kgCO2e / declared unit] =
    Σ own-process emissions        (activity_qty × EF, from OUR existing engine)
  + Σ purchased-input contributions (input_qty_per_unit × input PCF or secondary EF)
  + Σ transport/upstream modules    (existing freight derivation engine!)
  ─ allocated by mass|economic value where processes are shared
  ÷ units produced in the period
```

Rules that must be first-class (PACT v3 prescribes them): declared unit; boundary
(cradle-to-gate default); allocation method (physical → economic hierarchy);
**primary-data share %** (a headline PACT metric — we can compute it from our
green/amber/red provenance!); cut-off criteria; biogenic split (we already carry
`biogenic` columns); exclusion of offsets.

### 2.3 Backend design

New models (`models/product.py`):
- `Product` — org-scoped: name, sku, declared_unit, cn_code (CBAM link), category
- `ProductInput` (BOM row) — product_id, input type (`purchased_material | energy |
  transport | supplier_pcf`), quantity_per_unit, unit, factor_key OR supplier_pcf_id,
  allocation basis
- `SupplierPCF` — ingested PACT JSON from a supplier (id, product match, value,
  boundary, primary_data_share, valid_until, source doc → evidence storage)
- `ProductFootprint` — computed result snapshot: period_id, value, breakdown by stage
  (own ops / inputs / transport), primary_data_share, methodology hash, status
  (`draft | final`), immutable once final (verifier-portal pattern)

Service `services/pcf.py`: resolves each BOM line through the **existing factor library +
region precedence + derived-quantity engine**, allocates shared site/period activities to
products via a production-volume table, emits `ProductFootprint` with a full derivation
story per line (same provenance JSON shape as Smart Import grounding).

API (`api/products.py`): CRUD products/BOM · `POST /products/{id}/footprint?period_id=` ·
`GET /products/{id}/footprint/export?format=pact|pdf` · `POST /products/supplier-pcf`
(PACT JSON upload — validate against spec, Smart-Import-style review row).

### 2.4 Frontend

- **/products** catalog (cards: name, declared unit, latest PCF, primary-data-share dial)
- Product detail: BOM editor grid (same interaction grammar as the ingest review grid —
  factor-grounded rows, confidence bands, "needs data" gaps), stage-breakdown chart,
  derivation story per line (reuse the expandable methodology rows from wave3 UI)
- PACT export button (JSON) + branded PCF report (PDF lane exists)
- Supplier PCF inbox: upload/validate PACT files, match to BOM lines
- Teaser behavior: parse + compute visible, **export locked** (existing entitlement lane)

### 2.5 Verdict

**Effort: 2-4 sessions.** Highest reuse ratio of the three new modules: factor library,
region precedence, derived-quantity engine, provenance/confidence UI, PDF/export lane,
entitlements — all already built. New: product/BOM model, allocation logic, PACT schema
export/ingest. CBAM synergy is strong (same ICP: steel/cement/aluminium exporters; CN
codes shared; CBAM embedded-emissions math is a PCF sibling).

---

## 3. LCA — Life Cycle Assessment

### 3.1 Standards landscape

- **ISO 14040:2006 / 14044:2006** — principles + requirements. Stable for 20 years. Four
  phases: goal & scope → LCI (inventory) → LCIA (impact assessment) → interpretation.
- **EF 3.1** (EU Environmental Footprint method) — the characterization-factor set used by
  PEF and EN 15804+A2. **16 impact categories** (climate, ozone, acidification,
  eutrophication ×3, resource use ×2, water, land, toxicity ×3, particulates, ionising
  radiation, photochemical ozone). Published, free, versioned — this is our LCIA table.
- **Data formats:** ILCD XML (EU), EcoSpold2 (ecoinvent). We need *read* paths eventually;
  not phase-1.
- **PEF/PEFCR** — EU product-footprint method; watch (ESPR will lean on it), don't build.

### 3.2 The critical scoping decision: LCA-lite, not a research engine

A full LCA platform (matrix-based LCI solving à la Brightway/SimaPro, ecoinvent's ~20k
interlinked processes) is a multi-year product and a different company. What CBAM/EPD/PCF
customers actually need is: **a process-tree model of one product, background data from a
licensed/free LCI database, characterized into the EN 15804 indicator set.**

**LCA-lite =** PCF's product/BOM tree + two extensions:
1. **Multi-indicator factors.** Today `EmissionFactor` is GWP-only. Add
   `ImpactFactor(dataset_key, region, indicator_code, value, unit, method_version)` —
   same shape as the emission-factor table, ~19 indicators per dataset instead of 1.
   The calc loop is identical: quantity × factor, summed per indicator per module.
2. **Lifecycle modules.** Tag every BOM/process line with an EN 15804 module
   (A1-A3 production, A4-A5 construction, B1-B7 use, C1-C4 end-of-life, D benefits).
   Results become a matrix: indicator × module — which IS the EN 15804 results table
   an EPD needs.

Explicitly out of scope: circular/looped process systems, Monte-Carlo uncertainty,
parameterized datasets, consequential LCA. If a customer needs those, they need SimaPro.

### 3.3 The gating decision — background LCI data licensing

| Option | Cost | Coverage | Redistribution |
|--------|------|----------|----------------|
| **ecoinvent** | €2.5k-15k+/yr, per-user/embedded licensing negotiable | Gold standard, ~20k processes | Embedding in SaaS needs a commercial agreement |
| **EF 3.1 datasets** (EU) | Free | Good for PEF/EPD-relevant materials | Free for EF-compliant uses — fits EPD generation |
| **Own curated set** (extend current library: DEFRA/IEA/EF nodes for common materials) | Effort only | Thin but honest | Ours |

**Recommendation:** start with EF 3.1 datasets + our curated library (matches our existing
"factors with provenance notes" culture); add an ecoinvent embedded license only when a
paying EPD customer requires it. **This is Avi's call — it's the only real money decision
in the whole program.**

### 3.4 Verdict

**Effort: 3-5 sessions** *after* PCF exists (it supplies the product/process tree).
Deliverable is deliberately not "an LCA tool" in marketing terms until EPD sits on top —
LCA-lite is the engine room.

---

## 4. EPD — Environmental Product Declaration

### 4.1 Regulatory landscape (verified July 2026)

- **ISO 14025** — Type III environmental declarations: LCA-based, PCR-governed,
  **independently verified, published by a program operator**.
- **EN 15804+A2** — the construction-products PCR core. Mandatory for new EPDs since
  Oct 2022; **mandated under the revised EU Construction Products Regulation for products
  placed on the market from 2026** → EPDs shift from marketing asset to market-access
  requirement in construction. Requires **13 core + 6 additional = 19 indicators**,
  modules A1-A3 minimum + C1-C4 + D mandatory (cradle-to-grave disclosure).
- **ECO Platform** Verification Guidelines V8.0 (Dec 2024-aligned) — the pan-European
  mutual-recognition layer; **digital EPD** in ILCD+EPD format is where the ecosystem is
  heading (machine-readable EPDs feeding building-LCA tools like One Click LCA).
- **Program operators:** EPD International (Environdec), IBU (DE), EPD Norge, UL, etc.
  Data freshness rules: primary data <5 years, background <10 years.

### 4.2 What Climatrix can and cannot be

We **cannot issue** EPDs (that's the program operator + third-party verifier). We can be
the **EPD preparation platform**: model the product (PCF/LCA-lite), compute the EN 15804
results matrix, generate the declaration document + machine-readable dataset, run the
verification workflow, track registration. This mirrors exactly the verifier-portal
insight: we don't replace the auditor, we make the audit frictionless — same play, same
code patterns, one level down (product instead of org).

### 4.3 Design

Backend:
- `EPDProject` — product_id, PCR (EN 15804+A2 first; PCR registry table for later),
  program_operator, declared/functional unit, RSL (reference service life), status
  machine: `draft → internal_review → verification → registered → published | expired`
  (5-year validity → renewal reminders)
- Results: the LCA-lite indicator × module matrix, frozen per EPD version
- Document generation: EN 15804-structured PDF (existing PDF lane) + **ILCD+EPD digital
  dataset** (XML/JSON) for the digital-EPD ecosystem
- **Verification workflow: reuse VerifierAccess** — token-gated read-only view of the EPD
  project incl. underlying data + provenance; verifier comment threads; this is a
  parameter change to an existing feature, not a build

Frontend: EPD wizard (product → PCR → modules in scope → data gaps checklist → results
matrix → document preview → verification tab), EPD registry list per org with validity
countdown.

### 4.4 Verdict

**Effort: 2-3 sessions** once LCA-lite exists. Target segment is construction-products
manufacturers — heavily overlapping CBAM's steel/cement/aluminium ICP, and CPR-2026 gives
the same "regulation with a date" sales motion CBAM has. Partner angle: a program-operator
/ verifier relationship (SII does EPD verification in Israel) extends the existing
verifier-partner track.

---

## 5. Program view

### 5.1 Dependency graph

```
[existing calc engine + factor library + provenance UI + verifier portal + export lane]
        │
        ├── CCF completion (independent, immediate)
        │
        └── PCF (Product/BOM + allocation + PACT)
                └── LCA-lite (multi-indicator factors + lifecycle modules)
                        └── EPD (EN 15804 doc gen + verification workflow)
```

### 5.2 Suggested phasing vs the approved module order

Approved order was: verifier ✓ → CBAM GA → PCAF → SBTi → LCA/EPD. Proposal:

| Phase | What | Sessions (est.) | Blocking decision |
|-------|------|-----------------|-------------------|
| A | CCF completion + naming | 1-2 | none |
| B | PCF module (PACT v3 export, battery-reg aware) | 2-4 | where it slots vs CBAM GA / PCAF |
| C | LCA-lite engine | 3-5 | **LCI data licensing (§3.3)** |
| D | EPD generator | 2-3 | program-operator partner pick |

### 5.3 Decisions — LOCKED by Avi 2026-07-21 ("go with your rec" on all 4)

1. **Ordering:** the CCF → PCF → LCA-lite → EPD chain is the active module track,
   starting with CCF completion now. PCAF and SBTi move behind the chain.
2. **LCI data:** free EF 3.1 datasets + curated Climatrix library. NO ecoinvent license
   until a paying EPD customer requires it.
3. **PCF wedge market:** CBAM-adjacent manufacturers (steel/cement/aluminium exporters —
   same ICP as CBAM). Battery supply chain is a later opportunistic play.
4. **EPD partner:** court SII first (covers both ISO 14064 verification and EPD
   verification in Israel — one relationship serves the verifier portal AND the EPD
   module). Avi-side outreach item alongside the existing verifier picks.

### 5.4 Pricing hooks (for later)

CCF = core Professional. PCF/LCA/EPD are natural **add-on modules** (per-product or
per-EPD pricing is the industry norm — EPD consultancies charge €5-15k per EPD; a
self-serve "EPD-ready dataset" at a fraction of that is a real wedge). Fits the existing
add-on lane (site-pack/seat pattern) once Stripe is live.

---

## Sources

- GHGP Corporate Standard revision: [Corporate Standard Phase 1 Progress Update Dec 2025](https://ghgprotocol.org/sites/default/files/2025-12/CS-Phase1-ProgressUpdate.pdf) · [Scope 3 Phase 1 Update Mar 2026](https://ghgprotocol.org/sites/default/files/2026-03/S3-Phase1ProgressUpdate-20260331.pdf) · [Trellis: 2026 methodology timelines](https://trellis.net/article/2026-updates-4-key-esg-methodologies/)
- PACT: [PACT Methodology v3 (WBCSD)](https://www.wbcsd.org/resources/pact-methodology-version-3/) · [PCF Data Exchange Tech Spec v3.0.3](https://wbcsd.github.io/tr/data-exchange-protocol/latest/) · [ISO 14067 2026 guide](https://asuene.com/us/blog/product-carbon-footprint-under-iso-14067-2026-compliance-guide)
- EPD/EN 15804: [One Click LCA on EN 15804+A2](https://oneclicklca.com/en/resources/articles/en-15804-changes-epds) · [ECO Platform Verification Guidelines V8.0](https://www.eco-platform.org/files/download/Documents/2025/Verification%20Guidelines_V8.0.pdf) · [EPD data requirements 2026](https://epd.guide/epd-data-sources/epd-data-requirements-for-2026-clarified) · [EN 15804+A2 PCR (Environdec)](https://www.environdec.com/pcr-library/pcr_6b99d07c-4b75-4763-4485-08dd775d2e49)
- Battery Regulation: [EUR-Lex summary](https://eur-lex.europa.eu/EN/legal-content/summary/sustainability-rules-for-batteries-and-waste-batteries.html) · [Carbon footprint declaration deadlines](https://prodlaw.eu/2026/01/eu-battery-regulation-what-is-the-carbon-footprint-declaration-and-when-does-it-become-mandatory/)
- CSRD/Omnibus: [Commonwealth Climate Law: CSRD post-Omnibus 2026](https://commonwealthclimatelaw.org/publication/csrd-reporting-post-omnibus-i-what-directors-need-to-know-in-2026/) · [KPMG: EU agrees Omnibus changes](https://kpmg.com/xx/en/our-insights/ifrg/2025/esrs-eu-omnibus.html) · [Deloitte: Omnibus + ESRS updates Jan 2026](https://dart.deloitte.com/USDART/home/publications/deloitte/heads-up/2026/eu-sustainability-reporting-omnibus-esrs-updates)
