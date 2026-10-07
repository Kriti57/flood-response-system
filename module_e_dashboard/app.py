import json
from pathlib import Path

import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium


# --------------------------------------------------
# Configuration
# --------------------------------------------------

DATA_DIR = Path(__file__).parent / "mock_data"
REAL_ALLOCATION_PATH = Path(__file__).parent.parent / "module_c_allocation" / "allocation_output.json"
REAL_RISK_PATH = Path(__file__).parent.parent / "module_b_risk_scoring" / "sample_output" / "risk_output.json"
REAL_ROUTE_PATH = Path(__file__).parent.parent / "module_d_routing" / "route_output.json"
REAL_FLOOD_PATH = Path(__file__).parent.parent / "module_a_flood_detection" / "outputs" / "sample_output_DEMO_sen1floods11_chip.json.json"

MAP_CENTER = [27.9226, 85.1490]


# --------------------------------------------------
# Helper functions
# --------------------------------------------------

def load_json(filename):
    file_path = DATA_DIR / filename
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def load_real_allocation():
    with open(REAL_ALLOCATION_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


def load_real_risk():
    with open(REAL_RISK_PATH, "r", encoding="utf-8") as file:
        return json.load(file)

def load_real_routes():
    with open(REAL_ROUTE_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


def load_real_flood():
    with open(REAL_FLOOD_PATH, "r", encoding="utf-8") as file:
        return json.load(file)

def risk_color(score):
    if score >= 0.7:
        return "🔴"
    elif score >= 0.4:
        return "🟠"
    else:
        return "🟢"


def marker_style(resource_id):
    if resource_id.startswith("RescueTeam"):
        return {"color": "red", "icon": "user-shield"}
    elif resource_id.startswith("Ambulance"):
        return {"color": "blue", "icon": "plus"}
    elif resource_id.startswith("Boat"):
        return {"color": "darkgreen", "icon": "ship"}
    else:
        return {"color": "gray", "icon": "question"}


# --------------------------------------------------
# Load pipeline outputs
# --------------------------------------------------

flood_data = load_real_flood()
risk_data = load_real_risk()
allocation_data = load_real_allocation()
route_data = load_real_routes()


# --------------------------------------------------
# Page configuration + custom styling
# --------------------------------------------------

st.set_page_config(
    page_title="Flood Response System",
    page_icon="🌊",
    layout="wide"
)

st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 0;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #9ca3af;
        margin-top: 0;
    }
    div[data-testid="stMetric"] {
        background-color: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 10px;
        padding: 14px 18px;
    }
    div[data-testid="stDataFrame"] {
        border-radius: 8px;
        overflow: hidden;
    }
</style>
""", unsafe_allow_html=True)


# --------------------------------------------------
# Header
# --------------------------------------------------

st.markdown('<p class="main-header">🌊 Flood Response System</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Trishuli / Nuwakot, Nepal — Emergency Response Dashboard</p>', unsafe_allow_html=True)

st.info(
    "📍 Simulated flood-response scenario inspired by the August 2026 Bhote Koshi-Trishuli flood event.",
    icon="ℹ️"
)


# --------------------------------------------------
# Convert data to DataFrames
# --------------------------------------------------

flood_df = pd.DataFrame(flood_data)
risk_df = pd.DataFrame(risk_data)
allocation_df = pd.DataFrame(allocation_data)


# --------------------------------------------------
# Key metrics
# --------------------------------------------------

total_population = risk_df["population_affected"].sum()
highest_risk = risk_df["risk_score"].max()
highest_risk_zone = risk_df.loc[risk_df["risk_score"].idxmax(), "zone_id"]
resources = len(allocation_df)

col1, col2, col3, col4 = st.columns(4)
col1.metric("🗺️ Zones Monitored", len(flood_df))
col2.metric("👥 Population Affected", f"{total_population:,}")
col3.metric("⚠️ Highest Risk Zone", f"{highest_risk_zone} ({highest_risk:.2f})")
col4.metric("🚨 Resources Deployed", resources)


# --------------------------------------------------
# Flood + Risk tables
# --------------------------------------------------

st.divider()

left, right = st.columns(2)

with left:
    st.subheader("🌊 Flood Detection")
    st.caption("Source: U-Net (ResNet34), Sentinel-1 SAR — IoU 0.59, F1 0.742")

    flood_display = flood_df.copy()
    flood_display["flood_pct"] = (flood_display["flood_pct"] * 100).round(1)
    flood_display["mask_confidence"] = (flood_display["mask_confidence"] * 100).round(1)
    flood_display.columns = ["Zone", "Flood %", "Confidence %"]

    st.dataframe(flood_display, width="stretch", hide_index=True)

with right:
    st.subheader("⚠️ Risk Assessment")
    st.caption("Risk = weighted(flood %, population, road access, rainfall)")

    risk_display = risk_df[
        ["zone_id", "risk_score", "population_affected", "road_accessibility", "priority_rank"]
    ].copy()
    risk_display["risk_level"] = risk_display["risk_score"].apply(risk_color)
    risk_display = risk_display[["risk_level", "zone_id", "risk_score", "population_affected", "road_accessibility", "priority_rank"]]
    risk_display.columns = ["", "Zone", "Risk Score", "Population", "Road Access", "Priority"]

    st.dataframe(risk_display, width="stretch", hide_index=True)


# --------------------------------------------------
# Allocation comparison
# --------------------------------------------------

st.divider()
st.subheader("📊 Optimized vs Baseline Allocation")

col_a, col_b, col_c = st.columns(3)
col_a.metric("Baseline (Greedy)", "86.51")
col_b.metric("Optimized (ILP)", "92.02", delta="+6.4%")
col_c.metric("Zones Covered", "3 of 9", help="Zones that received at least one resource")

st.caption(
    "Score = sum of (risk_score x people_covered) across all zones. Optimized allocation "
    "beats naive greedy baseline by matching resource type to zone conditions "
    "(e.g. boats sent to low-road-access zones). *Figures from Day 2 test data — "
    "see module_c_allocation/results.md for current status.*"
)


# --------------------------------------------------
# Resource allocation
# --------------------------------------------------

st.divider()
st.subheader("🚑 Resource Allocation")

alloc_tab1, alloc_tab2 = st.tabs(["Table", "By Type"])

with alloc_tab1:
    allocation_display = allocation_df[["resource_id", "assigned_zone"]].copy()
    allocation_display.columns = ["Resource", "Assigned Zone"]
    st.dataframe(allocation_display, width="stretch", hide_index=True)

with alloc_tab2:
    type_counts = allocation_df["resource_id"].apply(
        lambda r: "Rescue Team" if r.startswith("RescueTeam")
        else "Ambulance" if r.startswith("Ambulance")
        else "Boat" if r.startswith("Boat") else "Other"
    ).value_counts()
    st.bar_chart(type_counts)


# --------------------------------------------------
# Map
# --------------------------------------------------

st.divider()
st.subheader("🗺️ Response Map")
st.caption("🔴 Rescue Teams &nbsp;&nbsp; 🔵 Ambulances &nbsp;&nbsp; 🟢 Boats", unsafe_allow_html=True)

m = folium.Map(location=MAP_CENTER, zoom_start=12, tiles="OpenStreetMap")

for resource in allocation_data:
    lat = resource["base_lat"]
    lng = resource["base_lng"]
    style = marker_style(resource["resource_id"])

    folium.Marker(
        location=[lat, lng],
        popup=f"<b>{resource['resource_id']}</b><br>Assigned Zone: {resource['assigned_zone']}",
        tooltip=resource["resource_id"],
        icon=folium.Icon(icon=style["icon"], prefix="fa", color=style["color"])
    ).add_to(m)

for route_data_item in route_data:
    route = route_data_item["route"]
    folium.PolyLine(
        locations=route,
        popup=f"{route_data_item['resource_id']} - ETA: {route_data_item['eta_minutes']} min",
        weight=4,
        color="#4a90d9",
        opacity=0.8
    ).add_to(m)

m.fit_bounds([[27.90, 85.14], [27.95, 85.16]])

st_folium(m, width=None, height=600)


# --------------------------------------------------
# Routing information
# --------------------------------------------------

st.divider()
st.subheader("🚨 Dynamic Routing")

route_display = pd.DataFrame(route_data)
route_display = route_display[["resource_id", "eta_minutes"]]
route_display.columns = ["Resource", "ETA (minutes)"]

st.dataframe(route_display, width="stretch", hide_index=True)


# --------------------------------------------------
# Footer
# --------------------------------------------------

st.divider()
st.caption(
    "✅ All four pipeline stages now use real data: Flood Detection (Sen1Floods11 demo chip, "
    "not Nepal imagery), Risk Scoring, Resource Allocation, and Dynamic Routing."
)