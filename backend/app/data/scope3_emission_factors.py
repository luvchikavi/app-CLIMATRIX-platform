"""
Scope 3 Category 3.1 - Physical Material Emission Factors.

DEFRA 2024 material-specific emission factors for purchased goods.
These provide physical quantity-based calculations (kg CO2e per kg material)
as an alternative to spend-based EEIO factors.

Hierarchy (per GHG Protocol):
1. Supplier-specific (EPD, LCA) — highest accuracy
2. EcoInvent (licensed LCA database) — stub, to implement when license available
3. DEFRA physical factors (this file) — good accuracy for common materials
4. EEIO spend-based (existing) — lowest accuracy, broadest coverage

Source: DEFRA 2024 (UK Government GHG Conversion Factors for Company Reporting)
"""
from decimal import Decimal


# =============================================================================
# DEFRA MATERIAL EMISSION FACTORS (kg CO2e per kg of material)
# =============================================================================

DEFRA_MATERIAL_FACTORS = {
    # =========================================================================
    # METALS
    # =========================================================================
    "steel_primary": {
        "display_name": "Steel (primary/virgin)",
        "co2e_per_kg": Decimal("2.80"),
        "unit": "kg",
        "source": "DEFRA_2024",
        "category": "metals",
        "notes": "BOF route, world average",
    },
    "steel_recycled": {
        "display_name": "Steel (recycled/EAF)",
        "co2e_per_kg": Decimal("0.47"),
        "unit": "kg",
        "source": "DEFRA_2024",
        "category": "metals",
        "notes": "EAF route with scrap input",
    },
    "steel_average": {
        "display_name": "Steel (average mix)",
        "co2e_per_kg": Decimal("1.83"),
        "unit": "kg",
        "source": "DEFRA_2024",
        "category": "metals",
        "notes": "Global average ~30% recycled content",
    },
    "aluminum_primary": {
        "display_name": "Aluminium (primary/virgin)",
        "co2e_per_kg": Decimal("9.16"),
        "unit": "kg",
        "source": "DEFRA_2024",
        "category": "metals",
        "notes": "Electrolysis, global average grid mix",
    },
    "aluminum_recycled": {
        "display_name": "Aluminium (recycled)",
        "co2e_per_kg": Decimal("0.52"),
        "unit": "kg",
        "source": "DEFRA_2024",
        "category": "metals",
        "notes": "Remelting process",
    },
    "aluminum_average": {
        "display_name": "Aluminium (average mix)",
        "co2e_per_kg": Decimal("6.67"),
        "unit": "kg",
        "source": "DEFRA_2024",
        "category": "metals",
        "notes": "Global average ~33% recycled content",
    },
    "copper_primary": {
        "display_name": "Copper (primary)",
        "co2e_per_kg": Decimal("3.81"),
        "unit": "kg",
        "source": "DEFRA_2024",
        "category": "metals",
    },
    "copper_recycled": {
        "display_name": "Copper (recycled)",
        "co2e_per_kg": Decimal("0.84"),
        "unit": "kg",
        "source": "DEFRA_2024",
        "category": "metals",
    },
    "stainless_steel": {
        "display_name": "Stainless Steel",
        "co2e_per_kg": Decimal("6.15"),
        "unit": "kg",
        "source": "DEFRA_2024",
        "category": "metals",
    },
    "zinc": {
        "display_name": "Zinc",
        "co2e_per_kg": Decimal("3.09"),
        "unit": "kg",
        "source": "DEFRA_2024",
        "category": "metals",
    },
    "lead": {
        "display_name": "Lead",
        "co2e_per_kg": Decimal("1.57"),
        "unit": "kg",
        "source": "DEFRA_2024",
        "category": "metals",
    },
    "tin": {
        "display_name": "Tin",
        "co2e_per_kg": Decimal("16.10"),
        "unit": "kg",
        "source": "DEFRA_2024",
        "category": "metals",
    },

    # =========================================================================
    # PLASTICS
    # =========================================================================
    "plastic_pet": {
        "display_name": "PET (Polyethylene Terephthalate)",
        "co2e_per_kg": Decimal("3.19"),
        "unit": "kg",
        "source": "DEFRA_2024",
        "category": "plastics",
    },
    "plastic_hdpe": {
        "display_name": "HDPE (High-Density Polyethylene)",
        "co2e_per_kg": Decimal("1.93"),
        "unit": "kg",
        "source": "DEFRA_2024",
        "category": "plastics",
    },
    "plastic_ldpe": {
        "display_name": "LDPE (Low-Density Polyethylene)",
        "co2e_per_kg": Decimal("2.08"),
        "unit": "kg",
        "source": "DEFRA_2024",
        "category": "plastics",
    },
    "plastic_pp": {
        "display_name": "PP (Polypropylene)",
        "co2e_per_kg": Decimal("1.95"),
        "unit": "kg",
        "source": "DEFRA_2024",
        "category": "plastics",
    },
    "plastic_ps": {
        "display_name": "PS (Polystyrene)",
        "co2e_per_kg": Decimal("3.43"),
        "unit": "kg",
        "source": "DEFRA_2024",
        "category": "plastics",
    },
    "plastic_pvc": {
        "display_name": "PVC (Polyvinyl Chloride)",
        "co2e_per_kg": Decimal("2.41"),
        "unit": "kg",
        "source": "DEFRA_2024",
        "category": "plastics",
    },
    "plastic_average": {
        "display_name": "Plastic (average mix)",
        "co2e_per_kg": Decimal("2.53"),
        "unit": "kg",
        "source": "DEFRA_2024",
        "category": "plastics",
        "notes": "Average of common plastic types",
    },
    "plastic_nylon": {
        "display_name": "Nylon (Polyamide)",
        "co2e_per_kg": Decimal("7.62"),
        "unit": "kg",
        "source": "DEFRA_2024",
        "category": "plastics",
    },

    # =========================================================================
    # PAPER & BOARD
    # =========================================================================
    "paper_primary": {
        "display_name": "Paper (virgin)",
        "co2e_per_kg": Decimal("0.92"),
        "unit": "kg",
        "source": "DEFRA_2024",
        "category": "paper",
    },
    "paper_recycled": {
        "display_name": "Paper (recycled)",
        "co2e_per_kg": Decimal("0.61"),
        "unit": "kg",
        "source": "DEFRA_2024",
        "category": "paper",
    },
    "paper_average": {
        "display_name": "Paper (average mix)",
        "co2e_per_kg": Decimal("0.84"),
        "unit": "kg",
        "source": "DEFRA_2024",
        "category": "paper",
    },
    "cardboard": {
        "display_name": "Cardboard/Corrugated Board",
        "co2e_per_kg": Decimal("0.79"),
        "unit": "kg",
        "source": "DEFRA_2024",
        "category": "paper",
    },

    # =========================================================================
    # GLASS
    # =========================================================================
    "glass_primary": {
        "display_name": "Glass (virgin)",
        "co2e_per_kg": Decimal("0.86"),
        "unit": "kg",
        "source": "DEFRA_2024",
        "category": "glass",
    },
    "glass_recycled": {
        "display_name": "Glass (recycled)",
        "co2e_per_kg": Decimal("0.47"),
        "unit": "kg",
        "source": "DEFRA_2024",
        "category": "glass",
    },
    "glass_average": {
        "display_name": "Glass (average mix)",
        "co2e_per_kg": Decimal("0.76"),
        "unit": "kg",
        "source": "DEFRA_2024",
        "category": "glass",
    },

    # =========================================================================
    # CONSTRUCTION MATERIALS
    # =========================================================================
    "concrete": {
        "display_name": "Concrete (average)",
        "co2e_per_kg": Decimal("0.13"),
        "unit": "kg",
        "source": "DEFRA_2024",
        "category": "construction",
    },
    "cement": {
        "display_name": "Cement (Portland)",
        "co2e_per_kg": Decimal("0.83"),
        "unit": "kg",
        "source": "DEFRA_2024",
        "category": "construction",
    },
    "brick": {
        "display_name": "Brick",
        "co2e_per_kg": Decimal("0.24"),
        "unit": "kg",
        "source": "DEFRA_2024",
        "category": "construction",
    },
    "timber_primary": {
        "display_name": "Timber (virgin)",
        "co2e_per_kg": Decimal("0.31"),
        "unit": "kg",
        "source": "DEFRA_2024",
        "category": "construction",
    },
    "plasterboard": {
        "display_name": "Plasterboard",
        "co2e_per_kg": Decimal("0.12"),
        "unit": "kg",
        "source": "DEFRA_2024",
        "category": "construction",
    },
    "insulation_mineral_wool": {
        "display_name": "Insulation (Mineral Wool)",
        "co2e_per_kg": Decimal("1.28"),
        "unit": "kg",
        "source": "DEFRA_2024",
        "category": "construction",
    },

    # =========================================================================
    # TEXTILES
    # =========================================================================
    "cotton": {
        "display_name": "Cotton Fabric",
        "co2e_per_kg": Decimal("8.10"),
        "unit": "kg",
        "source": "DEFRA_2024",
        "category": "textiles",
    },
    "polyester": {
        "display_name": "Polyester Fabric",
        "co2e_per_kg": Decimal("5.55"),
        "unit": "kg",
        "source": "DEFRA_2024",
        "category": "textiles",
    },
    "wool": {
        "display_name": "Wool Fabric",
        "co2e_per_kg": Decimal("18.90"),
        "unit": "kg",
        "source": "DEFRA_2024",
        "category": "textiles",
    },
    "textiles_average": {
        "display_name": "Textiles (average mix)",
        "co2e_per_kg": Decimal("7.00"),
        "unit": "kg",
        "source": "DEFRA_2024",
        "category": "textiles",
    },

    # =========================================================================
    # FOOD & AGRICULTURE
    # =========================================================================
    "food_meat_beef": {
        "display_name": "Beef",
        "co2e_per_kg": Decimal("27.00"),
        "unit": "kg",
        "source": "DEFRA_2024",
        "category": "food",
        "notes": "Includes land use change",
    },
    "food_meat_lamb": {
        "display_name": "Lamb",
        "co2e_per_kg": Decimal("20.40"),
        "unit": "kg",
        "source": "DEFRA_2024",
        "category": "food",
    },
    "food_meat_pork": {
        "display_name": "Pork",
        "co2e_per_kg": Decimal("5.77"),
        "unit": "kg",
        "source": "DEFRA_2024",
        "category": "food",
    },
    "food_meat_poultry": {
        "display_name": "Poultry (Chicken)",
        "co2e_per_kg": Decimal("4.12"),
        "unit": "kg",
        "source": "DEFRA_2024",
        "category": "food",
    },
    "food_fish": {
        "display_name": "Fish (average)",
        "co2e_per_kg": Decimal("3.49"),
        "unit": "kg",
        "source": "DEFRA_2024",
        "category": "food",
    },
    "food_dairy_milk": {
        "display_name": "Milk",
        "co2e_per_kg": Decimal("1.39"),
        "unit": "kg",
        "source": "DEFRA_2024",
        "category": "food",
    },
    "food_dairy_cheese": {
        "display_name": "Cheese",
        "co2e_per_kg": Decimal("8.55"),
        "unit": "kg",
        "source": "DEFRA_2024",
        "category": "food",
    },
    "food_vegetables": {
        "display_name": "Vegetables (average)",
        "co2e_per_kg": Decimal("0.37"),
        "unit": "kg",
        "source": "DEFRA_2024",
        "category": "food",
    },
    "food_fruit": {
        "display_name": "Fruit (average)",
        "co2e_per_kg": Decimal("0.46"),
        "unit": "kg",
        "source": "DEFRA_2024",
        "category": "food",
    },
    "food_cereals": {
        "display_name": "Cereals/Grains",
        "co2e_per_kg": Decimal("0.51"),
        "unit": "kg",
        "source": "DEFRA_2024",
        "category": "food",
    },
    "food_rice": {
        "display_name": "Rice",
        "co2e_per_kg": Decimal("2.55"),
        "unit": "kg",
        "source": "DEFRA_2024",
        "category": "food",
        "notes": "Includes methane from paddy cultivation",
    },

    # =========================================================================
    # CHEMICALS
    # =========================================================================
    "chemicals_general": {
        "display_name": "Chemicals (general/average)",
        "co2e_per_kg": Decimal("1.60"),
        "unit": "kg",
        "source": "DEFRA_2024",
        "category": "chemicals",
    },
    "chemicals_paints": {
        "display_name": "Paints & Coatings",
        "co2e_per_kg": Decimal("2.42"),
        "unit": "kg",
        "source": "DEFRA_2024",
        "category": "chemicals",
    },
    "chemicals_fertilizer": {
        "display_name": "Fertilizer (average)",
        "co2e_per_kg": Decimal("2.97"),
        "unit": "kg",
        "source": "DEFRA_2024",
        "category": "chemicals",
    },

    # =========================================================================
    # RUBBER
    # =========================================================================
    "rubber_natural": {
        "display_name": "Natural Rubber",
        "co2e_per_kg": Decimal("1.90"),
        "unit": "kg",
        "source": "DEFRA_2024",
        "category": "rubber",
    },
    "rubber_synthetic": {
        "display_name": "Synthetic Rubber",
        "co2e_per_kg": Decimal("3.18"),
        "unit": "kg",
        "source": "DEFRA_2024",
        "category": "rubber",
    },

    # =========================================================================
    # ELECTRONICS (per kg of product weight)
    # =========================================================================
    "electronics_average": {
        "display_name": "Electronics (average per kg)",
        "co2e_per_kg": Decimal("15.80"),
        "unit": "kg",
        "source": "DEFRA_2024",
        "category": "electronics",
        "notes": "Average across product types",
    },
    "batteries_lithium": {
        "display_name": "Lithium-ion Batteries",
        "co2e_per_kg": Decimal("12.50"),
        "unit": "kg",
        "source": "DEFRA_2024",
        "category": "electronics",
    },
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_material_factor(material_key: str) -> dict | None:
    """Get DEFRA material emission factor by key."""
    return DEFRA_MATERIAL_FACTORS.get(material_key.lower())


def get_material_co2e_per_kg(material_key: str) -> Decimal | None:
    """Get the CO2e factor for a material (kg CO2e per kg)."""
    factor = get_material_factor(material_key)
    if factor:
        return factor["co2e_per_kg"]
    return None


def search_materials(query: str, category: str = None) -> list[dict]:
    """
    Search material factors by name or category.

    Args:
        query: Search term (case-insensitive)
        category: Optional filter by category (metals, plastics, paper, etc.)

    Returns:
        List of matching material factor dicts with their keys
    """
    query_lower = query.lower()
    results = []

    for key, data in DEFRA_MATERIAL_FACTORS.items():
        if category and data.get("category") != category:
            continue
        if (query_lower in key.lower() or
            query_lower in data["display_name"].lower()):
            results.append({"key": key, **data})

    return results


def list_categories() -> list[str]:
    """Get all unique material categories."""
    categories = set()
    for data in DEFRA_MATERIAL_FACTORS.values():
        if "category" in data:
            categories.add(data["category"])
    return sorted(categories)


def get_factors_by_category(category: str) -> dict:
    """Get all factors for a given category."""
    return {
        key: data
        for key, data in DEFRA_MATERIAL_FACTORS.items()
        if data.get("category") == category
    }
