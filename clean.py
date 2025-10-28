import pandas as pd
from pathlib import Path

RAW = Path("raw_listings.csv")
OUT = Path("clean_listings.csv")

def run():
    if not RAW.exists():
        raise SystemExit("raw_listings.csv not found. Run test_run.py first.")

    df = pd.read_csv(RAW)

    # --- Keep only the columns we care about (they exist in your output) ---
    keep = [
        "property_id","price","beds","baths","sqft","address","city",
        "state","postal_code","latitude","longitude","prop_type","list_date"
    ]
    df = df[[c for c in keep if c in df.columns]].copy()

    # --- Types / coercions ---
    num_cols = ["price","beds","baths","sqft","latitude","longitude"]
    for c in num_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    # Filter out obviously bad rows
    if "sqft" in df.columns:
        df = df[(df["sqft"].isna()) | (df["sqft"] > 0)]

    # price_per_sqft
    if {"price","sqft"}.issubset(df.columns):
        df["price_per_sqft"] = (df["price"] / df["sqft"]).where(df["sqft"] > 0)
        df["price_per_sqft"] = df["price_per_sqft"].round(2)

    # Deduplicate (same property_id latest list_date wins)
    if "property_id" in df.columns:
        df = df.sort_values("list_date").drop_duplicates(subset=["property_id"], keep="last")

    # Sort newest first
    if "list_date" in df.columns:
        df = df.sort_values("list_date", ascending=False)

    # Save
    df.to_csv(OUT, index=False)
    print(f"✅ Saved {len(df):,} rows to {OUT}")

    # Quick preview
    cols = [c for c in ["address","city","price","beds","baths","sqft","price_per_sqft","list_date"] if c in df.columns]
    print(df[cols].head(10).to_string(index=False))

if __name__ == "__main__":
    run()
