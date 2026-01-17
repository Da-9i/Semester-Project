
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import calendar

st.set_page_config(
    page_title="Thermal Comfort & Climate Trends – Islamabad",
    layout="wide"
)

st.title("🌡️ Thermal Comfort, Heat Stress & Climate Trends in Islamabad (2000–2025)")

# ---------- Load Data ----------
DATA_PATH = Path(__file__).parent / "era5_land_daily_temp_2000_2025.csv"
df = pd.read_csv(DATA_PATH)

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

# Date handling
df["date"] = pd.to_datetime(df["date"])
df["year"] = df["date"].dt.year
df["month"] = df["date"].dt.month

# ---------- Derived Climate Indicators ----------
comfortable = df[(df["temp_c"] >= 18) & (df["temp_c"] <= 25)]
hot_days = df[df["temp_c"] > 35]

# ---------- Yearly Aggregates ----------
yearly_stats = (
    df.groupby("year")
    .agg(
        avg_temp_c=("temp_c", "mean"),
        temp_std=("temp_c", "std")
    )
    .reset_index()
)

yearly_comfort = (
    comfortable.groupby("year")
    .size()
    .reset_index(name="comfortable_days")
)

yearly_hot = (
    hot_days.groupby("year")
    .size()
    .reset_index(name="hot_days")
)

# Merge all yearly indicators
yearly = (
    yearly_stats
    .merge(yearly_comfort, on="year", how="left")
    .merge(yearly_hot, on="year", how="left")
)

yearly.fillna(0, inplace=True)
yearly["avg_temp_c"] = yearly["avg_temp_c"].round(2)
yearly["comfort_ratio"] = (yearly["comfortable_days"] / 365 * 100).round(1)

# ---------- SECTION 1: Long-term Climate Trends ----------
st.subheader("📈 Long-term Climate Trends")

fig_trends = go.Figure()

fig_trends.add_trace(go.Scatter(
    x=yearly["year"],
    y=yearly["avg_temp_c"],
    mode="lines+markers",
    name="Avg Temperature (°C)"
))

fig_trends.add_trace(go.Scatter(
    x=yearly["year"],
    y=yearly["comfortable_days"],
    mode="lines+markers",
    name="Comfortable Days",
    yaxis="y2"
))

fig_trends.update_layout(
    template="plotly_white",
    yaxis=dict(title="Avg Temperature (°C)"),
    yaxis2=dict(
        title="Comfortable Days",
        overlaying="y",
        side="right"
    ),
    legend=dict(x=0.01, y=0.99)
)

st.plotly_chart(fig_trends, use_container_width=True)

# ---------- SECTION 2: Comfort vs Warming Relationship ----------
st.subheader("🔁 Relationship Between Warming & Thermal Comfort")

fig_scatter = px.scatter(
    yearly,
    x="avg_temp_c",
    y="comfortable_days",
    trendline="ols",
    labels={
        "avg_temp_c": "Average Temperature (°C)",
        "comfortable_days": "Comfortable Days per Year"
    },
    template="plotly_white"
)

st.plotly_chart(fig_scatter, use_container_width=True)

# ---------- SECTION 3: Heat Stress Expansion ----------
st.subheader("🔥 Expansion of Extreme Heat Days")

fig_hot = px.bar(
    yearly,
    x="year",
    y="hot_days",
    labels={"hot_days": "Days > 35°C"},
    template="plotly_white"
)

st.plotly_chart(fig_hot, use_container_width=True)

# ---------- SECTION 4: Monthly Comfort Heatmap ----------
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

st.subheader("🗓️ Seasonal Distribution of Comfortable Days")

fig_heatmap = px.imshow(
    heatmap_data,
    aspect="auto",
    labels=dict(x="Month", y="Year", color="Comfortable Days"),
    template="plotly_white"
)

st.plotly_chart(fig_heatmap, use_container_width=True)

# ---------- SECTION 5: Strategic Summary Table ----------
monthly_counts = (
    comfortable.groupby(["year", "month"])
    .size()
    .reset_index(name="monthly_days")
)

idx = monthly_counts.groupby("year")["monthly_days"].idxmax()
top_months = monthly_counts.loc[idx]
top_months["month_name"] = top_months["month"].apply(lambda x: calendar.month_name[x])

summary_table = (
    yearly.merge(
        top_months[["year", "month_name", "monthly_days"]],
        on="year",
        how="left"
    )
)

st.subheader("📊 Strategic Yearly Summary")

fig_table = go.Figure(data=[go.Table(
    header=dict(
        values=[
            "Year",
            "Avg Temp (°C)",
            "Comfortable Days",
            "Comfort % of Year",
            "Hot Days (>35°C)",
            "Top Comfort Month",
            "Days in Top Month"
        ],
        fill_color="#1f2937",
        font=dict(color="white"),
        align="center"
    ),
    cells=dict(
        values=[
            summary_table["year"],
            summary_table["avg_temp_c"],
            summary_table["comfortable_days"],
            summary_table["comfort_ratio"],
            summary_table["hot_days"],
            summary_table["month_name"],
            summary_table["monthly_days"]
        ],
        align="center"
    )
)])

st.plotly_chart(fig_table, use_container_width=True)
