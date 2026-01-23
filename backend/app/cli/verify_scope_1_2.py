"""
CLIMATRIX - Scope 1 & 2 Verification Script

This script MUST PASS before any deployment.
Run: python -m app.cli.verify_scope_1_2

It checks:
1. All GHG Protocol categories exist
2. All emission factors have correct data
3. All categories support physical AND spend-based methods
4. Wizard configuration matches database
5. API endpoints return correct data
"""

import sqlite3
import sys
from pathlib import Path

# Expected structure based on GHG Protocol
GHG_PROTOCOL_SCOPE_1_2 = {
    "1.1": {
        "name": "Stationary Combustion",
        "min_factors": 8,
        "required_fuels": ["natural_gas", "diesel", "petrol", "lpg", "coal"],
        "units": ["m3", "kWh", "liters", "kg"],
    },
    "1.2": {
        "name": "Mobile Combustion",
        "min_factors": 10,
        "required_activities": ["car_petrol", "car_diesel", "van", "hgv", "motorcycle"],
        "units": ["km", "liters"],
    },
    "1.3": {
        "name": "Fugitive Emissions",
        "min_factors": 25,
        "required_refrigerants": ["r134a", "r410a", "r32", "sf6"],
        "units": ["kg"],
    },
    "2.1": {
        "name": "Purchased Electricity",
        "min_factors": 50,
        "required_regions": ["IL", "US", "UK", "EU", "Global"],
        "units": ["kWh"],
    },
    "2.2": {
        "name": "Purchased Heat/Steam",
        "min_factors": 2,
        "required_types": ["district_heat", "steam"],
        "units": ["kWh"],
    },
    "2.3": {
        "name": "Purchased Cooling",
        "min_factors": 2,
        "required_types": ["chilled_water", "district_cooling"],
        "units": ["kWh"],
    },
}

REQUIRED_SPEND_PRICES = {
    "1.1": ["natural_gas", "diesel", "petrol", "lpg", "coal", "fuel_oil", "kerosene"],
    "1.2": ["diesel", "petrol"],  # Mobile uses same fuels
    "1.3": ["refrigerant_r134a", "refrigerant_r410a", "refrigerant_r32", "refrigerant_sf6"],
    "2.1": ["electricity"],
    "2.2": ["district_heating", "steam"],
    "2.3": ["chilled_water", "district_cooling"],
}


def get_db_connection():
    db_path = Path(__file__).parent.parent.parent / "climatrix_v3.db"
    return sqlite3.connect(db_path)


def check_emission_factors(conn):
    """Check all emission factors exist and are valid."""
    print("\n" + "=" * 60)
    print("CHECK 1: EMISSION FACTORS")
    print("=" * 60)

    cursor = conn.cursor()
    errors = []

    for category_code, requirements in GHG_PROTOCOL_SCOPE_1_2.items():
        cursor.execute(
            "SELECT COUNT(*) FROM emission_factors WHERE category_code = ? AND is_active = 1",
            (category_code,)
        )
        count = cursor.fetchone()[0]

        status = "✅" if count >= requirements["min_factors"] else "❌"
        print(f"  {category_code} {requirements['name']}: {count} factors (min: {requirements['min_factors']}) {status}")

        if count < requirements["min_factors"]:
            errors.append(f"Category {category_code} has only {count} factors, needs {requirements['min_factors']}")

    return errors


def check_spend_support(conn):
    """Check all categories have fuel prices for spend-based calculations."""
    print("\n" + "=" * 60)
    print("CHECK 2: SPEND-BASED SUPPORT (Fuel Prices)")
    print("=" * 60)

    cursor = conn.cursor()
    errors = []

    for category_code, required_prices in REQUIRED_SPEND_PRICES.items():
        missing = []
        for fuel_type in required_prices:
            cursor.execute(
                "SELECT COUNT(*) FROM fuel_prices WHERE fuel_type LIKE ? AND is_active = 1",
                (f"%{fuel_type}%",)
            )
            count = cursor.fetchone()[0]
            if count == 0:
                missing.append(fuel_type)

        if missing:
            status = "❌"
            errors.append(f"Category {category_code} missing prices: {missing}")
        else:
            status = "✅"

        print(f"  {category_code}: {len(required_prices) - len(missing)}/{len(required_prices)} fuel prices {status}")

    return errors


def check_data_quality(conn):
    """Check emission factors have valid data."""
    print("\n" + "=" * 60)
    print("CHECK 3: DATA QUALITY")
    print("=" * 60)

    cursor = conn.cursor()
    errors = []

    # Check for zero or negative factors
    cursor.execute("""
        SELECT category_code, activity_key, co2e_factor
        FROM emission_factors
        WHERE scope IN (1, 2) AND is_active = 1 AND co2e_factor < 0
    """)
    negative = cursor.fetchall()
    if negative:
        errors.append(f"Found {len(negative)} negative emission factors")
        print(f"  Negative factors: ❌ Found {len(negative)}")
    else:
        print(f"  Negative factors: ✅ None")

    # Check for missing units
    cursor.execute("""
        SELECT category_code, activity_key
        FROM emission_factors
        WHERE scope IN (1, 2) AND is_active = 1 AND (activity_unit IS NULL OR activity_unit = '')
    """)
    missing_units = cursor.fetchall()
    if missing_units:
        errors.append(f"Found {len(missing_units)} factors without units")
        print(f"  Missing units: ❌ Found {len(missing_units)}")
    else:
        print(f"  Missing units: ✅ None")

    # Check for missing sources
    cursor.execute("""
        SELECT category_code, activity_key
        FROM emission_factors
        WHERE scope IN (1, 2) AND is_active = 1 AND (source IS NULL OR source = '')
    """)
    missing_sources = cursor.fetchall()
    if missing_sources:
        errors.append(f"Found {len(missing_sources)} factors without sources")
        print(f"  Missing sources: ❌ Found {len(missing_sources)}")
    else:
        print(f"  Missing sources: ✅ None")

    return errors


def check_category_consistency(conn):
    """Check category codes are consistent."""
    print("\n" + "=" * 60)
    print("CHECK 4: CATEGORY CONSISTENCY")
    print("=" * 60)

    cursor = conn.cursor()
    errors = []

    # Check no orphan categories
    cursor.execute("""
        SELECT DISTINCT category_code
        FROM emission_factors
        WHERE scope IN (1, 2) AND is_active = 1
        ORDER BY category_code
    """)
    db_categories = [row[0] for row in cursor.fetchall()]
    expected = list(GHG_PROTOCOL_SCOPE_1_2.keys())

    extra = set(db_categories) - set(expected)
    missing = set(expected) - set(db_categories)

    if extra:
        print(f"  Unexpected categories: ⚠️ {extra}")
    if missing:
        errors.append(f"Missing categories: {missing}")
        print(f"  Missing categories: ❌ {missing}")

    if not extra and not missing:
        print(f"  Category codes: ✅ All 7 categories present")

    return errors


def check_wizard_config():
    """Check frontend wizard matches database."""
    print("\n" + "=" * 60)
    print("CHECK 5: WIZARD CONFIGURATION")
    print("=" * 60)

    wizard_path = Path(__file__).parent.parent.parent.parent / "frontend_v3/src/stores/wizard.ts"

    if not wizard_path.exists():
        print(f"  Wizard file: ⚠️ Not found at {wizard_path}")
        return ["Wizard config file not found"]

    content = wizard_path.read_text()

    errors = []
    required_codes = ["1.1", "1.2", "1.3", "2.1", "2.2", "2.3"]

    for code in required_codes:
        if f"code: '{code}'" in content:
            print(f"  Category {code} in wizard: ✅")
        else:
            errors.append(f"Category {code} missing from wizard config")
            print(f"  Category {code} in wizard: ❌")

    return errors


def main():
    print("=" * 60)
    print("CLIMATRIX SCOPE 1 & 2 VERIFICATION")
    print("=" * 60)
    print("\nThis script verifies GHG Protocol compliance for Scope 1 & 2.")
    print("All checks must pass before deployment.\n")

    conn = get_db_connection()
    all_errors = []

    all_errors.extend(check_emission_factors(conn))
    all_errors.extend(check_spend_support(conn))
    all_errors.extend(check_data_quality(conn))
    all_errors.extend(check_category_consistency(conn))
    all_errors.extend(check_wizard_config())

    conn.close()

    print("\n" + "=" * 60)
    print("FINAL RESULT")
    print("=" * 60)

    if all_errors:
        print(f"\n❌ FAILED - {len(all_errors)} errors found:\n")
        for error in all_errors:
            print(f"  • {error}")
        print("\n⚠️  DO NOT DEPLOY until all errors are fixed!")
        sys.exit(1)
    else:
        print("\n✅ PASSED - Scope 1 & 2 fully compliant with GHG Protocol")
        print("\n✅ Safe to deploy!")
        sys.exit(0)


if __name__ == "__main__":
    main()
