# clean.py
import pandas as pd

df = pd.read_csv("raw_listings.csv")

# Drop obvious empties
df = df.dropna(subset=["price"]).copy()

# Price per sqft
if {"price","sqft"}.issubset(df.columns):
    df["price_per_sqft"] = (df["price"] / df["sqft"]).where(df["sqft"] > 0)

# Normalize prop type
if "prop_type" in df.columns:
    df["prop_type"] = df["prop_type"].fillna("unknown").str.replace("_"," ").str.title()

# Dedupe
subset_cols = [c for c in ["property_id","address","city","state","postal_code","price"] if c in df.columns]
if subset_cols:
    df = df.drop_duplicates(subset=subset_cols)

# Order columns
cols = [c for c in ["property_id","price","price_per_sqft","beds","baths","sqft",
                    "prop_type","address","city","state","postal_code",
                    "latitude","longitude","list_date"] if c in df.columns]
df = df[cols]

df.to_csv("clean_listings.csv", index=False)
print(f"✅ Saved {len(df)} rows to clean_listings.csv")
