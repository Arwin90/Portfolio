"""Werkt weerroute66.json bij met de NWS-weersvoorspelling (api.weather.gov).

Draait elke ochtend via GitHub Actions. Dagen binnen de voorspelling krijgen
de echte min/max; de rest houdt de waarden uit het reisschema.
"""
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

# dag, datum, locatie, lat, lon, schema_min, schema_max
SCHEMA = [
    (1, "2026-11-08", "Chicago, IL", 42.06, -88.08, 3, 10),
    (2, "2026-11-09", "Lincoln, IL", 40.15, -89.36, 3, 11),
    (3, "2026-11-10", "Rolla, MO", 37.95, -91.77, 2, 13),
    (4, "2026-11-11", "Joplin, MO", 37.08, -94.51, 2, 13),
    (5, "2026-11-12", "Medicine Park, OK", 34.73, -98.50, 3, 16),
    (6, "2026-11-13", "Wichita Mountains Refuge, OK", 34.73, -98.60, 4, 17),
    (7, "2026-11-14", "Amarillo, TX", 35.22, -101.83, 1, 16),
    (8, "2026-11-15", "Albuquerque, NM", 35.08, -106.65, 0, 14),
    (9, "2026-11-16", "Albuquerque, NM", 35.08, -106.65, 0, 14),
    (10, "2026-11-17", "Holbrook, AZ", 34.90, -110.16, -1, 14),
    (11, "2026-11-18", "Kingman, AZ", 35.19, -114.05, 6, 21),
    (12, "2026-11-19", "Barstow, CA", 34.90, -117.02, 7, 22),
    (13, "2026-11-20", "Los Angeles, CA", 34.09, -118.37, 11, 22),
    (14, "2026-11-21", "Los Angeles, CA", 34.09, -118.37, 11, 22),
    (15, "2026-11-22", "Los Angeles, CA", 34.09, -118.37, 11, 22),
    (16, "2026-11-23", "San Diego, CA", 32.75, -117.19, 11, 20),
    (17, "2026-11-24", "San Diego, CA", 32.75, -117.19, 11, 20),
    (18, "2026-11-25", "San Diego, CA", 32.75, -117.19, 11, 20),
    (19, "2026-11-26", "San Diego, CA", 32.75, -117.19, 11, 20),
]

OUT = Path(__file__).resolve().parent.parent / "weerroute66.json"
HEADERS = {"User-Agent": "weerroute66 (www.arwin.online)", "Accept": "application/geo+json"}


def get_json(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def f_to_c(f):
    return round((f - 32) * 5 / 9)


def forecast_by_date(lat, lon):
    """{datum: {"max": °C, "min": °C}} — max = dagdeel, min = de nacht die op die datum begint."""
    point = get_json(f"https://api.weather.gov/points/{lat:.4f},{lon:.4f}")
    periods = get_json(point["properties"]["forecast"])["properties"]["periods"]
    out = {}
    for p in periods:
        datum = p["startTime"][:10]  # lokale datum van die plek
        t = p["temperature"]
        if p.get("temperatureUnit", "F") == "F":
            t = f_to_c(t)
        key = "max" if p["isDaytime"] else "min"
        out.setdefault(datum, {})[key] = t
    return out


def vorige_waarden():
    """Eerder opgeslagen voorspellingen, zodat voorbije dagen hun voorspelling houden."""
    try:
        oud = json.loads(OUT.read_text(encoding="utf-8"))
        return {d["datum"]: d for d in oud.get("dagen", []) if d.get("bron") == "voorspelling"}
    except Exception:
        return {}


def main():
    vorig = vorige_waarden()
    cache = {}
    dagen = []
    for dag, datum, loc, lat, lon, smin, smax in SCHEMA:
        key = (lat, lon)
        if key not in cache:
            try:
                cache[key] = forecast_by_date(lat, lon)
            except Exception as e:  # weerdienst even niet bereikbaar: schemawaarden houden
                print(f"Geen voorspelling voor {loc}: {e}")
                cache[key] = {}
        fc = cache[key].get(datum, {})
        mn, mx = fc.get("min"), fc.get("max")
        if mn is None and mx is None and datum in vorig:  # dag niet meer in de voorspelling: laatste waarde houden
            mn, mx = vorig[datum]["min_c"], vorig[datum]["max_c"]
        bron = "voorspelling" if (mn is not None or mx is not None) else "reisschema"
        dagen.append({
            "dag": dag, "datum": datum, "locatie": loc,
            "min_c": mn if mn is not None else smin,
            "max_c": mx if mx is not None else smax,
            "bron": bron,
        })
    data = {"bijgewerkt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "dagen": dagen}
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    n = sum(d["bron"] == "voorspelling" for d in dagen)
    print(f"Klaar: {n} van de {len(dagen)} dagen met echte voorspelling.")


if __name__ == "__main__":
    main()
