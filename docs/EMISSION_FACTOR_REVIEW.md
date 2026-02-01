# Emission Factor Review - CLIMATRIX

**Date:** February 2026
**Reviewer:** Sivan
**Status:** REQUIRES CORRECTION

---

## Summary

The emission factors currently in the system have discrepancies compared to the official DEFRA 2024 and IPCC AR6 values. This document details the required corrections.

---

## Scope 1.1 - Stationary Combustion (Fuels)

| # | Activity Key | Display Name | Current Value | DEFRA 2024 (Sivan) | Difference | Status |
|---|--------------|--------------|---------------|---------------------|------------|--------|
| 4 | diesel_liters | Diesel/Gas Oil | 2.68 | **2.66155** | -0.01845 | NEEDS UPDATE |
| 8 | lng_liters | LNG (Liquefied Natural Gas) | 1.23 | **1.17216** | -0.05784 | NEEDS UPDATE |
| 10 | lpg_liters | LPG (volume) | 1.52 | **1.55713** | +0.03713 | NEEDS UPDATE |

---

## Scope 1.2 - Mobile Combustion (Fuels)

| # | Activity Key | Display Name | Current Value | DEFRA 2024 (Sivan) | Difference | Status |
|---|--------------|--------------|---------------|---------------------|------------|--------|
| 22 | diesel_liters_mobile | Diesel (mobile) | 2.68 | **2.66155** | -0.01845 | NEEDS UPDATE |
| 28 | petrol_liters | Petrol/Gasoline (fuel) | 2.31 | **2.35372** | +0.04372 | NEEDS UPDATE |
| 29 | urea_liters | Urea/AdBlue/DEF | 1.33 | **N/A** | - | NEEDS REVIEW |

**Note:** Urea/AdBlue - need to verify if this should have an emission factor or if it's N/A (not applicable as it's used to REDUCE emissions, not create them).

---

## Scope 1.3 - Fugitive Emissions (Refrigerants)

| # | Activity Key | Display Name | Current Value | Source | IPCC AR6 | DEFRA 2024 | Status |
|---|--------------|--------------|---------------|--------|----------|------------|--------|
| 31 | refrigerant_halon1211 | Halon-1211 (Fire Suppression) | 1890 | IPCC_AR6 | **1960** | **1750** | NEEDS DECISION |
| 50 | refrigerant_r134a | R-134a Refrigerant | 1530 | IPCC_AR6 | 1530 | **1300** | NEEDS DECISION |
| 59 | refrigerant_r410a | R-410A Refrigerant | 2256 | IPCC_AR6 | 2256 | **1130** | NEEDS DECISION |

---

## Key Questions to Resolve

### 1. Source Priority
Which source should take precedence for fuel emission factors?
- **Option A:** DEFRA 2024 (UK Government - most commonly used in Europe)
- **Option B:** EPA (US Government - for US operations)
- **Option C:** Allow user to select source per organization

**Recommendation:** Use DEFRA 2024 as default for Global, allow regional overrides.

### 2. Refrigerant GWP Values
There's significant variance between IPCC AR6 and DEFRA 2024 for refrigerants:
- **IPCC AR6:** Scientific GWP values from latest IPCC assessment
- **DEFRA 2024:** UK Government interpretation/adoption of GWP values

| Refrigerant | IPCC AR6 | DEFRA 2024 | Variance |
|-------------|----------|------------|----------|
| Halon-1211 | 1960 | 1750 | -10.7% |
| R-134a | 1530 | 1300 | -15.0% |
| R-410A | 2256 | 1130 | -49.9% |

**Note:** R-410A has a massive discrepancy (50% difference). This needs verification.

**Questions:**
- Should we use IPCC AR6 for scientific accuracy?
- Should we use DEFRA for regulatory compliance?
- Should we support both and let users choose?

### 3. Urea/AdBlue Factor
The current factor (1.33 kg CO2e/liter) needs verification:
- AdBlue is used to REDUCE NOx emissions from diesel engines
- It may have a small upstream production footprint
- Sivan marked this as "N/A" - need clarification

---

## Proposed Corrections

### Immediate Updates (DEFRA 2024 Fuel Factors)

```python
# Scope 1.1 - Stationary
"diesel_liters": 2.66155,    # was 2.68
"lng_liters": 1.17216,       # was 1.23
"lpg_liters": 1.55713,       # was 1.52

# Scope 1.2 - Mobile
"diesel_liters_mobile": 2.66155,  # was 2.68
"petrol_liters": 2.35372,         # was 2.31
"urea_liters": ???                # was 1.33, Sivan says N/A
```

### Pending Decision (Refrigerants)

Need to decide on source before updating:
- Option A: Update to IPCC AR6 GWP100 (current approach, already in use)
- Option B: Update to DEFRA 2024 values
- Option C: Keep both sources and add source selection

---

## Affected Files

1. `/backend/CORE_DOCS/emission_factors_401.csv` - Master CSV
2. `/backend/app/data/emission_factors.py` - Python seed data
3. `/backend/app/data/emission_factors_expanded.py` - Extended factors

---

## Next Steps

1. [ ] Confirm DEFRA 2024 is the correct source for fuel factors
2. [ ] Decide on refrigerant GWP source (IPCC vs DEFRA)
3. [ ] Clarify Urea/AdBlue treatment
4. [ ] Update emission_factors_401.csv with corrected values
5. [ ] Update emission_factors.py to match
6. [ ] Re-seed database with corrected values
7. [ ] Verify calculations are using updated factors

---

## DEFRA 2024 Reference

The official DEFRA 2024 GHG Conversion Factors can be found at:
https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2024

---

*This document was created to track the emission factor review process.*
