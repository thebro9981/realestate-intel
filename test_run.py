import os, json
from dotenv import load_dotenv
from realtor import fetch_listings

load_dotenv()
CITY  = os.getenv("CITY", "Bowie")
STATE = os.getenv("STATE_CODE", "MD")
LIMIT = int(os.getenv("LIMIT", "10"))

print(f"[info] CITY={CITY} STATE={STATE} LIMIT={LIMIT}")

try:
    df, slug, raw = fetch_listings(CITY, STATE, LIMIT)
    print(f"[info] using location slug: {slug}")
    if df is None or df.empty:
        print("[warn] No data returned. Showing first 800 chars of raw JSON for debugging:")
        snippet = json.dumps(raw, indent=2)[:800]
        print(snippet if snippet else "(empty JSON)")
    else:
        print(df.head(5).to_string(index=False))
        df.to_csv("raw_listings.csv", index=False)
        print("✅ Saved data to raw_listings.csv")
except Exception as e:
    print(f"[error] Request failed: {e}")
