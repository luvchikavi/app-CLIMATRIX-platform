"""
Israel commuting data: city distances to major employment centers.

Provides a dictionary of 32 Israeli cities (including Tel Aviv) with driving
distances in km to four major employment hubs: Tel Aviv, Jerusalem, Haifa,
and Beer Sheva.  Also exposes helper functions for fuzzy city lookup and
distance retrieval.
"""

from __future__ import annotations

import re
from typing import Optional

# ---------------------------------------------------------------------------
# City data
# ---------------------------------------------------------------------------

ISRAEL_CITIES: dict[str, dict] = {
    "tel_aviv": {
        "name_he": "תל אביב",
        "name_en": "Tel Aviv",
        "aliases": [
            "tel-aviv", "telaviv", "tel aviv yafo", "tel aviv-yafo",
            "tel aviv jaffa", "tlv", "תל אביב יפו", "תל-אביב",
        ],
        "distance_to_tel_aviv": 0,
        "distance_to_jerusalem": 66,
        "distance_to_haifa": 100,
        "distance_to_beer_sheva": 109,
    },
    "jerusalem": {
        "name_he": "ירושלים",
        "name_en": "Jerusalem",
        "aliases": ["yerushalayim", "jlm", "ירושלים"],
        "distance_to_tel_aviv": 66,
        "distance_to_jerusalem": 0,
        "distance_to_haifa": 152,
        "distance_to_beer_sheva": 99,
    },
    "haifa": {
        "name_he": "חיפה",
        "name_en": "Haifa",
        "aliases": ["hfa", "חיפה"],
        "distance_to_tel_aviv": 100,
        "distance_to_jerusalem": 152,
        "distance_to_haifa": 0,
        "distance_to_beer_sheva": 194,
    },
    "beer_sheva": {
        "name_he": "באר שבע",
        "name_en": "Beer Sheva",
        "aliases": [
            "be'er sheva", "beersheva", "beer-sheva", "beersheba",
            "be'er sheba", "באר שבע", "באר-שבע", "b7",
        ],
        "distance_to_tel_aviv": 109,
        "distance_to_jerusalem": 99,
        "distance_to_haifa": 194,
        "distance_to_beer_sheva": 0,
    },
    "netanya": {
        "name_he": "נתניה",
        "name_en": "Netanya",
        "aliases": ["netania", "נתניה"],
        "distance_to_tel_aviv": 35,
        "distance_to_jerusalem": 71,
        "distance_to_haifa": 55,
        "distance_to_beer_sheva": None,
    },
    "ashdod": {
        "name_he": "אשדוד",
        "name_en": "Ashdod",
        "aliases": ["אשדוד"],
        "distance_to_tel_aviv": 40,
        "distance_to_jerusalem": 54,
        "distance_to_haifa": 118,
        "distance_to_beer_sheva": 70,
    },
    "ashkelon": {
        "name_he": "אשקלון",
        "name_en": "Ashkelon",
        "aliases": ["ashqelon", "אשקלון"],
        "distance_to_tel_aviv": 60,
        "distance_to_jerusalem": 62,
        "distance_to_haifa": 133,
        "distance_to_beer_sheva": 55,
    },
    "petah_tikva": {
        "name_he": "פתח תקווה",
        "name_en": "Petah Tikva",
        "aliases": [
            "petach tikva", "petach tiqwa", "petah tiqwa",
            "פתח תקווה", "פתח-תקווה", "פ\"ת",
        ],
        "distance_to_tel_aviv": 14,
        "distance_to_jerusalem": 47,
        "distance_to_haifa": 90,
        "distance_to_beer_sheva": None,
    },
    "rishon_lezion": {
        "name_he": "ראשון לציון",
        "name_en": "Rishon LeZion",
        "aliases": [
            "rishon le-zion", "rishon le zion", "rishon letsion",
            "ראשון לציון", "ראשל\"צ",
        ],
        "distance_to_tel_aviv": 15,
        "distance_to_jerusalem": 46,
        "distance_to_haifa": 105,
        "distance_to_beer_sheva": None,
    },
    "holon": {
        "name_he": "חולון",
        "name_en": "Holon",
        "aliases": ["חולון"],
        "distance_to_tel_aviv": 6,
        "distance_to_jerusalem": 49,
        "distance_to_haifa": 106,
        "distance_to_beer_sheva": None,
    },
    "bat_yam": {
        "name_he": "בת ים",
        "name_en": "Bat Yam",
        "aliases": ["bat-yam", "בת ים", "בת-ים"],
        "distance_to_tel_aviv": 7,
        "distance_to_jerusalem": 52,
        "distance_to_haifa": 108,
        "distance_to_beer_sheva": None,
    },
    "ramat_gan": {
        "name_he": "רמת גן",
        "name_en": "Ramat Gan",
        "aliases": ["ramat-gan", "רמת גן", "רמת-גן"],
        "distance_to_tel_aviv": 5,
        "distance_to_jerusalem": 52,
        "distance_to_haifa": 98,
        "distance_to_beer_sheva": None,
    },
    "bnei_brak": {
        "name_he": "בני ברק",
        "name_en": "Bnei Brak",
        "aliases": ["bne brak", "bnei-brak", "בני ברק", "בני-ברק"],
        "distance_to_tel_aviv": 7,
        "distance_to_jerusalem": 50,
        "distance_to_haifa": 96,
        "distance_to_beer_sheva": None,
    },
    "herzliya": {
        "name_he": "הרצליה",
        "name_en": "Herzliya",
        "aliases": ["hertzeliya", "hertzliya", "הרצליה"],
        "distance_to_tel_aviv": 15,
        "distance_to_jerusalem": 68,
        "distance_to_haifa": 85,
        "distance_to_beer_sheva": None,
    },
    "kfar_saba": {
        "name_he": "כפר סבא",
        "name_en": "Kfar Saba",
        "aliases": ["kfar-saba", "kfar sava", "כפר סבא", "כפר-סבא"],
        "distance_to_tel_aviv": 22,
        "distance_to_jerusalem": 54,
        "distance_to_haifa": 70,
        "distance_to_beer_sheva": None,
    },
    "raanana": {
        "name_he": "רעננה",
        "name_en": "Ra'anana",
        "aliases": ["ra'anana", "raanana", "רעננה"],
        "distance_to_tel_aviv": 18,
        "distance_to_jerusalem": 60,
        "distance_to_haifa": 75,
        "distance_to_beer_sheva": None,
    },
    "rehovot": {
        "name_he": "רחובות",
        "name_en": "Rehovot",
        "aliases": ["rechovot", "רחובות"],
        "distance_to_tel_aviv": 25,
        "distance_to_jerusalem": 41,
        "distance_to_haifa": 115,
        "distance_to_beer_sheva": 85,
    },
    "modiin": {
        "name_he": "מודיעין",
        "name_en": "Modiin",
        "aliases": [
            "modi'in", "modiin-maccabim-reut", "modiin maccabim reut",
            "מודיעין", "מודיעין-מכבים-רעות",
        ],
        "distance_to_tel_aviv": 39,
        "distance_to_jerusalem": 30,
        "distance_to_haifa": 130,
        "distance_to_beer_sheva": None,
    },
    "lod": {
        "name_he": "לוד",
        "name_en": "Lod",
        "aliases": ["lydda", "לוד"],
        "distance_to_tel_aviv": 22,
        "distance_to_jerusalem": 40,
        "distance_to_haifa": 110,
        "distance_to_beer_sheva": None,
    },
    "ramla": {
        "name_he": "רמלה",
        "name_en": "Ramla",
        "aliases": ["ramle", "רמלה"],
        "distance_to_tel_aviv": 22,
        "distance_to_jerusalem": 38,
        "distance_to_haifa": 112,
        "distance_to_beer_sheva": None,
    },
    "hadera": {
        "name_he": "חדרה",
        "name_en": "Hadera",
        "aliases": ["חדרה"],
        "distance_to_tel_aviv": 50,
        "distance_to_jerusalem": 80,
        "distance_to_haifa": 42,
        "distance_to_beer_sheva": None,
    },
    "nazareth": {
        "name_he": "נצרת",
        "name_en": "Nazareth",
        "aliases": ["natzeret", "natzrat", "נצרת", "נצרת עילית"],
        "distance_to_tel_aviv": 105,
        "distance_to_jerusalem": 104,
        "distance_to_haifa": 32,
        "distance_to_beer_sheva": None,
    },
    "afula": {
        "name_he": "עפולה",
        "name_en": "Afula",
        "aliases": ["עפולה"],
        "distance_to_tel_aviv": 90,
        "distance_to_jerusalem": 93,
        "distance_to_haifa": 32,
        "distance_to_beer_sheva": None,
    },
    "nahariya": {
        "name_he": "נהריה",
        "name_en": "Nahariya",
        "aliases": ["nahariyya", "נהריה"],
        "distance_to_tel_aviv": 115,
        "distance_to_jerusalem": 138,
        "distance_to_haifa": 26,
        "distance_to_beer_sheva": None,
    },
    "acre": {
        "name_he": "עכו",
        "name_en": "Acre",
        "aliases": ["akko", "acco", "ako", "עכו"],
        "distance_to_tel_aviv": 105,
        "distance_to_jerusalem": 129,
        "distance_to_haifa": 15,
        "distance_to_beer_sheva": None,
    },
    "tiberias": {
        "name_he": "טבריה",
        "name_en": "Tiberias",
        "aliases": ["tverya", "tveria", "טבריה"],
        "distance_to_tel_aviv": 140,
        "distance_to_jerusalem": 150,
        "distance_to_haifa": 51,
        "distance_to_beer_sheva": None,
    },
    "carmiel": {
        "name_he": "כרמיאל",
        "name_en": "Carmiel",
        "aliases": ["karmiel", "כרמיאל"],
        "distance_to_tel_aviv": 129,
        "distance_to_jerusalem": 150,
        "distance_to_haifa": 31,
        "distance_to_beer_sheva": None,
    },
    "yokneam": {
        "name_he": "יוקנעם",
        "name_en": "Yokneam",
        "aliases": ["yoqneam", "yokneam illit", "יוקנעם", "יוקנעם עילית"],
        "distance_to_tel_aviv": 90,
        "distance_to_jerusalem": 120,
        "distance_to_haifa": 24,
        "distance_to_beer_sheva": None,
    },
    "kiryat_shmona": {
        "name_he": "קריית שמונה",
        "name_en": "Kiryat Shmona",
        "aliases": [
            "qiryat shmona", "kiryat shemona", "kiriat shmona",
            "קריית שמונה", "קרית שמונה",
        ],
        "distance_to_tel_aviv": 192,
        "distance_to_jerusalem": 200,
        "distance_to_haifa": 80,
        "distance_to_beer_sheva": None,
    },
    "eilat": {
        "name_he": "אילת",
        "name_en": "Eilat",
        "aliases": ["elat", "אילת"],
        "distance_to_tel_aviv": 350,
        "distance_to_jerusalem": 310,
        "distance_to_haifa": 450,
        "distance_to_beer_sheva": 245,
    },
    "dimona": {
        "name_he": "דימונה",
        "name_en": "Dimona",
        "aliases": ["דימונה"],
        "distance_to_tel_aviv": 148,
        "distance_to_jerusalem": 110,
        "distance_to_haifa": 250,
        "distance_to_beer_sheva": 35,
    },
    "arad": {
        "name_he": "ערד",
        "name_en": "Arad",
        "aliases": ["ערד"],
        "distance_to_tel_aviv": 140,
        "distance_to_jerusalem": 95,
        "distance_to_haifa": 240,
        "distance_to_beer_sheva": 45,
    },
}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _normalize(text: str) -> str:
    """Lower-case, strip, and collapse whitespace / punctuation for matching."""
    text = text.strip().lower()
    # Replace common separators with a single space
    text = re.sub(r"[-_''\u2019/]+", " ", text)
    # Collapse multiple spaces
    text = re.sub(r"\s+", " ", text)
    return text


def _matches(query_norm: str, city: dict) -> bool:
    """Return True if *query_norm* matches any name or alias of *city*."""
    candidates = [city["name_en"], city["name_he"]] + city["aliases"]
    for candidate in candidates:
        if _normalize(candidate) == query_norm:
            return True
    return False


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def search_cities(query: str) -> list[dict]:
    """Search for cities matching *query* using fuzzy matching.

    The search is case-insensitive and tolerates common punctuation
    variations (hyphens, underscores, apostrophes).  It checks against
    ``name_en``, ``name_he``, and every entry in ``aliases``.

    Parameters
    ----------
    query:
        Free-text city name in English or Hebrew.

    Returns
    -------
    list[dict]
        List of matching city dictionaries.  Each dict is a *copy* of the
        corresponding ``ISRAEL_CITIES`` entry with an additional ``"key"``
        field holding the normalised dictionary key.
    """
    query_norm = _normalize(query)
    if not query_norm:
        return []

    results: list[dict] = []

    for key, city in ISRAEL_CITIES.items():
        # Exact match (after normalisation)
        if _matches(query_norm, city):
            results.append({**city, "key": key})
            continue

        # Substring / partial match — match if the query is fully contained
        # in one of the candidate strings or vice-versa.
        candidates = [city["name_en"], city["name_he"]] + city["aliases"]
        for candidate in candidates:
            candidate_norm = _normalize(candidate)
            if query_norm in candidate_norm or candidate_norm in query_norm:
                results.append({**city, "key": key})
                break

    return results


def get_commuting_distance(
    city: str,
    office_city: str = "tel_aviv",
) -> Optional[int]:
    """Return the driving distance (km) from *city* to *office_city*.

    Parameters
    ----------
    city:
        Name of the employee's home city (English, Hebrew, or alias).
    office_city:
        Normalised key of the office location.  Must be one of
        ``"tel_aviv"``, ``"jerusalem"``, ``"haifa"``, or ``"beer_sheva"``.
        Defaults to ``"tel_aviv"``.

    Returns
    -------
    int | None
        Distance in kilometres, or ``None`` if the city was not found or no
        distance data is available for the requested office city.
    """
    # Map office_city to the correct distance field
    field_map: dict[str, str] = {
        "tel_aviv": "distance_to_tel_aviv",
        "jerusalem": "distance_to_jerusalem",
        "haifa": "distance_to_haifa",
        "beer_sheva": "distance_to_beer_sheva",
    }

    field = field_map.get(office_city)
    if field is None:
        return None

    matches = search_cities(city)
    if not matches:
        return None

    # Use the first match
    return matches[0].get(field)
