# app.py
import pandas as pd
import numpy as np
import plotly.express as px
import streamlit as st
from pathlib import Path

# ------------- Page & Theme -------------
st.set_page_config(
    page_title="Real Estate Intelligence — Maryland",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS (cards + subtle polish)
st.markdown(
    """
    <style>
      /* Base polish */
      .block-container {padding-top: 1.2rem; padding-bottom: 2rem;}
      [data-testid="stSidebar"] {border-right: 1px solid rgba(255,255,255,0.08);}
      .stMetric {gap:.25rem}
      .st-emotion-cache-ue6h4q {padding-top: 0 !important;} /* tighten headers */

      /* Card layout */
      .card {
        border-radius: 16px;
        padding: 18px 18px 14px 18px;
        background: linear-gradient(180deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.03) 100%);
        border: 1px solid rgba(255,255,255,0.08);
      }
      .card h3 {
        font-weight: 700;
        margin: 0 0 6px 0;
        font-size: 1rem;
        opacity: .85;
      }
      .kpi { display: flex; align-items: baseline; gap: .5rem; font-variant-numeric: tabular-nums; }
      .kpi .big { font-size: 1.6rem; font-weight: 800; }
      .pill {
        font-size: .75rem; padding: 2px 8px; border-radius: 999px;
        background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.08);
      }
      .section-title {
        font-weight: 800; font-size: 1.15rem; margin: 0 0 .35rem 0;
        display:flex; align-items:center; gap:.5rem;
      }
      .caption {opacity:.65; font-size:.9rem; margin-top:-.15rem;}
      .tight {margin-top: .2rem;}
    </style>
    """,
    unsafe_allow_html=True,
)

# ------------- Data load -------------
CSV = Path("clean_listings.csv")

@st.cache_data
def load_data(path: Path) -> pd.DataFrame:
    if not path.exists():
        st.error("`clean_listings.csv` not found. Run: `python clean.py` first.")
        st.stop()
    df = pd.read_csv(path)
    # Coerce numeric
    for c in ["price","beds","baths","sqft","price_per_sqft","latitude","longitude"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    # Clean types
    if "prop_type" in df.columns:
        df["prop_type"] = df["prop_type"].fillna("unknown").str.replace("_"," ").str.title()
    return df

df = load_data(CSV)

# ------------- Helpers -------------
def money(x):
    if pd.isna(x): return "—"
    return f"${x:,.0f}"

# ------------- Header -------------
cities_all = sorted(df["city"].dropna().unique().tolist())
left, right = st.columns([0.72, 0.28], vertical_alignment="center")
with left:
    st.markdown("## 🏠 Real Estate Intelligence — **Maryland**")
    st.caption("Automated pipeline → cleaning → **card-based** analytics dashboard")
with right:
    st.markdown(
        '<div class="card"><div class="kpi tight">'
        '<span class="pill">Live</span><span class="caption">Powered by Streamlit & Plotly</span>'
        "</div></div>",
        unsafe_allow_html=True,
    )

# ------------- Sidebar Filters -------------
with st.sidebar:
    st.markdown("### 🔎 Filters")
    # City multiselect (default all if available)
    if cities_all:
        city_sel = st.multiselect("City", options=cities_all, default=cities_all)
    else:
        city_sel = []

    # Price
    if df["price"].notna().any():
        pmin, pmax = int(df["price"].min()), int(df["price"].max())
    else:
        pmin, pmax = 0, 1_000_000
    price_range = st.slider("Price ($)", pmin, pmax, (pmin, pmax), step=10_000)

    # Beds / baths / sqft
    beds_min = st.number_input("Min Beds", min_value=0, step=1, value=0)
    baths_min = st.number_input("Min Baths", min_value=0, step=1, value=0)
    sqft_min = st.number_input("Min Sqft", min_value=0, step=100, value=0)

    st.markdown("---")
    sel_label = ", ".join(city_sel) if city_sel else "All"
    st.caption(f"Viewing: **{sel_label}**")
    st.caption("Tip: narrow price & min-sqft together to find value picks 📉")

# ------------- Filtering -------------
mask = pd.Series(True, index=df.index)
if city_sel:
    mask &= df["city"].isin(city_sel)
mask &= df["price"].between(*price_range)
mask &= (df["beds"].fillna(0) >= beds_min)
mask &= (df["baths"].fillna(0) >= baths_min)
mask &= (df["sqft"].fillna(0) >= sqft_min)

df_f = df[mask].copy()

# ------------- KPI Row (cards) -------------
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("<h3>Listings</h3>", unsafe_allow_html=True)
    st.markdown(f'<div class="kpi"><span class="big">{len(df_f):,}</span></div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with col2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("<h3>Avg Price</h3>", unsafe_allow_html=True)
    st.markdown(f'<div class="kpi"><span class="big">{money(df_f["price"].mean())}</span></div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with col3:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("<h3>Avg $/Sqft</h3>", unsafe_allow_html=True)
    st.markdown(f'<div class="kpi"><span class="big">{money(df_f["price_per_sqft"].mean())}</span></div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with col4:
    newest = pd.to_datetime(df_f["list_date"], errors="coerce").max() if "list_date" in df_f.columns else pd.NaT
    newest_fmt = newest.strftime("%Y-%m-%d") if pd.notna(newest) else "—"
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("<h3>Newest List</h3>", unsafe_allow_html=True)
    st.markdown(f'<div class="kpi"><span class="big">{newest_fmt}</span></div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("")

# ------------- Charts Row -------------
a, b = st.columns([0.62, 0.38])

with a:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">📈 Top 15 Listings by Price</div>', unsafe_allow_html=True)
    top = df_f.sort_values("price", ascending=False).head(15)
    if not top.empty:
        fig = px.bar(
            top, x="address", y="price", text="price", template="plotly_dark",
        )
        fig.update_traces(
            texttemplate="$%{text:,.0f}",
            textposition="outside",
            hovertemplate="%{x}<br>$%{y:,.0f}<extra></extra>",
        )
        fig.update_layout(
            xaxis_title=None, yaxis_title="Price ($)", showlegend=False,
            margin=dict(l=10,r=10,t=10,b=40), height=360
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data matches your filters.")
    st.markdown("</div>", unsafe_allow_html=True)

with b:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">🏷️ Property Type Mix</div>', unsafe_allow_html=True)
    if "prop_type" in df_f.columns and not df_f.empty:
        # ---- FIX: compatible with all pandas versions
        vc = df_f["prop_type"].value_counts(dropna=False)
        mix = vc.reset_index()
        mix.columns = ["prop_type", "count"]
        fig2 = px.pie(mix, values="count", names="prop_type", hole=0.55, template="plotly_dark")
        fig2.update_traces(
            textposition="inside", textinfo="percent+label",
            hovertemplate="%{label}: %{value} listings<extra></extra>"
        )
        fig2.update_layout(height=360, margin=dict(l=4,r=4,t=4,b=4))
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("No property type data.")
    st.markdown("</div>", unsafe_allow_html=True)

# ------------- Scatter (Price vs Sqft) -------------
st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown('<div class="section-title">📊 Price vs. Square Footage</div>', unsafe_allow_html=True)
scat = df_f.dropna(subset=["price","sqft"])

# Robust trendline: only if statsmodels is available
trendline_mode = None
try:
    import statsmodels.api as sm  # noqa: F401
    trendline_mode = "ols"
except Exception:
    trendline_mode = None

if not scat.empty:
    fig3 = px.scatter(
        scat, x="sqft", y="price",
        color="prop_type" if "prop_type" in scat.columns else None,
        hover_data=["address","beds","baths","city"] if set(["address","beds","baths","city"]).issubset(scat.columns) else None,
        trendline=trendline_mode,
        template="plotly_dark",
    )
    fig3.update_layout(
        xaxis_title="Sqft", yaxis_title="Price ($)", height=420,
        margin=dict(l=10,r=10,t=10,b=10), legend_title=None
    )
    st.plotly_chart(fig3, use_container_width=True)
else:
    st.info("Not enough data for scatter.")
st.markdown("</div>", unsafe_allow_html=True)

# ------------- Map -------------
if {"latitude","longitude"}.issubset(df_f.columns):
    mdf = df_f.dropna(subset=["latitude","longitude"]).rename(columns={"latitude":"lat","longitude":"lon"})
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">🗺️ Property Map</div>', unsafe_allow_html=True)
    if not mdf.empty:
        st.map(mdf[["lat","lon"]], use_container_width=True)
    else:
        st.caption("No coordinates available for the current filter range.")
    st.markdown("</div>", unsafe_allow_html=True)

# ------------- Data Table + Download -------------
st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown('<div class="section-title">📋 Detailed Results</div>', unsafe_allow_html=True)
if not df_f.empty:
    show_cols = [c for c in ["property_id","price","beds","baths","sqft","price_per_sqft",
                             "address","city","state","postal_code","prop_type","list_date"]
                 if c in df_f.columns]
    st.dataframe(df_f[show_cols].sort_values("price", ascending=False), use_container_width=True, height=380)
    st.download_button(
        label="⬇️ Download current view (CSV)",
        data=df_f[show_cols].to_csv(index=False).encode("utf-8"),
        file_name="listings_filtered.csv",
        mime="text/csv",
    )
else:
    st.info("No rows to display.")
st.markdown("</div>", unsafe_allow_html=True)
