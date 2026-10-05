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


# --------------------------------------------------
# Load pipeline outputs
# --------------------------------------------------

flood_data = load_json("a_flood_output.json")
risk_data = load_json("b_risk_output.json")
allocation_data = load_real_allocation()
route_data = load_json("d_route_output.json")


# --------------------------------------------------
# Page configuration
# --------------------------------------------------

st.set_page_config(
    page_title="Flood Response System",
    page_icon="🌊",
    layout="wide"
)


# --------------------------------------------------
# Header
# --------------------------------------------------

st.title("🌊 Flood Response System")
st.subheader("Trishuli / Nuwakot, Nepal")

st.info(
    "Simulated flood-response scenario inspired by the "
    "August 2026 Bhote Koshi–Trishuli flood event."
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
highest_flood = flood_df["flood_pct"].max()
resources = len(allocation_df)

col1, col2, col3, col4 = st.columns(4)

col1.metric("Zones Monitored", len(flood_df))
col2.metric("Population Affected", f"{total_population:,}")
col3.metric("Highest Risk Score", f"{highest_risk:.2f}")
col4.metric("Resources Deployed", resources)


# --------------------------------------------------
# Flood + Risk tables
# --------------------------------------------------

st.divider()

left, right = st.columns(2)

with left:
    st.subheader("🌊 Flood Detection")

    flood_display = flood_df.copy()
    flood_display["flood_pct"] = (flood_display["flood_pct"] * 100).round(1)
    flood_display["mask_confidence"] = (flood_display["mask_confidence"] * 100).round(1)
    flood_display.columns = ["Zone", "Flood %", "Confidence %"]

    st.dataframe(flood_display, width="stretch", hide_index=True)


with right:
    st.subheader("⚠️ Risk Assessment")

    risk_display = risk_df[
        ["zone_id", "risk_score", "population_affected", "road_accessibility", "priority_rank"]
    ].copy()
    risk_display.columns = ["Zone", "Risk Score", "Population", "Road Access", "Priority"]

    st.dataframe(risk_display, width="stretch", hide_index=True)


# --------------------------------------------------
# Resource allocation
# --------------------------------------------------

st.divider()
st.subheader("🚑 Resource Allocation")

allocation_display = allocation_df[["resource_id", "assigned_zone"]].copy()
allocation_display.columns = ["Resource", "Assigned Zone"]

st.dataframe(allocation_display, width="stretch", hide_index=True)


# --------------------------------------------------
# Map
# --------------------------------------------------

st.divider()
st.subheader("🗺️ Response Map")

m = folium.Map(location=MAP_CENTER, zoom_start=12)

for resource in allocation_data:
    lat = resource["base_lat"]
    lng = resource["base_lng"]

    folium.Marker(
        location=[lat, lng],
        popup=f"<b>{resource['resource_id']}</b><br>Assigned Zone: {resource['assigned_zone']}",
        tooltip=resource["resource_id"],
        icon=folium.Icon(icon="plus", prefix="fa")
    ).add_to(m)

for route_data_item in route_data:
    route = route_data_item["route"]

    folium.PolyLine(
        locations=route,
        popup=f"{route_data_item['resource_id']} - ETA: {route_data_item['eta_minutes']} min",
        weight=5
    ).add_to(m)

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
st.caption("Resource allocation is real (Person C, merged). Flood, risk, and routing data are still simulated.")