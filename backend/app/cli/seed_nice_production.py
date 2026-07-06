"""
Seed NICE demo data directly into production PostgreSQL using sync psycopg2.
Bypasses async SQLAlchemy which has connection timeout issues over public networks.

Usage:
    DATABASE_URL="postgresql://user:pass@host:port/db" python -m app.cli.seed_nice_production
"""

import os
import sys
import random
import uuid
from datetime import date, datetime

import psycopg2
from psycopg2.extras import execute_values

# Get DATABASE_URL from env
DB_URL = os.environ.get("DATABASE_URL", "")
if not DB_URL:
    print("ERROR: Set DATABASE_URL environment variable")
    sys.exit(1)

# Strip async prefix if present
DB_URL = DB_URL.replace("postgresql+asyncpg://", "postgresql://")

# Password hash for "NiceDemo2025!" (pre-computed bcrypt)
try:
    from passlib.context import CryptContext

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    PASSWORD_HASH = pwd_context.hash("NiceDemo2025!")
except ImportError:
    PASSWORD_HASH = "$2b$12$placeholder"  # fallback


NICE_SITES = [
    {
        "name": "Ra'anana HQ",
        "country_code": "IL",
        "address": "13 Zarchin St, Ra'anana",
        "grid_region": "IL",
        "employees": 1800,
    },
    {
        "name": "Hoboken NJ (Americas HQ)",
        "country_code": "US",
        "address": "221 River St, Hoboken, NJ",
        "grid_region": "US",
        "employees": 1200,
    },
    {
        "name": "Richardson TX",
        "country_code": "US",
        "address": "Richardson, TX",
        "grid_region": "US",
        "employees": 600,
    },
    {
        "name": "Sandy UT",
        "country_code": "US",
        "address": "Sandy, UT",
        "grid_region": "US",
        "employees": 500,
    },
    {
        "name": "Atlanta GA",
        "country_code": "US",
        "address": "Atlanta, GA",
        "grid_region": "US",
        "employees": 350,
    },
    {
        "name": "London",
        "country_code": "GB",
        "address": "London, United Kingdom",
        "grid_region": "UK",
        "employees": 400,
    },
    {
        "name": "Pune R&D Center",
        "country_code": "IN",
        "address": "Pune, Maharashtra, India",
        "grid_region": "Global",
        "employees": 1500,
    },
    {
        "name": "Bangalore",
        "country_code": "IN",
        "address": "Bangalore, Karnataka, India",
        "grid_region": "Global",
        "employees": 800,
    },
    {
        "name": "Manila Support Center",
        "country_code": "PH",
        "address": "BGC, Taguig, Manila",
        "grid_region": "Global",
        "employees": 350,
    },
    {
        "name": "Singapore",
        "country_code": "SG",
        "address": "Singapore",
        "grid_region": "Global",
        "employees": 150,
    },
    {
        "name": "Frankfurt",
        "country_code": "DE",
        "address": "Frankfurt am Main, Germany",
        "grid_region": "EU",
        "employees": 200,
    },
    {
        "name": "Tokyo",
        "country_code": "JP",
        "address": "Tokyo, Japan",
        "grid_region": "Global",
        "employees": 120,
    },
    {
        "name": "Denver CO",
        "country_code": "US",
        "address": "Denver, CO",
        "grid_region": "US",
        "employees": 300,
    },
    {
        "name": "Lod (Actimize R&D)",
        "country_code": "IL",
        "address": "Lod, Israel",
        "grid_region": "IL",
        "employees": 400,
    },
]

ELECTRICITY_KEYS = {
    "IL": "electricity_il",
    "US": "electricity_us",
    "GB": "electricity_uk",
    "IN": "electricity_in",
    "SG": "electricity_sg",
    "DE": "electricity_de",
    "JP": "electricity_jp",
    "PH": "electricity_global",
}


def generate_activities(site, year=2025):
    """Generate activity dicts for a site."""
    activities = []
    emp = site["employees"]
    cc = site["country_code"]
    elec_key = ELECTRICITY_KEYS.get(cc, "electricity_global")

    # Scope 1.1 - Diesel generators
    gen_mult = 1.5 if cc in ("IN", "PH", "IL") else 0.5
    monthly_diesel = emp * 0.08 * gen_mult
    if monthly_diesel > 5:
        for m in range(1, 13):
            activities.append(
                {
                    "scope": 1,
                    "cat": "1.1",
                    "key": "diesel_liters",
                    "desc": f"Backup generator diesel — {date(year,m,1).strftime('%B')}",
                    "qty": round(monthly_diesel * random.uniform(0.7, 1.3), 1),
                    "unit": "liters",
                    "dt": date(year, m, 15),
                }
            )

    # Scope 1.2 - Fleet
    if cc in ("IL", "US") and emp >= 300:
        cars = max(5, emp // 80)
        for m in range(1, 13):
            activities.append(
                {
                    "scope": 1,
                    "cat": "1.2",
                    "key": "car_petrol_km",
                    "desc": f"Company fleet ({cars} vehicles) — {date(year,m,1).strftime('%B')}",
                    "qty": round(cars * 1800 * random.uniform(0.8, 1.2)),
                    "unit": "km",
                    "dt": date(year, m, 15),
                }
            )

    # Scope 1.3 - Refrigerants
    if emp >= 200:
        activities.append(
            {
                "scope": 1,
                "cat": "1.3",
                "key": "refrigerant_r410a",
                "desc": "HVAC refrigerant R-410A annual top-up",
                "qty": round(emp * 0.015 * random.uniform(0.6, 1.4), 2),
                "unit": "kg",
                "dt": date(year, 6, 15),
            }
        )

    # Scope 2 - Electricity
    kwh_base = 375
    if cc in ("IN", "PH"):
        kwh_base = 280
    elif cc == "SG":
        kwh_base = 420
    for m in range(1, 13):
        s = (
            1.25
            if m in (7, 8)
            else (1.15 if m in (1, 2, 12) and cc not in ("SG", "PH", "IN") else 1.0)
        )
        activities.append(
            {
                "scope": 2,
                "cat": "2",
                "key": elec_key,
                "desc": f"Purchased electricity — {date(year,m,1).strftime('%B')}",
                "qty": round(emp * kwh_base * s * random.uniform(0.92, 1.08)),
                "unit": "kWh",
                "dt": date(year, m, 15),
            }
        )

    # Scope 3.1 - Purchased goods (quarterly)
    for q, mo in [(1, 3), (2, 6), (3, 9), (4, 12)]:
        activities.append(
            {
                "scope": 3,
                "cat": "3.1",
                "key": "spend_it_equipment",
                "desc": f"IT equipment & software — Q{q}",
                "qty": round(emp * 200 * random.uniform(0.8, 1.3)),
                "unit": "USD",
                "dt": date(year, mo, 28),
            }
        )
        activities.append(
            {
                "scope": 3,
                "cat": "3.1",
                "key": "spend_office_supplies",
                "desc": f"Office supplies — Q{q}",
                "qty": round(emp * 80 * random.uniform(0.7, 1.2)),
                "unit": "USD",
                "dt": date(year, mo, 28),
            }
        )
        if emp >= 200:
            activities.append(
                {
                    "scope": 3,
                    "cat": "3.1",
                    "key": "spend_food_beverages",
                    "desc": f"Cafeteria & catering — Q{q}",
                    "qty": round(emp * 120 * random.uniform(0.8, 1.1)),
                    "unit": "USD",
                    "dt": date(year, mo, 28),
                }
            )

    # Scope 3.5 - Waste
    waste_kg = emp * 1.5
    for m in range(1, 13):
        q = waste_kg * random.uniform(0.7, 1.3)
        activities.append(
            {
                "scope": 3,
                "cat": "3.5",
                "key": "waste_recycled_mixed",
                "desc": f"Recycled waste — {date(year,m,1).strftime('%B')}",
                "qty": round(q * 0.6, 1),
                "unit": "kg",
                "dt": date(year, m, 28),
            }
        )
        activities.append(
            {
                "scope": 3,
                "cat": "3.5",
                "key": "waste_landfill_mixed",
                "desc": f"Landfill waste — {date(year,m,1).strftime('%B')}",
                "qty": round(q * 0.4, 1),
                "unit": "kg",
                "dt": date(year, m, 28),
            }
        )

    # Scope 3.6 - Flights
    fpe = 3.0 if cc in ("IL", "US") else 2.0
    if emp < 200:
        fpe = 1.5
    sh = emp * fpe / 12 * 800
    lh = emp * fpe / 12 * 4000
    for m in range(1, 13):
        tf = 0.6 if m in (7, 8, 12) else 1.15
        if sh > 100:
            activities.append(
                {
                    "scope": 3,
                    "cat": "3.6",
                    "key": "flight_short_economy",
                    "desc": f"Short-haul flights — {date(year,m,1).strftime('%B')}",
                    "qty": round(sh * 0.4 * tf * random.uniform(0.8, 1.2)),
                    "unit": "km",
                    "dt": date(year, m, 20),
                }
            )
        if lh > 100:
            activities.append(
                {
                    "scope": 3,
                    "cat": "3.6",
                    "key": "flight_long_economy",
                    "desc": f"Long-haul flights (economy) — {date(year,m,1).strftime('%B')}",
                    "qty": round(lh * 0.5 * tf * random.uniform(0.8, 1.2)),
                    "unit": "km",
                    "dt": date(year, m, 20),
                }
            )
            activities.append(
                {
                    "scope": 3,
                    "cat": "3.6",
                    "key": "flight_long_business",
                    "desc": f"Long-haul flights (business) — {date(year,m,1).strftime('%B')}",
                    "qty": round(lh * 0.1 * tf * random.uniform(0.7, 1.3)),
                    "unit": "km",
                    "dt": date(year, m, 20),
                }
            )

    # Scope 3.6 - Hotels
    hn = emp * fpe / 12 * 2.5
    for m in range(1, 13):
        tf = 0.6 if m in (7, 8, 12) else 1.15
        if hn > 5:
            activities.append(
                {
                    "scope": 3,
                    "cat": "3.6",
                    "key": "hotel_night",
                    "desc": f"Hotel stays — {date(year,m,1).strftime('%B')}",
                    "qty": round(hn * tf * random.uniform(0.8, 1.2)),
                    "unit": "nights",
                    "dt": date(year, m, 20),
                }
            )

    # Scope 3.7 - Commuting
    car_pct = 0.70 if cc in ("IL", "US") else 0.30
    bus_pct = 0.15 if cc in ("IN", "PH") else 0.10
    rail_pct = 1.0 - car_pct - bus_pct
    for m in range(1, 13):
        vf = 0.7 if m in (8, 12) else 1.0
        car_km = emp * car_pct * 25 * 2 * 21 * vf
        if car_km > 0:
            activities.append(
                {
                    "scope": 3,
                    "cat": "3.7",
                    "key": "commute_car_petrol",
                    "desc": f"Commuting by car — {date(year,m,1).strftime('%B')}",
                    "qty": round(car_km * random.uniform(0.9, 1.1)),
                    "unit": "km",
                    "dt": date(year, m, 28),
                }
            )
        rail_km = emp * rail_pct * 25 * 2 * 21 * vf
        if rail_km > 1000:
            activities.append(
                {
                    "scope": 3,
                    "cat": "3.7",
                    "key": "commute_rail",
                    "desc": f"Commuting by train — {date(year,m,1).strftime('%B')}",
                    "qty": round(rail_km * random.uniform(0.9, 1.1)),
                    "unit": "km",
                    "dt": date(year, m, 28),
                }
            )
        bus_km = emp * bus_pct * 25 * 2 * 21 * vf
        if bus_km > 1000:
            activities.append(
                {
                    "scope": 3,
                    "cat": "3.7",
                    "key": "commute_bus",
                    "desc": f"Commuting by bus — {date(year,m,1).strftime('%B')}",
                    "qty": round(bus_km * random.uniform(0.9, 1.1)),
                    "unit": "km",
                    "dt": date(year, m, 28),
                }
            )

    return activities


def main():
    print("Connecting to production database...")
    conn = psycopg2.connect(DB_URL)
    conn.autocommit = False
    cur = conn.cursor()

    # Check if NICE already exists
    cur.execute("SELECT id FROM organizations WHERE name = 'NICE Ltd'")
    existing = cur.fetchone()
    if existing:
        org_id = existing[0]
        print(f"Cleaning up existing NICE data (org_id={org_id})...")
        cur.execute(
            "DELETE FROM emissions WHERE activity_id IN (SELECT id FROM activities WHERE organization_id = %s)",
            (org_id,),
        )
        cur.execute("DELETE FROM activities WHERE organization_id = %s", (org_id,))
        cur.execute("DELETE FROM import_batches WHERE organization_id = %s", (org_id,))
        cur.execute(
            "DELETE FROM roadmap_milestones WHERE scenario_id IN (SELECT id FROM scenarios WHERE organization_id = %s)",
            (org_id,),
        )
        cur.execute(
            "DELETE FROM scenario_initiatives WHERE scenario_id IN (SELECT id FROM scenarios WHERE organization_id = %s)",
            (org_id,),
        )
        cur.execute("DELETE FROM scenarios WHERE organization_id = %s", (org_id,))
        cur.execute(
            "DELETE FROM emission_checkpoints WHERE organization_id = %s", (org_id,)
        )
        cur.execute(
            "DELETE FROM decarbonization_targets WHERE organization_id = %s", (org_id,)
        )
        cur.execute("DELETE FROM sites WHERE organization_id = %s", (org_id,))
        cur.execute(
            "DELETE FROM reporting_periods WHERE organization_id = %s", (org_id,)
        )
        cur.execute("DELETE FROM users WHERE organization_id = %s", (org_id,))
        cur.execute("DELETE FROM organizations WHERE id = %s", (org_id,))
        conn.commit()
        print("  Cleaned.")

    # Create org
    org_id = str(uuid.uuid4())
    print("Creating NICE Ltd organization...")
    cur.execute(
        """INSERT INTO organizations (id, name, country_code, industry_code, base_year, default_region, subscription_plan, is_active, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
        (
            org_id,
            "NICE Ltd",
            "IL",
            "software",
            2024,
            "IL",
            "enterprise",
            True,
            datetime.utcnow(),
        ),
    )

    # Create user
    user_id = str(uuid.uuid4())
    cur.execute(
        """INSERT INTO users (id, email, full_name, role, is_active, organization_id, hashed_password, onboarding_completed, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
        (
            user_id,
            "demo@nice.com",
            "Demo Admin",
            "ADMIN",
            True,
            org_id,
            PASSWORD_HASH,
            True,
            datetime.utcnow(),
        ),
    )

    # Create period
    period_id = str(uuid.uuid4())
    cur.execute(
        """INSERT INTO reporting_periods (id, organization_id, name, start_date, end_date, is_locked, status, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
        (
            period_id,
            org_id,
            "FY 2025",
            date(2025, 1, 1),
            date(2025, 12, 31),
            False,
            "draft",
            datetime.utcnow(),
        ),
    )

    # Create sites
    print("Creating 14 sites...")
    site_ids = {}
    for s in NICE_SITES:
        sid = str(uuid.uuid4())
        site_ids[s["name"]] = sid
        cur.execute(
            """INSERT INTO sites (id, organization_id, name, country_code, address, grid_region, is_active, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
            (
                sid,
                org_id,
                s["name"],
                s["country_code"],
                s["address"],
                s["grid_region"],
                True,
                datetime.utcnow(),
            ),
        )

    conn.commit()

    # Build emission factor lookup: activity_key -> (id, co2e_factor, activity_unit)
    print("Loading emission factors...")
    cur.execute(
        "SELECT id, activity_key, co2e_factor, activity_unit FROM emission_factors WHERE is_active = true AND status = 'approved'"
    )
    ef_map = {}
    for row in cur.fetchall():
        ef_id, akey, co2e, aunit = row
        ef_map[akey] = (str(ef_id), float(co2e), aunit)

    # Generate and insert activities + emissions in bulk
    total_acts = 0
    total_co2e = 0.0
    skipped = 0

    for site_data in NICE_SITES:
        site_id = site_ids[site_data["name"]]
        acts = generate_activities(site_data)
        print(f"  {site_data['name']}: {len(acts)} activities...", end=" ", flush=True)

        act_rows = []
        em_rows = []

        for a in acts:
            ef = ef_map.get(a["key"])
            if not ef:
                skipped += 1
                continue

            ef_id, co2e_factor, _ = ef
            act_id = str(uuid.uuid4())
            em_id = str(uuid.uuid4())
            qty = float(a["qty"])
            co2e_kg = qty * co2e_factor

            act_rows.append(
                (
                    act_id,
                    org_id,
                    period_id,
                    site_id,
                    a["scope"],
                    a["cat"],
                    a["key"],
                    a["desc"],
                    a["qty"],
                    a["unit"],
                    "activity",
                    a["dt"],
                    "import",
                    user_id,
                    3,
                    datetime.utcnow(),
                )
            )

            em_rows.append(
                (
                    em_id,
                    act_id,
                    ef_id,
                    round(co2e_kg, 4),
                    round(co2e_kg, 4),  # co2e_kg and co2_kg simplified
                    None,
                    None,
                    None,  # ch4, n2o, wtt
                    a["qty"],
                    a["unit"],
                    f"{qty} {a['unit']} × {co2e_factor} = {co2e_kg:.2f} kg CO2e",
                    "high",
                    "exact",
                    False,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    datetime.utcnow(),
                    None,
                )
            )

            total_co2e += co2e_kg
            total_acts += 1

        # Bulk insert activities
        execute_values(
            cur,
            """INSERT INTO activities
            (id, organization_id, reporting_period_id, site_id,
             scope, category_code, activity_key, description,
             quantity, unit, calculation_method, activity_date,
             data_source, created_by, data_quality_score, created_at)
            VALUES %s""",
            act_rows,
        )

        # Bulk insert emissions
        execute_values(
            cur,
            """INSERT INTO emissions
            (id, activity_id, emission_factor_id,
             co2e_kg, co2_kg, ch4_kg, n2o_kg, wtt_co2e_kg,
             converted_quantity, converted_unit,
             formula, confidence, resolution_strategy,
             needs_review, warnings,
             factor_year, factor_region, method_hierarchy,
             location_co2e_kg, market_co2e_kg,
             calculated_at, recalculated_at)
            VALUES %s""",
            em_rows,
        )

        conn.commit()
        print(f"OK ({total_acts} total)")

    # ==========================================
    # DECARBONIZATION: Initiatives + Target + Scenario
    # ==========================================
    print("\nSeeding initiative library...")

    # Check if initiatives exist
    cur.execute("SELECT count(*) FROM initiatives")
    init_count = cur.fetchone()[0]
    if init_count == 0:
        from app.cli.seed_decarbonization import INITIATIVES

        for data in INITIATIVES:
            init_id = str(uuid.uuid4())
            cur.execute(
                """INSERT INTO initiatives
                (id, category, subcategory, name, short_description,
                 applicable_scopes, applicable_category_codes, applicable_activity_keys,
                 typical_reduction_percent_min, typical_reduction_percent_max, typical_reduction_percent_median,
                 typical_capex_per_tco2e_reduced, typical_opex_change_percent,
                 typical_payback_years_min, typical_payback_years_max,
                 complexity, implementation_time_months_min, implementation_time_months_max,
                 co_benefits, common_barriers, is_active, created_at)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                (
                    init_id,
                    data["category"],
                    data.get("subcategory"),
                    data["name"],
                    data["short_description"],
                    psycopg2.extras.Json(data["applicable_scopes"]),
                    psycopg2.extras.Json(data["applicable_category_codes"]),
                    psycopg2.extras.Json(data["applicable_activity_keys"]),
                    data["typical_reduction_percent_min"],
                    data["typical_reduction_percent_max"],
                    data["typical_reduction_percent_median"],
                    data.get("typical_capex_per_tco2e_reduced"),
                    data.get("typical_opex_change_percent"),
                    data.get("typical_payback_years_min"),
                    data.get("typical_payback_years_max"),
                    data["complexity"],
                    data["implementation_time_months_min"],
                    data["implementation_time_months_max"],
                    psycopg2.extras.Json(data.get("co_benefits")),
                    psycopg2.extras.Json(data.get("common_barriers")),
                    True,
                    datetime.utcnow(),
                ),
            )
        conn.commit()
        print(f"  Seeded {len(INITIATIVES)} initiatives.")
    else:
        print(f"  Initiatives already exist ({init_count}). Skipping.")

    # Create target
    print("Creating decarbonization target...")
    total_tco2e = total_co2e / 1000
    target_reduction = 40
    target_emissions = total_tco2e * (1 - target_reduction / 100)

    target_id = str(uuid.uuid4())
    cur.execute(
        """INSERT INTO decarbonization_targets
        (id, organization_id, name, description, target_type, framework,
         base_year, base_year_period_id, base_year_emissions_tco2e,
         target_year, target_reduction_percent, target_emissions_tco2e,
         includes_scope1, includes_scope2, includes_scope3, scope3_categories,
         is_sbti_validated, is_public, is_active, created_at, created_by_id)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
        (
            target_id,
            org_id,
            "NICE 2030 Climate Target",
            "Board-approved: 40% absolute reduction by 2030, SBTi 1.5°C aligned.",
            "absolute",
            "sbti_1_5c",
            2025,
            period_id,
            round(total_tco2e, 2),
            2030,
            target_reduction,
            round(target_emissions, 2),
            True,
            True,
            True,
            psycopg2.extras.Json(["3.1", "3.5", "3.6", "3.7"]),
            False,
            True,
            True,
            datetime.utcnow(),
            user_id,
        ),
    )

    # Create scenario
    scenario_id = str(uuid.uuid4())
    cur.execute(
        """INSERT INTO scenarios
        (id, organization_id, target_id, name, description, scenario_type,
         is_active, total_reduction_tco2e, total_investment, total_annual_savings,
         weighted_payback_years, target_achievement_percent,
         carbon_price_scenario, assumed_carbon_price_2030, created_at, created_by_id)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
        (
            scenario_id,
            org_id,
            target_id,
            "NICE Accelerated Decarbonization Plan",
            "Comprehensive plan: renewable energy, fleet electrification, travel policy, efficiency.",
            "aggressive",
            True,
            26730,
            3010000,
            3825000,
            3.2,
            97,
            "moderate",
            75,
            datetime.utcnow(),
            user_id,
        ),
    )

    # Add scenario initiatives
    print("Adding scenario initiatives...")
    cur.execute("SELECT id, name FROM initiatives")
    init_map = {row[1]: str(row[0]) for row in cur.fetchall()}

    scenario_inits = [
        (
            "Renewable Energy Procurement (PPA/Green Tariff)",
            "electricity_il",
            11500,
            90,
            50000,
            120000,
            0,
            "2025-07-01",
            "2026-01-01",
            "in_progress",
            1,
        ),
        (
            "Smart HVAC Controls & Optimization",
            "electricity_us",
            2300,
            18,
            460000,
            -180000,
            180000,
            "2025-10-01",
            "2026-06-01",
            "planned",
            2,
        ),
        (
            "Virtual-First Travel Policy",
            "flight_long_economy",
            3800,
            35,
            50000,
            -2500000,
            2500000,
            "2025-04-01",
            "2025-07-01",
            "in_progress",
            3,
        ),
        (
            "Hybrid Work Policy (3 days office)",
            "commute_car_petrol",
            4200,
            40,
            200000,
            -800000,
            800000,
            "2025-01-01",
            "2025-03-01",
            "completed",
            4,
        ),
        (
            "Fleet Electrification",
            "car_petrol_km",
            850,
            80,
            1200000,
            -200000,
            200000,
            "2026-01-01",
            "2028-06-01",
            "planned",
            5,
        ),
        (
            "LED Lighting Retrofit",
            "electricity_in",
            650,
            8,
            120000,
            -95000,
            95000,
            "2025-09-01",
            "2026-03-01",
            "planned",
            6,
        ),
        (
            "Zero Waste to Landfill Program",
            "waste_landfill_mixed",
            280,
            70,
            80000,
            -30000,
            30000,
            "2025-06-01",
            "2026-06-01",
            "planned",
            7,
        ),
        (
            "Low-GWP Refrigerant Transition",
            "refrigerant_r410a",
            450,
            65,
            350000,
            -20000,
            20000,
            "2026-01-01",
            "2028-12-31",
            "planned",
            8,
        ),
        (
            "Sustainable IT Procurement Policy",
            "spend_it_equipment",
            1500,
            15,
            0,
            0,
            0,
            "2025-07-01",
            "2025-12-31",
            "planned",
            9,
        ),
        (
            "Employee Shuttle / Carpool Program",
            "commute_car_petrol",
            1200,
            22,
            500000,
            350000,
            0,
            "2026-03-01",
            "2026-09-01",
            "planned",
            10,
        ),
    ]

    for si in scenario_inits:
        (
            name,
            akey,
            red_tco2e,
            red_pct,
            capex,
            opex,
            savings,
            start,
            end,
            status,
            priority,
        ) = si
        iid = init_map.get(name)
        if not iid:
            print(f"  WARN: Initiative '{name}' not found")
            continue
        si_id = str(uuid.uuid4())
        cur.execute(
            """INSERT INTO scenario_initiatives
            (id, scenario_id, initiative_id, target_activity_key,
             expected_reduction_tco2e, expected_reduction_percent,
             capex, annual_opex_change, annual_savings,
             implementation_start, implementation_end,
             status, priority_order, created_at)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (
                si_id,
                scenario_id,
                iid,
                akey,
                red_tco2e,
                red_pct,
                capex,
                opex,
                savings,
                start,
                end,
                status,
                priority,
                datetime.utcnow(),
            ),
        )

    # Add milestones
    print("Adding roadmap milestones...")
    milestones = [
        (
            "Quick Wins Complete",
            "Travel policy, hybrid work implemented",
            "2025-12-31",
            2025,
            8000,
            300000,
            round(total_tco2e - 8000, 2),
        ),
        (
            "Renewable Energy Transition",
            "Israel offices on 100% renewable",
            "2026-12-31",
            2026,
            16000,
            1200000,
            round(total_tco2e - 16000, 2),
        ),
        (
            "Fleet & Infrastructure",
            "50% fleet electrified, LED complete",
            "2027-12-31",
            2027,
            21000,
            2500000,
            round(total_tco2e - 21000, 2),
        ),
        (
            "Global Renewable Expansion",
            "US/UK/EU offices renewable",
            "2028-12-31",
            2028,
            24000,
            2800000,
            round(total_tco2e - 24000, 2),
        ),
        (
            "2030 Target Achievement",
            "40% reduction achieved",
            "2030-12-31",
            2030,
            26730,
            3010000,
            round(target_emissions, 2),
        ),
    ]
    for ms in milestones:
        ms_id = str(uuid.uuid4())
        cur.execute(
            """INSERT INTO roadmap_milestones
            (id, scenario_id, name, description, target_date, milestone_year,
             cumulative_reduction_tco2e, cumulative_investment, expected_emissions_tco2e,
             status, created_at)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (
                ms_id,
                scenario_id,
                ms[0],
                ms[1],
                ms[2],
                ms[3],
                ms[4],
                ms[5],
                ms[6],
                "pending",
                datetime.utcnow(),
            ),
        )

    conn.commit()
    conn.close()

    print(f"\n{'='*60}")
    print("NICE Ltd Production Seeding Complete")
    print(f"{'='*60}")
    print("Organization: NICE Ltd")
    print("Login:        demo@nice.com / NiceDemo2025!")
    print(f"Sites:        {len(NICE_SITES)}")
    print(f"Activities:   {total_acts} (skipped: {skipped})")
    print(f"Total CO2e:   {total_tco2e:,.1f} tonnes")
    print(f"Target:       40% reduction by 2030 → {target_emissions:,.0f} tCO2e")
    print("Scenario:     10 initiatives, 97% target achievement")
    print(f"{'='*60}")
    print("\nClient URL: https://climatrix.io")
    print("Email: demo@nice.com")
    print("Password: NiceDemo2025!")


if __name__ == "__main__":
    main()
