import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import calendar

st.set_page_config(
    page_title="Comfortable Temperature Days – Islamabad",
    layout="wide"
)

st.title("🌤️ Comfortable Temperature Days in Islamabad (2000–2025)")

# ---------- Load Data ----------
DATA_PATH = Path(__file__).parent / "era5_land_daily_temp_2000_2025.csv"
df = pd.read_csv(DATA_PATH)

# Ensure correct column names
df.columns = df.columns.str.strip().str.lower()

# Rename temperature column if needed
if "temp_c" not in df.columns:
    for col in df.columns:
        if "temp" in col:
            df.rename(columns={col: "temp_c"}, inplace=True)
            break

# Add Islamabad coordinates
df["lat"] = 33.6844
df["lon"] = 73.0479

comfortable = df.loc[
    (df["temp_c"] >= 18) & (df["temp_c"] <= 25)
].copy()


df["date"] = pd.to_datetime(df["date"])
df["year"] = df["date"].dt.year
df["month"] = df["date"].dt.month

# ---------- Comfortable Temperature Filter ----------
comfortable = df[(df["temp_c"] >= 18) & (df["temp_c"] <= 25)]

# ---------- Yearly Comfortable Days ----------
yearly_comfort = (
    comfortable.groupby("year")
    .size()
    .reset_index(name="comfortable_days")
)

st.subheader("📊 Yearly Comfortable Temperature Days")

fig_bar = px.bar(
    yearly_comfort,
    x="year",
    y="comfortable_days",
    labels={"year": "Year", "comfortable_days": "Comfortable Days"},
    template="plotly_white"
)
st.plotly_chart(fig_bar, use_container_width=True)

fig_line = px.line(
    yearly_comfort,
    x="year",
    y="comfortable_days",
    markers=True,
    template="plotly_white"
)
st.plotly_chart(fig_line, use_container_width=True)

# ---------- Monthly Heatmap ----------
monthly_comfort = (
    comfortable.groupby(["year", "month"])
    .size()
    .reset_index(name="count")
)

heatmap_data = monthly_comfort.pivot(
    index="year",
    columns="month",
    values="count"
).fillna(0)

st.subheader("🔥 Monthly Distribution Heatmap")

fig_heatmap = px.imshow(
    heatmap_data,
    aspect="auto",
    labels=dict(x="Month", y="Year", color="Comfortable Days"),
    template="plotly_white"
)
st.plotly_chart(fig_heatmap, use_container_width=True)

# ---------- Summary Table ----------
yearly_total = (
    comfortable.groupby("year")
    .size()
    .reset_index(name="total_comfortable_days")
)

monthly_counts = (
    comfortable.groupby(["year", "month"])
    .size()
    .reset_index(name="monthly_days")
)

idx = monthly_counts.groupby("year")["monthly_days"].idxmax()
top_months = monthly_counts.loc[idx]
top_months["month_name"] = top_months["month"].apply(lambda x: calendar.month_name[x])

summary_table = yearly_total.merge(
    top_months[["year", "month_name", "monthly_days"]],
    on="year"
)

st.subheader("📋 Yearly Summary Table")

fig_table = go.Figure(data=[go.Table(
    header=dict(
        values=["Year", "Total Comfortable Days", "Top Comfortable Month", "Days in Top Month"],
        fill_color="#1f2937",
        font=dict(color="white"),
        align="center"
    ),
    cells=dict(
        values=[
            summary_table["year"],
            summary_table["total_comfortable_days"],
            summary_table["month_name"],
            summary_table["monthly_days"]
        ],
        align="center"
    )
)])

st.plotly_chart(fig_table, use_container_width=True)



yearly_comfort_map = (
    comfortable
    .groupby("year", as_index=False)
    .agg(
        lat=("lat", "first"),
        lon=("lon", "first"),
        comfortable_days=("year", "count")
    )
)


st.subheader("🗺️ Spatial View (Islamabad)")

st.sidebar.subheader("🗺️ Map Controls")

map_year = st.sidebar.slider(
    "Select year for map",
    int(yearly_comfort_map["year"].min()),
    int(yearly_comfort_map["year"].max()),
    int(yearly_comfort_map["year"].max())
)

map_data = yearly_comfort_map[
    yearly_comfort_map["year"] == map_year
]

fig_map = px.scatter_mapbox(
    map_data,
    lat="lat",
    lon="lon",
    size="comfortable_days",
    color="comfortable_days",
    zoom=6,
    size_max=40,
    mapbox_style="carto-positron",
    title=f"Comfortable Temperature Days in Islamabad – {map_year}",
    hover_data={"comfortable_days": True}
)

st.plotly_chart(fig_map, use_container_width=True)


st.subheader("🗺️ Spatial Distribution of Comfortable Days")

st.sidebar.subheader("Map Controls")
map_year = st.sidebar.slider(
    "Select year for map",
    int(yearly_comfort_map["year"].min()),
    int(yearly_comfort_map["year"].max()),
    int(yearly_comfort_map["year"].max()),
    key="map_year_slider"   # ✅ UNIQUE KEY
)





