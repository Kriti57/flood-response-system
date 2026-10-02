import streamlit as st
from pipeline import run_pipeline

st.title("Flood Response Dashboard (Mock Data - Day 1)")

data = run_pipeline()

st.subheader("Flood Status per Zone")
st.table(data["flood"])

st.subheader("Risk Scores per Zone")
st.table(data["risk"])

st.subheader("Resource Allocation")
st.table(data["allocation"])

st.subheader("Routes & ETA")
st.table([{"resource_id": r["resource_id"], "eta_minutes": r["eta_minutes"]} for r in data["routes"]])