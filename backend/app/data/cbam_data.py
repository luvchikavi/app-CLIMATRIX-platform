"""
CBAM Reference Data

EU Carbon Border Adjustment Mechanism (Regulation 2023/956)
Default values for embedded emissions calculations.

Sources:
- EU Commission Implementing Regulation 2023/2547
- EU Commission default values for transitional period
- Third-country grid emission factors from IEA/EU Commission
"""

from decimal import Decimal
from datetime import date

# ============================================================================
# CBAM DEFAULT SPECIFIC EMBEDDED EMISSIONS (SEE)
# tCO2e per tonne of product
# Source: EU Commission default values
# ============================================================================

CBAM_DEFAULT_VALUES = [
    # -------------------------------------------------------------------------
    # CEMENT (CN 2523)
    # -------------------------------------------------------------------------
    {
        "cn_code": "2523_10_00",
        "sector": "cement",
        "product_description": "Cement clinker",
        "direct_see": Decimal("0.756"),
        "indirect_see": Decimal("0.050"),
        "total_see": Decimal("0.806"),
        "source": "EU Commission Default Values 2024",
        "valid_from": date(2024, 1, 1),
    },
    {
        "cn_code": "2523_21_00",
        "sector": "cement",
        "product_description": "White Portland cement",
        "direct_see": Decimal("0.632"),
        "indirect_see": Decimal("0.080"),
        "total_see": Decimal("0.712"),
        "source": "EU Commission Default Values 2024",
        "valid_from": date(2024, 1, 1),
    },
    {
        "cn_code": "2523_29_00",
        "sector": "cement",
        "product_description": "Other Portland cement",
        "direct_see": Decimal("0.632"),
        "indirect_see": Decimal("0.080"),
        "total_see": Decimal("0.712"),
        "source": "EU Commission Default Values 2024",
        "valid_from": date(2024, 1, 1),
    },
    {
        "cn_code": "2523_30_00",
        "sector": "cement",
        "product_description": "Aluminous cement",
        "direct_see": Decimal("0.425"),
        "indirect_see": Decimal("0.060"),
        "total_see": Decimal("0.485"),
        "source": "EU Commission Default Values 2024",
        "valid_from": date(2024, 1, 1),
    },
    {
        "cn_code": "2523_90_00",
        "sector": "cement",
        "product_description": "Other hydraulic cements",
        "direct_see": Decimal("0.632"),
        "indirect_see": Decimal("0.070"),
        "total_see": Decimal("0.702"),
        "source": "EU Commission Default Values 2024",
        "valid_from": date(2024, 1, 1),
    },

    # -------------------------------------------------------------------------
    # IRON AND STEEL (CN 72, 73)
    # -------------------------------------------------------------------------
    {
        "cn_code": "7201",
        "sector": "iron_steel",
        "product_description": "Pig iron and spiegeleisen",
        "direct_see": Decimal("1.328"),
        "indirect_see": None,
        "total_see": Decimal("1.328"),
        "source": "EU Commission Default Values 2024",
        "valid_from": date(2024, 1, 1),
    },
    {
        "cn_code": "7202",
        "sector": "iron_steel",
        "product_description": "Ferro-alloys",
        "direct_see": Decimal("0.716"),
        "indirect_see": None,
        "total_see": Decimal("0.716"),
        "source": "EU Commission Default Values 2024",
        "valid_from": date(2024, 1, 1),
    },
    {
        "cn_code": "7203",
        "sector": "iron_steel",
        "product_description": "Ferrous products from direct reduction",
        "direct_see": Decimal("0.496"),
        "indirect_see": None,
        "total_see": Decimal("0.496"),
        "source": "EU Commission Default Values 2024",
        "valid_from": date(2024, 1, 1),
    },
    {
        "cn_code": "7206",
        "sector": "iron_steel",
        "product_description": "Iron and non-alloy steel ingots",
        "direct_see": Decimal("0.352"),
        "indirect_see": None,
        "total_see": Decimal("0.352"),
        "source": "EU Commission Default Values 2024",
        "valid_from": date(2024, 1, 1),
    },
    {
        "cn_code": "7207",
        "sector": "iron_steel",
        "product_description": "Semi-finished products of iron/non-alloy steel",
        "direct_see": Decimal("1.115"),
        "indirect_see": None,
        "total_see": Decimal("1.115"),
        "source": "EU Commission Default Values 2024",
        "valid_from": date(2024, 1, 1),
    },
    {
        "cn_code": "7208",
        "sector": "iron_steel",
        "product_description": "Flat-rolled products, hot-rolled, width >= 600mm",
        "direct_see": Decimal("1.297"),
        "indirect_see": None,
        "total_see": Decimal("1.297"),
        "source": "EU Commission Default Values 2024",
        "valid_from": date(2024, 1, 1),
    },
    {
        "cn_code": "7209",
        "sector": "iron_steel",
        "product_description": "Flat-rolled products, cold-rolled, width >= 600mm",
        "direct_see": Decimal("1.442"),
        "indirect_see": None,
        "total_see": Decimal("1.442"),
        "source": "EU Commission Default Values 2024",
        "valid_from": date(2024, 1, 1),
    },
    {
        "cn_code": "7210",
        "sector": "iron_steel",
        "product_description": "Flat-rolled products, plated or coated",
        "direct_see": Decimal("1.545"),
        "indirect_see": None,
        "total_see": Decimal("1.545"),
        "source": "EU Commission Default Values 2024",
        "valid_from": date(2024, 1, 1),
    },
    {
        "cn_code": "7211",
        "sector": "iron_steel",
        "product_description": "Flat-rolled products, width < 600mm, not clad",
        "direct_see": Decimal("1.328"),
        "indirect_see": None,
        "total_see": Decimal("1.328"),
        "source": "EU Commission Default Values 2024",
        "valid_from": date(2024, 1, 1),
    },
    {
        "cn_code": "7212",
        "sector": "iron_steel",
        "product_description": "Flat-rolled products, width < 600mm, clad/coated",
        "direct_see": Decimal("1.486"),
        "indirect_see": None,
        "total_see": Decimal("1.486"),
        "source": "EU Commission Default Values 2024",
        "valid_from": date(2024, 1, 1),
    },
    {
        "cn_code": "7213",
        "sector": "iron_steel",
        "product_description": "Bars and rods, hot-rolled, in coils",
        "direct_see": Decimal("1.207"),
        "indirect_see": None,
        "total_see": Decimal("1.207"),
        "source": "EU Commission Default Values 2024",
        "valid_from": date(2024, 1, 1),
    },
    {
        "cn_code": "7214",
        "sector": "iron_steel",
        "product_description": "Bars and rods, not in coils",
        "direct_see": Decimal("1.248"),
        "indirect_see": None,
        "total_see": Decimal("1.248"),
        "source": "EU Commission Default Values 2024",
        "valid_from": date(2024, 1, 1),
    },
    {
        "cn_code": "7215",
        "sector": "iron_steel",
        "product_description": "Other bars and rods",
        "direct_see": Decimal("1.352"),
        "indirect_see": None,
        "total_see": Decimal("1.352"),
        "source": "EU Commission Default Values 2024",
        "valid_from": date(2024, 1, 1),
    },
    {
        "cn_code": "7216",
        "sector": "iron_steel",
        "product_description": "Angles, shapes and sections",
        "direct_see": Decimal("1.285"),
        "indirect_see": None,
        "total_see": Decimal("1.285"),
        "source": "EU Commission Default Values 2024",
        "valid_from": date(2024, 1, 1),
    },
    {
        "cn_code": "7217",
        "sector": "iron_steel",
        "product_description": "Wire of iron or non-alloy steel",
        "direct_see": Decimal("1.425"),
        "indirect_see": None,
        "total_see": Decimal("1.425"),
        "source": "EU Commission Default Values 2024",
        "valid_from": date(2024, 1, 1),
    },
    {
        "cn_code": "7218",
        "sector": "iron_steel",
        "product_description": "Stainless steel in ingots/other primary forms",
        "direct_see": Decimal("2.156"),
        "indirect_see": None,
        "total_see": Decimal("2.156"),
        "source": "EU Commission Default Values 2024",
        "valid_from": date(2024, 1, 1),
    },
    {
        "cn_code": "7219",
        "sector": "iron_steel",
        "product_description": "Flat-rolled stainless steel, width >= 600mm",
        "direct_see": Decimal("2.456"),
        "indirect_see": None,
        "total_see": Decimal("2.456"),
        "source": "EU Commission Default Values 2024",
        "valid_from": date(2024, 1, 1),
    },
    {
        "cn_code": "7220",
        "sector": "iron_steel",
        "product_description": "Flat-rolled stainless steel, width < 600mm",
        "direct_see": Decimal("2.523"),
        "indirect_see": None,
        "total_see": Decimal("2.523"),
        "source": "EU Commission Default Values 2024",
        "valid_from": date(2024, 1, 1),
    },
    {
        "cn_code": "7301",
        "sector": "iron_steel",
        "product_description": "Sheet piling",
        "direct_see": Decimal("1.356"),
        "indirect_see": None,
        "total_see": Decimal("1.356"),
        "source": "EU Commission Default Values 2024",
        "valid_from": date(2024, 1, 1),
    },
    {
        "cn_code": "7302",
        "sector": "iron_steel",
        "product_description": "Railway or tramway track construction material",
        "direct_see": Decimal("1.298"),
        "indirect_see": None,
        "total_see": Decimal("1.298"),
        "source": "EU Commission Default Values 2024",
        "valid_from": date(2024, 1, 1),
    },
    {
        "cn_code": "7303",
        "sector": "iron_steel",
        "product_description": "Tubes and pipes of cast iron",
        "direct_see": Decimal("1.185"),
        "indirect_see": None,
        "total_see": Decimal("1.185"),
        "source": "EU Commission Default Values 2024",
        "valid_from": date(2024, 1, 1),
    },
    {
        "cn_code": "7304",
        "sector": "iron_steel",
        "product_description": "Seamless tubes and pipes",
        "direct_see": Decimal("1.756"),
        "indirect_see": None,
        "total_see": Decimal("1.756"),
        "source": "EU Commission Default Values 2024",
        "valid_from": date(2024, 1, 1),
    },
    {
        "cn_code": "7305",
        "sector": "iron_steel",
        "product_description": "Other tubes and pipes, diameter > 406.4mm",
        "direct_see": Decimal("1.485"),
        "indirect_see": None,
        "total_see": Decimal("1.485"),
        "source": "EU Commission Default Values 2024",
        "valid_from": date(2024, 1, 1),
    },
    {
        "cn_code": "7306",
        "sector": "iron_steel",
        "product_description": "Other tubes, pipes and hollow profiles",
        "direct_see": Decimal("1.552"),
        "indirect_see": None,
        "total_see": Decimal("1.552"),
        "source": "EU Commission Default Values 2024",
        "valid_from": date(2024, 1, 1),
    },

    # -------------------------------------------------------------------------
    # ALUMINIUM (CN 76)
    # -------------------------------------------------------------------------
    {
        "cn_code": "7601_10_00",
        "sector": "aluminium",
        "product_description": "Unwrought aluminium, not alloyed",
        "direct_see": Decimal("1.576"),
        "indirect_see": Decimal("5.141"),
        "total_see": Decimal("6.717"),
        "source": "EU Commission Default Values 2024",
        "valid_from": date(2024, 1, 1),
    },
    {
        "cn_code": "7601_20_00",
        "sector": "aluminium",
        "product_description": "Aluminium alloys",
        "direct_see": Decimal("0.294"),
        "indirect_see": Decimal("0.958"),
        "total_see": Decimal("1.252"),
        "source": "EU Commission Default Values 2024",
        "valid_from": date(2024, 1, 1),
    },
    {
        "cn_code": "7602",
        "sector": "aluminium",
        "product_description": "Aluminium waste and scrap",
        "direct_see": Decimal("0.121"),
        "indirect_see": Decimal("0.396"),
        "total_see": Decimal("0.517"),
        "source": "EU Commission Default Values 2024",
        "valid_from": date(2024, 1, 1),
    },
    {
        "cn_code": "7603",
        "sector": "aluminium",
        "product_description": "Aluminium powders and flakes",
        "direct_see": Decimal("1.671"),
        "indirect_see": Decimal("5.450"),
        "total_see": Decimal("7.121"),
        "source": "EU Commission Default Values 2024",
        "valid_from": date(2024, 1, 1),
    },
    {
        "cn_code": "7604",
        "sector": "aluminium",
        "product_description": "Aluminium bars, rods and profiles",
        "direct_see": Decimal("1.695"),
        "indirect_see": Decimal("5.529"),
        "total_see": Decimal("7.224"),
        "source": "EU Commission Default Values 2024",
        "valid_from": date(2024, 1, 1),
    },
    {
        "cn_code": "7605",
        "sector": "aluminium",
        "product_description": "Aluminium wire",
        "direct_see": Decimal("1.721"),
        "indirect_see": Decimal("5.612"),
        "total_see": Decimal("7.333"),
        "source": "EU Commission Default Values 2024",
        "valid_from": date(2024, 1, 1),
    },
    {
        "cn_code": "7606",
        "sector": "aluminium",
        "product_description": "Aluminium plates, sheets and strip",
        "direct_see": Decimal("1.752"),
        "indirect_see": Decimal("5.714"),
        "total_see": Decimal("7.466"),
        "source": "EU Commission Default Values 2024",
        "valid_from": date(2024, 1, 1),
    },
    {
        "cn_code": "7607",
        "sector": "aluminium",
        "product_description": "Aluminium foil",
        "direct_see": Decimal("1.856"),
        "indirect_see": Decimal("6.052"),
        "total_see": Decimal("7.908"),
        "source": "EU Commission Default Values 2024",
        "valid_from": date(2024, 1, 1),
    },
    {
        "cn_code": "7608",
        "sector": "aluminium",
        "product_description": "Aluminium tubes and pipes",
        "direct_see": Decimal("1.798"),
        "indirect_see": Decimal("5.863"),
        "total_see": Decimal("7.661"),
        "source": "EU Commission Default Values 2024",
        "valid_from": date(2024, 1, 1),
    },

    # -------------------------------------------------------------------------
    # FERTILISERS (CN 2808, 2814, 3102, 3105)
    # -------------------------------------------------------------------------
    {
        "cn_code": "2808_00_00",
        "sector": "fertiliser",
        "product_description": "Nitric acid; sulphonitric acids",
        "direct_see": Decimal("0.528"),
        "indirect_see": Decimal("0.100"),
        "total_see": Decimal("0.628"),
        "source": "EU Commission Default Values 2024",
        "valid_from": date(2024, 1, 1),
    },
    {
        "cn_code": "2814",
        "sector": "fertiliser",
        "product_description": "Ammonia, anhydrous or in aqueous solution",
        "direct_see": Decimal("1.629"),
        "indirect_see": Decimal("0.200"),
        "total_see": Decimal("1.829"),
        "source": "EU Commission Default Values 2024",
        "valid_from": date(2024, 1, 1),
    },
    {
        "cn_code": "3102_10_00",
        "sector": "fertiliser",
        "product_description": "Urea",
        "direct_see": Decimal("2.233"),
        "indirect_see": Decimal("0.300"),
        "total_see": Decimal("2.533"),
        "source": "EU Commission Default Values 2024",
        "valid_from": date(2024, 1, 1),
    },
    {
        "cn_code": "3102_30_00",
        "sector": "fertiliser",
        "product_description": "Ammonium nitrate",
        "direct_see": Decimal("2.807"),
        "indirect_see": Decimal("0.300"),
        "total_see": Decimal("3.107"),
        "source": "EU Commission Default Values 2024",
        "valid_from": date(2024, 1, 1),
    },
    {
        "cn_code": "3102_40_00",
        "sector": "fertiliser",
        "product_description": "Mixtures of ammonium nitrate with calcium compounds",
        "direct_see": Decimal("2.156"),
        "indirect_see": Decimal("0.250"),
        "total_see": Decimal("2.406"),
        "source": "EU Commission Default Values 2024",
        "valid_from": date(2024, 1, 1),
    },
    {
        "cn_code": "3102_50_00",
        "sector": "fertiliser",
        "product_description": "Sodium nitrate",
        "direct_see": Decimal("1.425"),
        "indirect_see": Decimal("0.180"),
        "total_see": Decimal("1.605"),
        "source": "EU Commission Default Values 2024",
        "valid_from": date(2024, 1, 1),
    },
    {
        "cn_code": "3105_10_00",
        "sector": "fertiliser",
        "product_description": "Fertilisers in tablets or similar forms",
        "direct_see": Decimal("1.856"),
        "indirect_see": Decimal("0.220"),
        "total_see": Decimal("2.076"),
        "source": "EU Commission Default Values 2024",
        "valid_from": date(2024, 1, 1),
    },
    {
        "cn_code": "3105_20_00",
        "sector": "fertiliser",
        "product_description": "NPK fertilisers",
        "direct_see": Decimal("1.523"),
        "indirect_see": Decimal("0.200"),
        "total_see": Decimal("1.723"),
        "source": "EU Commission Default Values 2024",
        "valid_from": date(2024, 1, 1),
    },

    # -------------------------------------------------------------------------
    # ELECTRICITY (CN 2716)
    # -------------------------------------------------------------------------
    {
        "cn_code": "2716_00_00",
        "sector": "electricity",
        "product_description": "Electrical energy",
        "direct_see": Decimal("0.400"),  # Default, varies by country
        "indirect_see": None,
        "total_see": Decimal("0.400"),
        "source": "EU Commission Default Values 2024",
        "valid_from": date(2024, 1, 1),
    },

    # -------------------------------------------------------------------------
    # HYDROGEN (CN 2804 10 00)
    # -------------------------------------------------------------------------
    {
        "cn_code": "2804_10_00_grey",
        "sector": "hydrogen",
        "product_description": "Hydrogen - Grey (Steam Methane Reforming)",
        "direct_see": Decimal("11.900"),
        "indirect_see": None,
        "total_see": Decimal("11.900"),
        "source": "EU Commission Default Values 2024",
        "valid_from": date(2024, 1, 1),
    },
    {
        "cn_code": "2804_10_00_blue",
        "sector": "hydrogen",
        "product_description": "Hydrogen - Blue (SMR with CCS)",
        "direct_see": Decimal("4.500"),
        "indirect_see": None,
        "total_see": Decimal("4.500"),
        "source": "EU Commission Default Values 2024",
        "valid_from": date(2024, 1, 1),
    },
    {
        "cn_code": "2804_10_00_green",
        "sector": "hydrogen",
        "product_description": "Hydrogen - Green (Electrolysis with renewables)",
        "direct_see": Decimal("0.000"),
        "indirect_see": Decimal("0.000"),
        "total_see": Decimal("0.000"),
        "source": "EU Commission Default Values 2024",
        "valid_from": date(2024, 1, 1),
    },
]


# ============================================================================
# THIRD-COUNTRY GRID EMISSION FACTORS
# tCO2e per MWh
# Source: IEA, EU Commission, national reports
# ============================================================================

CBAM_GRID_FACTORS = [
    # Major CBAM-relevant countries
    {"country_code": "CN", "country_name": "China", "grid_factor": Decimal("0.582"), "year": 2023, "source": "IEA 2023"},
    {"country_code": "IN", "country_name": "India", "grid_factor": Decimal("0.708"), "year": 2023, "source": "IEA 2023"},
    {"country_code": "TR", "country_name": "Turkey", "grid_factor": Decimal("0.431"), "year": 2023, "source": "IEA 2023"},
    {"country_code": "RU", "country_name": "Russia", "grid_factor": Decimal("0.327"), "year": 2023, "source": "IEA 2023"},
    {"country_code": "UA", "country_name": "Ukraine", "grid_factor": Decimal("0.345"), "year": 2023, "source": "IEA 2023"},
    {"country_code": "EG", "country_name": "Egypt", "grid_factor": Decimal("0.462"), "year": 2023, "source": "IEA 2023"},
    {"country_code": "ZA", "country_name": "South Africa", "grid_factor": Decimal("0.928"), "year": 2023, "source": "IEA 2023"},
    {"country_code": "BR", "country_name": "Brazil", "grid_factor": Decimal("0.074"), "year": 2023, "source": "IEA 2023"},
    {"country_code": "MX", "country_name": "Mexico", "grid_factor": Decimal("0.423"), "year": 2023, "source": "IEA 2023"},
    {"country_code": "KR", "country_name": "South Korea", "grid_factor": Decimal("0.415"), "year": 2023, "source": "IEA 2023"},
    {"country_code": "JP", "country_name": "Japan", "grid_factor": Decimal("0.457"), "year": 2023, "source": "IEA 2023"},
    {"country_code": "ID", "country_name": "Indonesia", "grid_factor": Decimal("0.761"), "year": 2023, "source": "IEA 2023"},
    {"country_code": "VN", "country_name": "Vietnam", "grid_factor": Decimal("0.524"), "year": 2023, "source": "IEA 2023"},
    {"country_code": "TH", "country_name": "Thailand", "grid_factor": Decimal("0.445"), "year": 2023, "source": "IEA 2023"},
    {"country_code": "MY", "country_name": "Malaysia", "grid_factor": Decimal("0.585"), "year": 2023, "source": "IEA 2023"},
    {"country_code": "PH", "country_name": "Philippines", "grid_factor": Decimal("0.593"), "year": 2023, "source": "IEA 2023"},
    {"country_code": "PK", "country_name": "Pakistan", "grid_factor": Decimal("0.412"), "year": 2023, "source": "IEA 2023"},
    {"country_code": "BD", "country_name": "Bangladesh", "grid_factor": Decimal("0.528"), "year": 2023, "source": "IEA 2023"},
    {"country_code": "SA", "country_name": "Saudi Arabia", "grid_factor": Decimal("0.625"), "year": 2023, "source": "IEA 2023"},
    {"country_code": "AE", "country_name": "United Arab Emirates", "grid_factor": Decimal("0.412"), "year": 2023, "source": "IEA 2023"},
    {"country_code": "IR", "country_name": "Iran", "grid_factor": Decimal("0.523"), "year": 2023, "source": "IEA 2023"},
    {"country_code": "US", "country_name": "United States", "grid_factor": Decimal("0.379"), "year": 2023, "source": "EPA 2023"},
    {"country_code": "CA", "country_name": "Canada", "grid_factor": Decimal("0.120"), "year": 2023, "source": "IEA 2023"},
    {"country_code": "AU", "country_name": "Australia", "grid_factor": Decimal("0.656"), "year": 2023, "source": "IEA 2023"},
    {"country_code": "NO", "country_name": "Norway", "grid_factor": Decimal("0.008"), "year": 2023, "source": "IEA 2023"},
    {"country_code": "CH", "country_name": "Switzerland", "grid_factor": Decimal("0.012"), "year": 2023, "source": "IEA 2023"},
    {"country_code": "GB", "country_name": "United Kingdom", "grid_factor": Decimal("0.207"), "year": 2023, "source": "DEFRA 2023"},
    {"country_code": "RS", "country_name": "Serbia", "grid_factor": Decimal("0.719"), "year": 2023, "source": "IEA 2023"},
    {"country_code": "BA", "country_name": "Bosnia and Herzegovina", "grid_factor": Decimal("0.825"), "year": 2023, "source": "IEA 2023"},
    {"country_code": "MK", "country_name": "North Macedonia", "grid_factor": Decimal("0.612"), "year": 2023, "source": "IEA 2023"},
    {"country_code": "AL", "country_name": "Albania", "grid_factor": Decimal("0.015"), "year": 2023, "source": "IEA 2023"},
    {"country_code": "ME", "country_name": "Montenegro", "grid_factor": Decimal("0.425"), "year": 2023, "source": "IEA 2023"},
    {"country_code": "XK", "country_name": "Kosovo", "grid_factor": Decimal("0.892"), "year": 2023, "source": "IEA 2023"},
    # EU average for fallback
    {"country_code": "EU", "country_name": "European Union (average)", "grid_factor": Decimal("0.251"), "year": 2023, "source": "EEA 2023"},
    # World average for unknown countries
    {"country_code": "WORLD", "country_name": "World Average", "grid_factor": Decimal("0.436"), "year": 2023, "source": "IEA 2023"},
]


# ============================================================================
# CBAM PRODUCTS (CN CODE REFERENCE)
# ============================================================================

CBAM_PRODUCTS = [
    # Cement
    {"cn_code": "2523", "sector": "cement", "description": "Portland cement, aluminous cement, slag cement and similar hydraulic cements", "direct_required": True, "indirect_required": True},

    # Iron and Steel
    {"cn_code": "72", "sector": "iron_steel", "description": "Iron and steel", "direct_required": True, "indirect_required": False},
    {"cn_code": "73", "sector": "iron_steel", "description": "Articles of iron or steel", "direct_required": True, "indirect_required": False},

    # Aluminium
    {"cn_code": "76", "sector": "aluminium", "description": "Aluminium and articles thereof", "direct_required": True, "indirect_required": True},

    # Fertilisers
    {"cn_code": "2808", "sector": "fertiliser", "description": "Nitric acid; sulphonitric acids", "direct_required": True, "indirect_required": True},
    {"cn_code": "2814", "sector": "fertiliser", "description": "Ammonia, anhydrous or in aqueous solution", "direct_required": True, "indirect_required": True},
    {"cn_code": "3102", "sector": "fertiliser", "description": "Mineral or chemical fertilisers, nitrogenous", "direct_required": True, "indirect_required": True},
    {"cn_code": "3105", "sector": "fertiliser", "description": "Mineral or chemical fertilisers containing two or three nutrients", "direct_required": True, "indirect_required": True},

    # Electricity
    {"cn_code": "2716", "sector": "electricity", "description": "Electrical energy", "direct_required": True, "indirect_required": False},

    # Hydrogen
    {"cn_code": "2804_10_00", "sector": "hydrogen", "description": "Hydrogen", "direct_required": True, "indirect_required": True},
]


# ============================================================================
# EU ETS HISTORICAL PRICES (Sample data)
# EUR per tCO2e
# ============================================================================

EU_ETS_PRICES_2024 = [
    {"price_date": date(2024, 1, 3), "week_number": 1, "year": 2024, "price_eur": Decimal("73.42")},
    {"price_date": date(2024, 1, 10), "week_number": 2, "year": 2024, "price_eur": Decimal("68.95")},
    {"price_date": date(2024, 1, 17), "week_number": 3, "year": 2024, "price_eur": Decimal("62.38")},
    {"price_date": date(2024, 1, 24), "week_number": 4, "year": 2024, "price_eur": Decimal("58.72")},
    {"price_date": date(2024, 1, 31), "week_number": 5, "year": 2024, "price_eur": Decimal("56.85")},
    {"price_date": date(2024, 2, 7), "week_number": 6, "year": 2024, "price_eur": Decimal("54.23")},
    {"price_date": date(2024, 2, 14), "week_number": 7, "year": 2024, "price_eur": Decimal("53.18")},
    {"price_date": date(2024, 2, 21), "week_number": 8, "year": 2024, "price_eur": Decimal("55.62")},
    {"price_date": date(2024, 2, 28), "week_number": 9, "year": 2024, "price_eur": Decimal("58.45")},
    {"price_date": date(2024, 3, 6), "week_number": 10, "year": 2024, "price_eur": Decimal("61.23")},
    {"price_date": date(2024, 3, 13), "week_number": 11, "year": 2024, "price_eur": Decimal("59.87")},
    {"price_date": date(2024, 3, 20), "week_number": 12, "year": 2024, "price_eur": Decimal("62.15")},
    # Add more weeks as needed...
]


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_default_see_by_cn_code(cn_code: str) -> dict | None:
    """Look up default SEE value by CN code (exact or prefix match)."""
    # First try exact match
    for item in CBAM_DEFAULT_VALUES:
        if item["cn_code"] == cn_code:
            return item

    # Then try prefix match (e.g., "7208" matches "7208_10_00")
    for item in CBAM_DEFAULT_VALUES:
        if item["cn_code"].startswith(cn_code) or cn_code.startswith(item["cn_code"].replace("_", "")):
            return item

    return None


def get_grid_factor_by_country(country_code: str) -> Decimal:
    """Get grid emission factor for a country, with fallback to world average."""
    for item in CBAM_GRID_FACTORS:
        if item["country_code"] == country_code:
            return item["grid_factor"]

    # Fallback to world average
    return Decimal("0.436")


def get_sector_for_cn_code(cn_code: str) -> str | None:
    """Determine CBAM sector from CN code."""
    cn_2digit = cn_code[:2]
    cn_4digit = cn_code[:4]

    if cn_4digit == "2523":
        return "cement"
    elif cn_2digit in ("72", "73"):
        return "iron_steel"
    elif cn_2digit == "76":
        return "aluminium"
    elif cn_4digit in ("2808", "2814", "3102", "3105"):
        return "fertiliser"
    elif cn_4digit == "2716":
        return "electricity"
    elif cn_code.startswith("2804_10"):
        return "hydrogen"

    return None
