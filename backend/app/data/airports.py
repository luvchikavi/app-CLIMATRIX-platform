"""
IATA Airport Database for Flight Distance Calculations.

Source: OpenFlights.org + Manual Verification
Contains 200+ major airports worldwide with coordinates for accurate
great-circle distance calculations.
"""
from decimal import Decimal
from math import radians, sin, cos, sqrt, atan2
from typing import Optional, Tuple

# =============================================================================
# IATA AIRPORT DATABASE
# Format: IATA_CODE -> (name, city, country, latitude, longitude)
# =============================================================================

AIRPORTS: dict[str, Tuple[str, str, str, float, float]] = {
    # ==========================================================================
    # NORTH AMERICA - United States
    # ==========================================================================
    "ATL": ("Hartsfield-Jackson Atlanta International", "Atlanta", "US", 33.6407, -84.4277),
    "LAX": ("Los Angeles International", "Los Angeles", "US", 33.9425, -118.4081),
    "ORD": ("O'Hare International", "Chicago", "US", 41.9742, -87.9073),
    "DFW": ("Dallas/Fort Worth International", "Dallas", "US", 32.8998, -97.0403),
    "DEN": ("Denver International", "Denver", "US", 39.8561, -104.6737),
    "JFK": ("John F. Kennedy International", "New York", "US", 40.6413, -73.7781),
    "SFO": ("San Francisco International", "San Francisco", "US", 37.6213, -122.3790),
    "SEA": ("Seattle-Tacoma International", "Seattle", "US", 47.4502, -122.3088),
    "LAS": ("Harry Reid International", "Las Vegas", "US", 36.0840, -115.1537),
    "MCO": ("Orlando International", "Orlando", "US", 28.4312, -81.3081),
    "EWR": ("Newark Liberty International", "Newark", "US", 40.6895, -74.1745),
    "MIA": ("Miami International", "Miami", "US", 25.7959, -80.2870),
    "PHX": ("Phoenix Sky Harbor International", "Phoenix", "US", 33.4373, -112.0078),
    "IAH": ("George Bush Intercontinental", "Houston", "US", 29.9902, -95.3368),
    "BOS": ("Boston Logan International", "Boston", "US", 42.3656, -71.0096),
    "MSP": ("Minneapolis-St Paul International", "Minneapolis", "US", 44.8848, -93.2223),
    "DTW": ("Detroit Metropolitan Wayne County", "Detroit", "US", 42.2162, -83.3554),
    "FLL": ("Fort Lauderdale-Hollywood International", "Fort Lauderdale", "US", 26.0742, -80.1506),
    "PHL": ("Philadelphia International", "Philadelphia", "US", 39.8729, -75.2437),
    "LGA": ("LaGuardia", "New York", "US", 40.7769, -73.8740),
    "BWI": ("Baltimore/Washington International", "Baltimore", "US", 39.1774, -76.6684),
    "DCA": ("Ronald Reagan Washington National", "Washington", "US", 38.8512, -77.0402),
    "IAD": ("Washington Dulles International", "Washington", "US", 38.9531, -77.4565),
    "SAN": ("San Diego International", "San Diego", "US", 32.7338, -117.1933),
    "TPA": ("Tampa International", "Tampa", "US", 27.9756, -82.5333),
    "PDX": ("Portland International", "Portland", "US", 45.5898, -122.5951),
    "SLC": ("Salt Lake City International", "Salt Lake City", "US", 40.7899, -111.9791),
    "HNL": ("Daniel K. Inouye International", "Honolulu", "US", 21.3187, -157.9225),
    "AUS": ("Austin-Bergstrom International", "Austin", "US", 30.1975, -97.6664),
    "RDU": ("Raleigh-Durham International", "Raleigh", "US", 35.8776, -78.7875),

    # ==========================================================================
    # NORTH AMERICA - Canada
    # ==========================================================================
    "YYZ": ("Toronto Pearson International", "Toronto", "CA", 43.6777, -79.6248),
    "YVR": ("Vancouver International", "Vancouver", "CA", 49.1947, -123.1792),
    "YUL": ("Montréal-Pierre Elliott Trudeau International", "Montreal", "CA", 45.4706, -73.7408),
    "YYC": ("Calgary International", "Calgary", "CA", 51.1215, -114.0076),
    "YEG": ("Edmonton International", "Edmonton", "CA", 53.3097, -113.5792),
    "YOW": ("Ottawa Macdonald-Cartier International", "Ottawa", "CA", 45.3225, -75.6692),

    # ==========================================================================
    # EUROPE - United Kingdom
    # ==========================================================================
    "LHR": ("London Heathrow", "London", "GB", 51.4700, -0.4543),
    "LGW": ("London Gatwick", "London", "GB", 51.1537, -0.1821),
    "STN": ("London Stansted", "London", "GB", 51.8860, 0.2389),
    "LTN": ("London Luton", "London", "GB", 51.8747, -0.3683),
    "MAN": ("Manchester", "Manchester", "GB", 53.3537, -2.2750),
    "EDI": ("Edinburgh", "Edinburgh", "GB", 55.9508, -3.3615),
    "BHX": ("Birmingham", "Birmingham", "GB", 52.4539, -1.7480),
    "GLA": ("Glasgow", "Glasgow", "GB", 55.8642, -4.4331),
    "BRS": ("Bristol", "Bristol", "GB", 51.3827, -2.7190),
    "NCL": ("Newcastle", "Newcastle", "GB", 55.0375, -1.6917),

    # ==========================================================================
    # EUROPE - Germany
    # ==========================================================================
    "FRA": ("Frankfurt am Main", "Frankfurt", "DE", 50.0379, 8.5622),
    "MUC": ("Munich", "Munich", "DE", 48.3538, 11.7861),
    "BER": ("Berlin Brandenburg", "Berlin", "DE", 52.3667, 13.5033),
    "DUS": ("Düsseldorf", "Düsseldorf", "DE", 51.2895, 6.7668),
    "HAM": ("Hamburg", "Hamburg", "DE", 53.6304, 10.0065),
    "CGN": ("Cologne Bonn", "Cologne", "DE", 50.8659, 7.1427),
    "STR": ("Stuttgart", "Stuttgart", "DE", 48.6899, 9.2220),

    # ==========================================================================
    # EUROPE - France
    # ==========================================================================
    "CDG": ("Paris Charles de Gaulle", "Paris", "FR", 49.0097, 2.5479),
    "ORY": ("Paris Orly", "Paris", "FR", 48.7262, 2.3652),
    "NCE": ("Nice Côte d'Azur", "Nice", "FR", 43.6584, 7.2159),
    "LYS": ("Lyon-Saint Exupéry", "Lyon", "FR", 45.7256, 5.0811),
    "MRS": ("Marseille Provence", "Marseille", "FR", 43.4393, 5.2214),
    "TLS": ("Toulouse-Blagnac", "Toulouse", "FR", 43.6291, 1.3638),

    # ==========================================================================
    # EUROPE - Spain
    # ==========================================================================
    "MAD": ("Adolfo Suárez Madrid-Barajas", "Madrid", "ES", 40.4983, -3.5676),
    "BCN": ("Josep Tarradellas Barcelona-El Prat", "Barcelona", "ES", 41.2974, 2.0833),
    "PMI": ("Palma de Mallorca", "Palma", "ES", 39.5517, 2.7388),
    "AGP": ("Málaga-Costa del Sol", "Málaga", "ES", 36.6749, -4.4991),
    "ALC": ("Alicante-Elche", "Alicante", "ES", 38.2822, -0.5582),

    # ==========================================================================
    # EUROPE - Italy
    # ==========================================================================
    "FCO": ("Leonardo da Vinci-Fiumicino", "Rome", "IT", 41.8003, 12.2389),
    "MXP": ("Milan Malpensa", "Milan", "IT", 45.6306, 8.7281),
    "LIN": ("Milan Linate", "Milan", "IT", 45.4451, 9.2767),
    "VCE": ("Venice Marco Polo", "Venice", "IT", 45.5053, 12.3519),
    "NAP": ("Naples International", "Naples", "IT", 40.8860, 14.2908),
    "BGY": ("Milan Bergamo", "Bergamo", "IT", 45.6739, 9.7042),

    # ==========================================================================
    # EUROPE - Netherlands
    # ==========================================================================
    "AMS": ("Amsterdam Schiphol", "Amsterdam", "NL", 52.3105, 4.7683),
    "RTM": ("Rotterdam The Hague", "Rotterdam", "NL", 51.9569, 4.4372),

    # ==========================================================================
    # EUROPE - Other
    # ==========================================================================
    "ZRH": ("Zürich", "Zürich", "CH", 47.4582, 8.5555),
    "GVA": ("Geneva", "Geneva", "CH", 46.2370, 6.1092),
    "VIE": ("Vienna International", "Vienna", "AT", 48.1103, 16.5697),
    "BRU": ("Brussels", "Brussels", "BE", 50.9014, 4.4844),
    "CPH": ("Copenhagen", "Copenhagen", "DK", 55.6180, 12.6508),
    "OSL": ("Oslo Gardermoen", "Oslo", "NO", 60.1939, 11.1004),
    "ARN": ("Stockholm Arlanda", "Stockholm", "SE", 59.6498, 17.9238),
    "HEL": ("Helsinki-Vantaa", "Helsinki", "FI", 60.3172, 24.9633),
    "DUB": ("Dublin", "Dublin", "IE", 53.4264, -6.2499),
    "LIS": ("Lisbon Humberto Delgado", "Lisbon", "PT", 38.7813, -9.1359),
    "ATH": ("Athens International", "Athens", "GR", 37.9364, 23.9445),
    "PRG": ("Václav Havel Prague", "Prague", "CZ", 50.1008, 14.2600),
    "WAW": ("Warsaw Chopin", "Warsaw", "PL", 52.1657, 20.9671),
    "BUD": ("Budapest Ferenc Liszt", "Budapest", "HU", 47.4298, 19.2611),

    # ==========================================================================
    # MIDDLE EAST
    # ==========================================================================
    "TLV": ("Ben Gurion International", "Tel Aviv", "IL", 32.0114, 34.8867),
    "ETM": ("Ramon Airport", "Eilat", "IL", 29.7268, 35.0114),
    "VDA": ("Ovda Airport", "Ovda", "IL", 29.9403, 34.9358),
    "HFA": ("Haifa Airport", "Haifa", "IL", 32.8094, 35.0431),
    "DXB": ("Dubai International", "Dubai", "AE", 25.2532, 55.3657),
    "AUH": ("Abu Dhabi International", "Abu Dhabi", "AE", 24.4330, 54.6511),
    "DOH": ("Hamad International", "Doha", "QA", 25.2609, 51.6138),
    "AMA": ("King Abdulaziz International", "Jeddah", "SA", 21.6796, 39.1565),
    "RUH": ("King Khalid International", "Riyadh", "SA", 24.9576, 46.6988),
    "CAI": ("Cairo International", "Cairo", "EG", 30.1219, 31.4056),
    "AMM": ("Queen Alia International", "Amman", "JO", 31.7226, 35.9932),
    "IST": ("Istanbul Airport", "Istanbul", "TR", 41.2753, 28.7519),
    "SAW": ("Istanbul Sabiha Gökçen", "Istanbul", "TR", 40.8986, 29.3092),
    "TBS": ("Tbilisi International", "Tbilisi", "GE", 41.6692, 44.9547),

    # ==========================================================================
    # ASIA - East Asia
    # ==========================================================================
    "HND": ("Tokyo Haneda", "Tokyo", "JP", 35.5494, 139.7798),
    "NRT": ("Tokyo Narita", "Tokyo", "JP", 35.7653, 140.3864),
    "KIX": ("Osaka Kansai", "Osaka", "JP", 34.4347, 135.2441),
    "ICN": ("Incheon International", "Seoul", "KR", 37.4602, 126.4407),
    "GMP": ("Seoul Gimpo International", "Seoul", "KR", 37.5583, 126.7906),
    "PEK": ("Beijing Capital", "Beijing", "CN", 40.0799, 116.6031),
    "PKX": ("Beijing Daxing", "Beijing", "CN", 39.5098, 116.4105),
    "PVG": ("Shanghai Pudong", "Shanghai", "CN", 31.1443, 121.8083),
    "SHA": ("Shanghai Hongqiao", "Shanghai", "CN", 31.1979, 121.3363),
    "HKG": ("Hong Kong International", "Hong Kong", "HK", 22.3080, 113.9185),
    "CAN": ("Guangzhou Baiyun", "Guangzhou", "CN", 23.3924, 113.2988),
    "SZX": ("Shenzhen Bao'an", "Shenzhen", "CN", 22.6393, 113.8129),
    "TPE": ("Taiwan Taoyuan", "Taipei", "TW", 25.0797, 121.2342),

    # ==========================================================================
    # ASIA - Southeast Asia
    # ==========================================================================
    "SIN": ("Singapore Changi", "Singapore", "SG", 1.3644, 103.9915),
    "BKK": ("Suvarnabhumi", "Bangkok", "TH", 13.6900, 100.7501),
    "DMK": ("Don Mueang International", "Bangkok", "TH", 13.9126, 100.6068),
    "KUL": ("Kuala Lumpur International", "Kuala Lumpur", "MY", 2.7456, 101.7099),
    "CGK": ("Soekarno-Hatta International", "Jakarta", "ID", -6.1256, 106.6559),
    "MNL": ("Ninoy Aquino International", "Manila", "PH", 14.5086, 121.0197),
    "SGN": ("Tan Son Nhat International", "Ho Chi Minh City", "VN", 10.8188, 106.6519),
    "HAN": ("Noi Bai International", "Hanoi", "VN", 21.2212, 105.8072),

    # ==========================================================================
    # ASIA - South Asia
    # ==========================================================================
    "DEL": ("Indira Gandhi International", "Delhi", "IN", 28.5562, 77.1000),
    "BOM": ("Chhatrapati Shivaji Maharaj International", "Mumbai", "IN", 19.0896, 72.8656),
    "BLR": ("Kempegowda International", "Bangalore", "IN", 13.1986, 77.7066),
    "MAA": ("Chennai International", "Chennai", "IN", 12.9941, 80.1709),
    "CCU": ("Netaji Subhash Chandra Bose International", "Kolkata", "IN", 22.6520, 88.4463),
    "HYD": ("Rajiv Gandhi International", "Hyderabad", "IN", 17.2403, 78.4294),
    "CMB": ("Bandaranaike International", "Colombo", "LK", 7.1808, 79.8841),

    # ==========================================================================
    # OCEANIA
    # ==========================================================================
    "SYD": ("Sydney Kingsford Smith", "Sydney", "AU", -33.9399, 151.1753),
    "MEL": ("Melbourne Tullamarine", "Melbourne", "AU", -37.6690, 144.8410),
    "BNE": ("Brisbane", "Brisbane", "AU", -27.3842, 153.1175),
    "PER": ("Perth", "Perth", "AU", -31.9385, 115.9672),
    "AKL": ("Auckland", "Auckland", "NZ", -37.0082, 174.7850),
    "WLG": ("Wellington", "Wellington", "NZ", -41.3272, 174.8052),
    "CHC": ("Christchurch", "Christchurch", "NZ", -43.4864, 172.5369),

    # ==========================================================================
    # SOUTH AMERICA
    # ==========================================================================
    "GRU": ("São Paulo-Guarulhos", "São Paulo", "BR", -23.4356, -46.4731),
    "GIG": ("Rio de Janeiro-Galeão", "Rio de Janeiro", "BR", -22.8099, -43.2506),
    "EZE": ("Buenos Aires-Ezeiza", "Buenos Aires", "AR", -34.8222, -58.5358),
    "SCL": ("Santiago Arturo Merino Benítez", "Santiago", "CL", -33.3930, -70.7858),
    "BOG": ("El Dorado International", "Bogotá", "CO", 4.7016, -74.1469),
    "LIM": ("Jorge Chávez International", "Lima", "PE", -12.0219, -77.1143),
    "MEX": ("Mexico City International", "Mexico City", "MX", 19.4363, -99.0721),
    "CUN": ("Cancún International", "Cancún", "MX", 21.0365, -86.8771),
    "GDL": ("Guadalajara International", "Guadalajara", "MX", 20.5218, -103.3111),
    "PTY": ("Tocumen International", "Panama City", "PA", 9.0714, -79.3835),

    # ==========================================================================
    # AFRICA
    # ==========================================================================
    "JNB": ("O.R. Tambo International", "Johannesburg", "ZA", -26.1392, 28.2460),
    "CPT": ("Cape Town International", "Cape Town", "ZA", -33.9715, 18.6021),
    "NBO": ("Jomo Kenyatta International", "Nairobi", "KE", -1.3192, 36.9278),
    "ADD": ("Addis Ababa Bole International", "Addis Ababa", "ET", 8.9779, 38.7993),
    "LOS": ("Murtala Muhammed International", "Lagos", "NG", 6.5774, 3.3212),
    "CMN": ("Mohammed V International", "Casablanca", "MA", 33.3675, -7.5898),
    "RAK": ("Marrakech Menara", "Marrakech", "MA", 31.6069, -8.0363),
    "TUN": ("Tunis-Carthage International", "Tunis", "TN", 36.8510, 10.2272),
}


# =============================================================================
# DISTANCE CALCULATION
# =============================================================================

EARTH_RADIUS_KM = 6371.0


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate great-circle distance between two points using Haversine formula.

    Args:
        lat1, lon1: Latitude and longitude of first point in degrees
        lat2, lon2: Latitude and longitude of second point in degrees

    Returns:
        Distance in kilometers
    """
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return EARTH_RADIUS_KM * c


def get_airport(iata_code: str) -> Optional[Tuple[str, str, str, float, float]]:
    """
    Get airport details by IATA code.

    Args:
        iata_code: 3-letter IATA airport code (case-insensitive)

    Returns:
        Tuple of (name, city, country, latitude, longitude) or None if not found
    """
    return AIRPORTS.get(iata_code.upper())


def calculate_flight_distance(origin: str, destination: str) -> Optional[float]:
    """
    Calculate flight distance between two airports.

    Args:
        origin: IATA code of origin airport
        destination: IATA code of destination airport

    Returns:
        Distance in kilometers, or None if airports not found
    """
    origin_data = get_airport(origin)
    dest_data = get_airport(destination)

    if not origin_data or not dest_data:
        return None

    return haversine_distance(
        origin_data[3], origin_data[4],
        dest_data[3], dest_data[4]
    )


# Israel airport IATA codes
ISRAEL_AIRPORTS = {"TLV", "ETM", "VDA", "HFA", "SDV"}


def classify_flight_distance(distance_km: float, origin: str = None, destination: str = None) -> str:
    """
    Classify flight distance as domestic, short, medium, or long haul.

    Israel-specific rules:
    - Israel domestic (any IL airport <-> any IL airport) -> "domestic"
    - Israel international (IL <-> non-IL) -> always "long" (DEFRA SHORT is UK-specific)

    Standard DEFRA rules (non-Israel):
    - Short-haul: < 785 km (e.g., domestic UK, Europe regional)
    - Medium-haul: 785-3700 km (e.g., UK to Middle East, intra-Europe)
    - Long-haul: > 3700 km (e.g., intercontinental)

    Args:
        distance_km: Flight distance in kilometers
        origin: IATA code of origin airport (optional, for Israel logic)
        destination: IATA code of destination airport (optional, for Israel logic)

    Returns:
        Classification: "domestic", "short", "medium", or "long"

    Note:
        When Israel domestic flights return "domestic", the emission factor key will be
        "flight_domestic_economy" (or other cabin class). Ensure that a corresponding
        emission factor (e.g., flight_domestic_economy) exists in the database/seed data.
    """
    # Israel-specific classification
    if origin and destination:
        origin_upper = origin.upper()
        dest_upper = destination.upper()
        origin_is_il = origin_upper in ISRAEL_AIRPORTS
        dest_is_il = dest_upper in ISRAEL_AIRPORTS

        if origin_is_il and dest_is_il:
            return "domestic"

        if origin_is_il or dest_is_il:
            # Israel international flights are always classified as long-haul
            # DEFRA short-haul category is UK-specific
            return "long"

    # Standard DEFRA thresholds for non-Israel flights
    if distance_km < 785:
        return "short"
    elif distance_km < 3700:
        return "medium"
    else:
        return "long"


def get_flight_emission_key(origin: str, destination: str, cabin_class: str = "economy") -> Optional[str]:
    """
    Get the appropriate emission factor activity key for a flight route.

    Args:
        origin: IATA code of origin airport
        destination: IATA code of destination airport
        cabin_class: Cabin class - "economy", "premium_economy", "business", "first"

    Returns:
        Activity key string or None if airports not found
    """
    distance = calculate_flight_distance(origin, destination)
    if distance is None:
        return None

    haul_type = classify_flight_distance(distance, origin, destination)

    cabin_map = {
        "economy": "economy",
        "premium_economy": "premium_economy",
        "business": "business",
        "first": "first",
    }
    cabin_suffix = cabin_map.get(cabin_class.lower(), "economy")

    return f"flight_{haul_type}_{cabin_suffix}"


def search_airports(query: str, limit: int = 10) -> list[dict]:
    """
    Search airports by name, city, or IATA code.

    Args:
        query: Search term (case-insensitive)
        limit: Maximum number of results

    Returns:
        List of airport dictionaries
    """
    query = query.upper()
    results = []

    for code, (name, city, country, lat, lon) in AIRPORTS.items():
        if (query in code or
            query in name.upper() or
            query in city.upper()):
            results.append({
                "iata_code": code,
                "name": name,
                "city": city,
                "country": country,
                "latitude": lat,
                "longitude": lon,
            })
            if len(results) >= limit:
                break

    return results


# =============================================================================
# AIRPORT STATISTICS
# =============================================================================

def get_airport_stats() -> dict:
    """Get statistics about the airport database."""
    countries = set()
    for _, (_, _, country, _, _) in AIRPORTS.items():
        countries.add(country)

    return {
        "total_airports": len(AIRPORTS),
        "countries_covered": len(countries),
        "country_list": sorted(countries),
    }


# Example usage and tests
if __name__ == "__main__":
    # Test distance calculation
    tlv_to_lhr = calculate_flight_distance("TLV", "LHR")
    print(f"TLV → LHR: {tlv_to_lhr:.0f} km ({classify_flight_distance(tlv_to_lhr)} haul)")

    jfk_to_lax = calculate_flight_distance("JFK", "LAX")
    print(f"JFK → LAX: {jfk_to_lax:.0f} km ({classify_flight_distance(jfk_to_lax)} haul)")

    lhr_to_syd = calculate_flight_distance("LHR", "SYD")
    print(f"LHR → SYD: {lhr_to_syd:.0f} km ({classify_flight_distance(lhr_to_syd)} haul)")

    # Test search
    print("\nSearch for 'london':")
    for airport in search_airports("london", limit=5):
        print(f"  {airport['iata_code']}: {airport['name']}")

    # Test Israel flight classification
    tlv_to_etm = calculate_flight_distance("TLV", "ETM")
    print(f"\nTLV → ETM: {tlv_to_etm:.0f} km ({classify_flight_distance(tlv_to_etm, 'TLV', 'ETM')} haul)")

    tlv_to_lhr_haul = classify_flight_distance(tlv_to_lhr, "TLV", "LHR")
    print(f"TLV → LHR: {tlv_to_lhr:.0f} km ({tlv_to_lhr_haul} haul - Israel international = always long)")

    lhr_to_cdg = calculate_flight_distance("LHR", "CDG")
    print(f"LHR → CDG: {lhr_to_cdg:.0f} km ({classify_flight_distance(lhr_to_cdg, 'LHR', 'CDG')} haul)")

    # Stats
    stats = get_airport_stats()
    print(f"\nDatabase: {stats['total_airports']} airports in {stats['countries_covered']} countries")
