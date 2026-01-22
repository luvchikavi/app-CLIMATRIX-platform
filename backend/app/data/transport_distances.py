"""
Transport Distance Matrix for Category 3.4 Upstream Transportation.

Default shipping distances when clients know origin country but not exact route.
Used for calculating transport emissions when detailed logistics data unavailable.

Sources:
- Sea distances: Sea-distances.org, UNCTAD
- Land distances: Regional averages from trade data
"""
from decimal import Decimal


# =============================================================================
# TRANSPORT DISTANCE MATRIX
# Format: (origin, destination) -> {sea_km, origin_land_km, dest_land_km, mode}
# =============================================================================

TRANSPORT_DISTANCES = {
    # =========================================================================
    # FROM CHINA
    # =========================================================================
    ("CN", "IL"): {
        "sea_distance_km": 12000,
        "origin_land_km": 500,
        "destination_land_km": 100,
        "total_distance_km": 12600,
        "transport_mode": "sea_container",
        "air_distance_km": 7800,
        "rail_distance_km": None,  # No direct rail
        "source": "Shanghai-Haifa via Suez",
        "notes": "Primary route via Suez Canal",
    },
    ("CN", "GB"): {
        "sea_distance_km": 20000,
        "origin_land_km": 500,
        "destination_land_km": 200,
        "total_distance_km": 20700,
        "transport_mode": "sea_container",
        "air_distance_km": 8500,
        "rail_distance_km": 12000,  # Trans-Siberian + Europe
        "source": "Shanghai-Felixstowe",
        "notes": "Via Suez or around Cape; rail via Kazakhstan/Russia",
    },
    ("CN", "US"): {
        "sea_distance_km": 11000,  # West Coast
        "origin_land_km": 500,
        "destination_land_km": 300,
        "total_distance_km": 11800,
        "transport_mode": "sea_container",
        "air_distance_km": 10500,
        "rail_distance_km": None,
        "source": "Shanghai-LA",
        "notes": "West Coast; East Coast add ~9000 km sea or ~4000 km rail inland",
    },
    ("CN", "DE"): {
        "sea_distance_km": 18000,
        "origin_land_km": 500,
        "destination_land_km": 300,
        "total_distance_km": 18800,
        "transport_mode": "sea_container",
        "air_distance_km": 7800,
        "rail_distance_km": 11000,  # China-Europe Express
        "source": "Shanghai-Hamburg",
        "notes": "Rail via New Silk Road increasingly used",
    },
    ("CN", "NL"): {
        "sea_distance_km": 19000,
        "origin_land_km": 500,
        "destination_land_km": 100,
        "total_distance_km": 19600,
        "transport_mode": "sea_container",
        "air_distance_km": 8200,
        "rail_distance_km": 10500,
        "source": "Shanghai-Rotterdam",
        "notes": "Rotterdam is Europe's largest container port",
    },
    ("CN", "JP"): {
        "sea_distance_km": 1800,
        "origin_land_km": 300,
        "destination_land_km": 100,
        "total_distance_km": 2200,
        "transport_mode": "sea_container",
        "air_distance_km": 2100,
        "rail_distance_km": None,
        "source": "Shanghai-Tokyo",
        "notes": "Short sea route",
    },
    ("CN", "AU"): {
        "sea_distance_km": 8500,
        "origin_land_km": 500,
        "destination_land_km": 200,
        "total_distance_km": 9200,
        "transport_mode": "sea_container",
        "air_distance_km": 8900,
        "rail_distance_km": None,
        "source": "Shanghai-Sydney",
        "notes": "Direct Pacific route",
    },

    # =========================================================================
    # FROM INDIA
    # =========================================================================
    ("IN", "IL"): {
        "sea_distance_km": 4500,
        "origin_land_km": 400,
        "destination_land_km": 100,
        "total_distance_km": 5000,
        "transport_mode": "sea_container",
        "air_distance_km": 4000,
        "rail_distance_km": None,
        "source": "Mumbai-Haifa",
        "notes": "Via Red Sea",
    },
    ("IN", "GB"): {
        "sea_distance_km": 9000,
        "origin_land_km": 400,
        "destination_land_km": 200,
        "total_distance_km": 9600,
        "transport_mode": "sea_container",
        "air_distance_km": 7200,
        "rail_distance_km": None,
        "source": "Mumbai-Felixstowe",
        "notes": "Via Suez Canal",
    },
    ("IN", "US"): {
        "sea_distance_km": 14000,  # West Coast via Pacific
        "origin_land_km": 400,
        "destination_land_km": 300,
        "total_distance_km": 14700,
        "transport_mode": "sea_container",
        "air_distance_km": 13000,
        "rail_distance_km": None,
        "source": "Mumbai-LA",
        "notes": "Pacific route; East Coast shorter via Suez",
    },
    ("IN", "DE"): {
        "sea_distance_km": 8500,
        "origin_land_km": 400,
        "destination_land_km": 300,
        "total_distance_km": 9200,
        "transport_mode": "sea_container",
        "air_distance_km": 6500,
        "rail_distance_km": None,
        "source": "Mumbai-Hamburg",
        "notes": "Via Suez Canal",
    },

    # =========================================================================
    # FROM TURKEY
    # =========================================================================
    ("TR", "IL"): {
        "sea_distance_km": 1500,
        "origin_land_km": 200,
        "destination_land_km": 100,
        "total_distance_km": 1800,
        "transport_mode": "sea_container",
        "air_distance_km": 1000,
        "rail_distance_km": None,
        "source": "Mersin-Haifa",
        "notes": "Short Mediterranean route; road also viable",
    },
    ("TR", "GB"): {
        "sea_distance_km": 4500,
        "origin_land_km": 200,
        "destination_land_km": 200,
        "total_distance_km": 4900,
        "transport_mode": "sea_container",
        "air_distance_km": 2500,
        "rail_distance_km": 3500,
        "source": "Istanbul-Felixstowe",
        "notes": "Road/rail through Europe also common",
    },
    ("TR", "DE"): {
        "sea_distance_km": 4000,
        "origin_land_km": 200,
        "destination_land_km": 300,
        "total_distance_km": 4500,
        "transport_mode": "sea_container",
        "air_distance_km": 1800,
        "rail_distance_km": 2500,
        "source": "Istanbul-Hamburg",
        "notes": "Road transport common via Balkans",
    },

    # =========================================================================
    # FROM GERMANY (Intra-Europe)
    # =========================================================================
    ("DE", "IL"): {
        "sea_distance_km": 4500,
        "origin_land_km": 300,
        "destination_land_km": 100,
        "total_distance_km": 4900,
        "transport_mode": "sea_container",
        "air_distance_km": 3000,
        "rail_distance_km": None,
        "source": "Hamburg-Haifa",
        "notes": "Via Mediterranean",
    },
    ("DE", "GB"): {
        "sea_distance_km": 800,
        "origin_land_km": 300,
        "destination_land_km": 200,
        "total_distance_km": 1300,
        "transport_mode": "sea_container",
        "air_distance_km": 900,
        "rail_distance_km": 1100,
        "source": "Hamburg-Felixstowe",
        "notes": "Road/ferry common via Calais or direct ferry",
    },
    ("DE", "US"): {
        "sea_distance_km": 7000,
        "origin_land_km": 300,
        "destination_land_km": 300,
        "total_distance_km": 7600,
        "transport_mode": "sea_container",
        "air_distance_km": 7500,
        "rail_distance_km": None,
        "source": "Hamburg-New York",
        "notes": "East Coast",
    },
    ("DE", "FR"): {
        "sea_distance_km": 0,  # Road only - no sea leg
        "origin_land_km": 500,  # Full road distance
        "destination_land_km": 0,
        "total_distance_km": 500,
        "transport_mode": "road_hgv",
        "air_distance_km": 400,
        "rail_distance_km": 600,
        "source": "Frankfurt-Paris road",
        "notes": "Road dominant for intra-Europe",
    },

    # =========================================================================
    # FROM NETHERLANDS
    # =========================================================================
    ("NL", "IL"): {
        "sea_distance_km": 5000,
        "origin_land_km": 100,
        "destination_land_km": 100,
        "total_distance_km": 5200,
        "transport_mode": "sea_container",
        "air_distance_km": 3300,
        "rail_distance_km": None,
        "source": "Rotterdam-Haifa",
        "notes": "Rotterdam major hub",
    },
    ("NL", "GB"): {
        "sea_distance_km": 300,
        "origin_land_km": 100,
        "destination_land_km": 200,
        "total_distance_km": 600,
        "transport_mode": "sea_container",
        "air_distance_km": 400,
        "rail_distance_km": 500,
        "source": "Rotterdam-Felixstowe",
        "notes": "Very short sea crossing",
    },

    # =========================================================================
    # FROM UNITED STATES
    # =========================================================================
    ("US", "IL"): {
        "sea_distance_km": 11000,
        "origin_land_km": 500,
        "destination_land_km": 100,
        "total_distance_km": 11600,
        "transport_mode": "sea_container",
        "air_distance_km": 9500,
        "rail_distance_km": None,
        "source": "New York-Haifa",
        "notes": "Via Atlantic and Mediterranean",
    },
    ("US", "GB"): {
        "sea_distance_km": 5500,
        "origin_land_km": 500,
        "destination_land_km": 200,
        "total_distance_km": 6200,
        "transport_mode": "sea_container",
        "air_distance_km": 5500,
        "rail_distance_km": None,
        "source": "New York-Felixstowe",
        "notes": "Transatlantic",
    },
    ("US", "DE"): {
        "sea_distance_km": 6000,
        "origin_land_km": 500,
        "destination_land_km": 300,
        "total_distance_km": 6800,
        "transport_mode": "sea_container",
        "air_distance_km": 6300,
        "rail_distance_km": None,
        "source": "New York-Hamburg",
        "notes": "Transatlantic",
    },

    # =========================================================================
    # FROM VIETNAM
    # =========================================================================
    ("VN", "IL"): {
        "sea_distance_km": 10000,
        "origin_land_km": 300,
        "destination_land_km": 100,
        "total_distance_km": 10400,
        "transport_mode": "sea_container",
        "air_distance_km": 7500,
        "rail_distance_km": None,
        "source": "Ho Chi Minh-Haifa",
        "notes": "Via Suez Canal",
    },
    ("VN", "US"): {
        "sea_distance_km": 12000,
        "origin_land_km": 300,
        "destination_land_km": 300,
        "total_distance_km": 12600,
        "transport_mode": "sea_container",
        "air_distance_km": 13500,
        "rail_distance_km": None,
        "source": "Ho Chi Minh-LA",
        "notes": "Pacific route",
    },

    # =========================================================================
    # FROM SOUTH KOREA
    # =========================================================================
    ("KR", "IL"): {
        "sea_distance_km": 11000,
        "origin_land_km": 200,
        "destination_land_km": 100,
        "total_distance_km": 11300,
        "transport_mode": "sea_container",
        "air_distance_km": 7400,
        "rail_distance_km": None,
        "source": "Busan-Haifa",
        "notes": "Via Suez Canal",
    },
    ("KR", "US"): {
        "sea_distance_km": 9500,
        "origin_land_km": 200,
        "destination_land_km": 300,
        "total_distance_km": 10000,
        "transport_mode": "sea_container",
        "air_distance_km": 9500,
        "rail_distance_km": None,
        "source": "Busan-LA",
        "notes": "Pacific route",
    },

    # =========================================================================
    # FROM TAIWAN
    # =========================================================================
    ("TW", "IL"): {
        "sea_distance_km": 10500,
        "origin_land_km": 100,
        "destination_land_km": 100,
        "total_distance_km": 10700,
        "transport_mode": "sea_container",
        "air_distance_km": 7200,
        "rail_distance_km": None,
        "source": "Kaohsiung-Haifa",
        "notes": "Via Suez Canal",
    },
    ("TW", "US"): {
        "sea_distance_km": 10000,
        "origin_land_km": 100,
        "destination_land_km": 300,
        "total_distance_km": 10400,
        "transport_mode": "sea_container",
        "air_distance_km": 11000,
        "rail_distance_km": None,
        "source": "Kaohsiung-LA",
        "notes": "Pacific route",
    },

    # =========================================================================
    # FROM ITALY
    # =========================================================================
    ("IT", "IL"): {
        "sea_distance_km": 2500,
        "origin_land_km": 200,
        "destination_land_km": 100,
        "total_distance_km": 2800,
        "transport_mode": "sea_container",
        "air_distance_km": 2200,
        "rail_distance_km": None,
        "source": "Genoa-Haifa",
        "notes": "Short Mediterranean route",
    },

    # =========================================================================
    # FROM SPAIN
    # =========================================================================
    ("ES", "IL"): {
        "sea_distance_km": 3500,
        "origin_land_km": 200,
        "destination_land_km": 100,
        "total_distance_km": 3800,
        "transport_mode": "sea_container",
        "air_distance_km": 3500,
        "rail_distance_km": None,
        "source": "Barcelona-Haifa",
        "notes": "Via Mediterranean",
    },

    # =========================================================================
    # FROM BRAZIL
    # =========================================================================
    ("BR", "IL"): {
        "sea_distance_km": 10500,
        "origin_land_km": 500,
        "destination_land_km": 100,
        "total_distance_km": 11100,
        "transport_mode": "sea_container",
        "air_distance_km": 10000,
        "rail_distance_km": None,
        "source": "Santos-Haifa",
        "notes": "Via Atlantic",
    },
    ("BR", "US"): {
        "sea_distance_km": 8000,
        "origin_land_km": 500,
        "destination_land_km": 300,
        "total_distance_km": 8800,
        "transport_mode": "sea_container",
        "air_distance_km": 7500,
        "rail_distance_km": None,
        "source": "Santos-New York",
        "notes": "Via Atlantic",
    },
}


# =============================================================================
# EMISSION FACTORS FOR TRANSPORT MODES
# Source: DEFRA 2024
# =============================================================================

TRANSPORT_EMISSION_FACTORS = {
    "sea_container": Decimal("0.016"),      # kg CO2e per tonne-km
    "sea_bulk": Decimal("0.004"),           # kg CO2e per tonne-km (bulk carriers)
    "road_hgv": Decimal("0.107"),           # kg CO2e per tonne-km (HGV >7.5t)
    "road_van": Decimal("0.605"),           # kg CO2e per tonne-km (Van <3.5t)
    "rail_freight": Decimal("0.028"),       # kg CO2e per tonne-km
    "air_freight": Decimal("1.130"),        # kg CO2e per tonne-km
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_transport_distance(origin_country: str, destination_country: str) -> dict | None:
    """
    Get default transport distances between two countries.

    Args:
        origin_country: 2-letter ISO country code (e.g., "CN", "IN")
        destination_country: 2-letter ISO country code (e.g., "IL", "GB")

    Returns:
        Dictionary with distance components or None if route not found
    """
    origin = origin_country.upper()
    dest = destination_country.upper()

    return TRANSPORT_DISTANCES.get((origin, dest))


def calculate_transport_emissions(
    origin_country: str,
    destination_country: str,
    weight_tonnes: Decimal,
    transport_mode: str = "auto"
) -> dict | None:
    """
    Calculate transport emissions for a shipment.

    Args:
        origin_country: 2-letter ISO country code
        destination_country: 2-letter ISO country code
        weight_tonnes: Weight of shipment in tonnes
        transport_mode: "sea_container", "air_freight", or "auto" (use default)

    Returns:
        Dictionary with emissions breakdown or None if route not found
    """
    distances = get_transport_distance(origin_country, destination_country)
    if not distances:
        return None

    # Use specified mode or default from matrix
    if transport_mode == "auto":
        transport_mode = distances["transport_mode"]

    # Calculate each leg
    origin_land_ef = TRANSPORT_EMISSION_FACTORS["road_hgv"]
    sea_ef = TRANSPORT_EMISSION_FACTORS.get(transport_mode, TRANSPORT_EMISSION_FACTORS["sea_container"])
    dest_land_ef = TRANSPORT_EMISSION_FACTORS["road_hgv"]

    origin_land_emissions = weight_tonnes * Decimal(distances["origin_land_km"]) * origin_land_ef

    # Sea or air emissions
    if transport_mode == "air_freight" and distances.get("air_distance_km"):
        main_distance = distances["air_distance_km"]
        main_ef = TRANSPORT_EMISSION_FACTORS["air_freight"]
    else:
        main_distance = distances["sea_distance_km"] or 0
        main_ef = sea_ef

    main_leg_emissions = weight_tonnes * Decimal(main_distance) * main_ef
    dest_land_emissions = weight_tonnes * Decimal(distances["destination_land_km"]) * dest_land_ef

    total_emissions = origin_land_emissions + main_leg_emissions + dest_land_emissions

    return {
        "origin_country": origin_country,
        "destination_country": destination_country,
        "weight_tonnes": weight_tonnes,
        "transport_mode": transport_mode,

        "legs": [
            {
                "leg": "origin_land",
                "mode": "road_hgv",
                "distance_km": distances["origin_land_km"],
                "emissions_kg": float(origin_land_emissions),
            },
            {
                "leg": "main",
                "mode": transport_mode,
                "distance_km": main_distance,
                "emissions_kg": float(main_leg_emissions),
            },
            {
                "leg": "destination_land",
                "mode": "road_hgv",
                "distance_km": distances["destination_land_km"],
                "emissions_kg": float(dest_land_emissions),
            },
        ],

        "total_distance_km": distances["origin_land_km"] + main_distance + distances["destination_land_km"],
        "total_emissions_kg": float(total_emissions),

        "formula": f"{weight_tonnes} tonnes × {distances['origin_land_km']} km (road) + {main_distance} km ({transport_mode}) + {distances['destination_land_km']} km (road)",
        "source": distances.get("source", "Default matrix"),
    }


def list_available_routes() -> list[tuple[str, str]]:
    """Return list of all available origin-destination pairs."""
    return list(TRANSPORT_DISTANCES.keys())


def get_transport_stats() -> dict:
    """Get statistics about the transport distance matrix."""
    origins = set()
    destinations = set()

    for origin, dest in TRANSPORT_DISTANCES.keys():
        origins.add(origin)
        destinations.add(dest)

    return {
        "total_routes": len(TRANSPORT_DISTANCES),
        "origin_countries": len(origins),
        "destination_countries": len(destinations),
        "origins": sorted(origins),
        "destinations": sorted(destinations),
    }


# =============================================================================
# TEST
# =============================================================================

if __name__ == "__main__":
    # Test transport emissions calculation
    result = calculate_transport_emissions("CN", "IL", Decimal("1.0"))
    if result:
        print(f"China → Israel (1 tonne):")
        print(f"  Total distance: {result['total_distance_km']} km")
        print(f"  Total emissions: {result['total_emissions_kg']:.1f} kg CO2e")
        print(f"  Legs:")
        for leg in result['legs']:
            print(f"    {leg['leg']}: {leg['distance_km']} km ({leg['mode']}) = {leg['emissions_kg']:.1f} kg")

    print(f"\nTransport matrix: {len(TRANSPORT_DISTANCES)} routes")
    stats = get_transport_stats()
    print(f"Origins: {stats['origins']}")
    print(f"Destinations: {stats['destinations']}")
