import os, json
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

API_BASE = os.getenv("REALTOR_API_BASE", "").rstrip("/")
API_KEY  = os.getenv("REALTOR_API_KEY", "")
HOST     = "realtor-com4.p.rapidapi.com"

HEADERS = {
    "x-rapidapi-key": API_KEY,
    "x-rapidapi-host": HOST,
}

def _get_location_slug(city: str, state: str) -> str:
    """Find a slug like 'Bowie_MD' from auto-complete."""
    url = f"{API_BASE}/auto-complete"
    params = {"input": f"{city}, {state}"}
    r = requests.get(url, headers=HEADERS, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()
    items = (data or {}).get("autocomplete", []) or []
    for it in items:
        if (
            (it or {}).get("area_type") == "city" and
            ((it or {}).get("city") or "").lower() == city.lower() and
            ((it or {}).get("state_code") or "").upper() == state.upper()
        ):
            return (it or {}).get("slug_id") or f"{city}_{state}"
    # fallback guess
    return f"{city}_{state}"

def _pick(obj, *path_options):
    """Safely pick the first existing nested value; never throws."""
    for path in path_options:
        cur = obj
        ok = True
        for part in path.split("."):
            if isinstance(cur, dict):
                cur = cur.get(part)
            else:
                ok = False
                break
        if ok and cur is not None:
            return cur
    return None

def fetch_listings(city: str, state: str, limit: int = 10):
    if not API_BASE or not API_KEY:
        raise RuntimeError("Missing REALTOR_API_BASE or REALTOR_API_KEY in .env")

    slug = _get_location_slug(city, state)

    url = f"{API_BASE}/properties/list_v2"
    params = {
        "location": slug,           # REQUIRED for this endpoint
        "limit": int(limit),
        "offset": 0,
        "sortField": "list_date",
        "sortDirection": "desc",
        # Add optional filters if you want:
        # "status": "for_sale,ready_to_build",
        # "price_min": 100000,
        # "price_max": 900000,
        # "beds_min": 2,
    }

    r = requests.get(url, headers=HEADERS, params=params, timeout=30)
    r.raise_for_status()
    raw = r.json() or {}

    results = (((raw.get("data") or {}).get("home_search") or {}).get("results") or []) or []
    # Normalize
    rows = []
    for it in results:
        it = it or {}
        rows.append({
            "property_id": _pick(it, "property_id", "id", "listing_id"),
            "price": _pick(it, "list_price", "price"),
            "beds": _pick(it, "description.beds", "beds"),
            "baths": _pick(it, "description.baths", "baths"),
            "sqft": _pick(it, "description.sqft", "building_size.size", "sqft"),
            "address": _pick(it, "location.address.line", "address.line"),
            "city": _pick(it, "location.address.city", "address.city"),
            "state": _pick(it, "location.address.state_code", "address.state_code"),
            "postal_code": _pick(it, "location.address.postal_code", "address.postal_code"),
            "latitude": _pick(it, "location.address.coordinate.lat", "location.lat", "lat"),
            "longitude": _pick(it, "location.address.coordinate.lon", "location.lon", "lng", "lon"),
            "prop_type": _pick(it, "description.type"),
            "list_date": _pick(it, "list_date"),
        })

    df = pd.DataFrame(rows)
    return df, slug, raw
