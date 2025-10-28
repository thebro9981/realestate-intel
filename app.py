import pandas as pd
import numpy as np
from pathlib import Path
import streamlit as st
import plotly.express as px
import pydeck as pdk  # pip install pydeck

st.set_page_config(page_title="Real Estate Intelligence — Bowie, MD", layout="wide")
CSV = Path("clean_listings.csv")

@st.cache_data
def load_data():
    if not CSV.exists():
        st.error("clean_listings.csv not found. Run: python clean.py")
        st.stop()
    df = pd.read_csv(CSV)
    for c in ["price","beds","baths","sqft","price_per_sqft","latitude","longitude"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    if "list_date" in df.columns:
        df["list_date"] = pd.to_datetime(df["list_date"], errors="coerce")
    if "city" not in df.columns:
        df["city"] = "Bowie"
    if "address" in df.columns:
        df["addr_short"] = df["address"].apply(lambda s: s if isinstance(s,str) and len(s)<=26 else (s[:25]+"…") if isinstance(s,str) else "")
    else:
        df["addr_short"] = ""
    return df

df = load_data()

# ---- SIDEBAR FILTERS ----
st.sidebar.header("Filters")
cities = sorted(df["city"].dropna().unique().tolist())
city_sel = st.sidebar.multiselect("City", options=cities, default=(["Bowie"] if "Bowie" in cities else cities[:1]))

min_price, max_price = int(df["price"].min()), int(df["price"].max())
price_range = st.sidebar.slider("Price ($)", min_price, max_price, (min_price, max_price), step=10000)

beds_min  = st.sidebar.number_input("Min Beds",  min_value=0, value=0, step=1)
baths_min = st.sidebar.number_input("Min Baths", min_value=0, value=0, step=1)

if df["sqft"].notna().any():
    sqft_min, sqft_max = int(np.nanmin(df["sqft"])), int(np.nanmax(df["sqft"]))
    sqft_cut = st.sidebar.slider("Min Sqft", sqft_min, sqft_max, sqft_min, step=100)
else:
    sqft_cut = 0

mask = (
    df["price"].between(*price_range) &
    (df["beds"].fillna(0)  >= beds_min) &
    (df["baths"].fillna(0) >= baths_min)
)
if city_sel:
    mask &= df["city"].isin(city_sel)
if "sqft" in df and df["sqft"].notna().any():
    mask &= (df["sqft"].fillna(0) >= sqft_cut)

df_f = df.loc[mask].copy()

# ---- HEADER + KPIs ----
st.title("🏠 Real Estate Intelligence — Bowie, MD")
st.caption("Automated data pipeline → cleaning → visualization dashboard")

k1,k2,k3,k4 = st.columns(4)
with k1: st.metric("Listings", f"{len(df_f):,}")
with k2: st.metric("Avg Price", f"${df_f['price'].mean():,.0f}" if len(df_f) else "—")
with k3: st.metric("Avg $/Sqft", f"${df_f['price_per_sqft'].mean():,.0f}" if "price_per_sqft" in df_f else "—")
with k4:
    newest = df_f["list_date"].max() if "list_date" in df_f else pd.NaT
    st.metric("Newest List", newest.strftime("%Y-%m-%d") if pd.notna(newest) else "—")

st.divider()

# ---- TOP 15 BAR ----
st.subheader("📊 Top 15 Listings by Price")
top = df_f.sort_values("price", ascending=False).head(15)
if not top.empty:
    fig = px.bar(
        top, x="addr_short", y="price", text="price",
        template="plotly_dark", labels={"addr_short":"Address","price":"Price ($)"}
    )
    fig.update_traces(texttemplate="$%{text:,.0f}", textposition="outside")
    fig.update_layout(margin=dict(l=10,r=10,t=30,b=10), xaxis_tickangle=-20, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("No data matches your filters.")

# ---- ANALYTICS ROW ----
cL,cR = st.columns(2)

with cL:
    st.subheader("Price Distribution")
    if not df_f.empty:
        hist = px.histogram(df_f, x="price", nbins=20, template="plotly_dark", labels={"price":"Price ($)"})
        hist.update_layout(margin=dict(l=10,r=10,t=30,b=10))
        st.plotly_chart(hist, use_container_width=True)
    else:
        st.info("No data to show.")

with cR:
    st.subheader("Price per Sqft vs Sqft")
    scatter_df = df_f.dropna(subset=["price_per_sqft","sqft"])
    if not scatter_df.empty:
        sc = px.scatter(
            scatter_df, x="sqft", y="price_per_sqft",
            hover_data=["address","beds","baths","price"],
            template="plotly_dark",
            labels={"sqft":"Sqft","price_per_sqft":"$/Sqft"},
        )
        sc.update_layout(margin=dict(l=10,r=10,t=30,b=10))
        st.plotly_chart(sc, use_container_width=True)
    else:
        st.info("Need sqft + $/sqft to display.")

st.divider()

# ---- MAP ----
st.subheader("🗺️ Property Map")
latlon = df_f.dropna(subset=["latitude","longitude"]).copy()
if not latlon.empty:
    tooltip = {
        "html": "<b>{address}</b><br/>${price} • {beds} bd / {baths} ba<br/>{city}, {state} {postal_code}",
        "style": {"backgroundColor": "rgba(0,0,0,0.85)", "color": "white"}
    }
    layer = pdk.Layer(
        "ScatterplotLayer",
        data=latlon,
        get_position='[longitude, latitude]',
        get_radius=60,
        get_fill_color=[120, 180, 255, 170],
        pickable=True,
    )
    view = pdk.ViewState(
        latitude=float(latlon["latitude"].mean()),
        longitude=float(latlon["longitude"].mean()),
        zoom=10, pitch=0
    )
    st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=view, tooltip=tooltip))
else:
    st.info("No coordinates available for current filters.")

st.divider()

# ---- TABLE + DOWNLOAD ----
st.subheader("📋 Detailed Table")
tbl = df_f.sort_values("price", ascending=False)
st.dataframe(tbl, use_container_width=True, hide_index=True)

st.download_button(
    "⬇️ Download filtered CSV",
    data=tbl.to_csv(index=False).encode("utf-8"),
    file_name="listings_filtered.csv",
    mime="text/csv",
)
