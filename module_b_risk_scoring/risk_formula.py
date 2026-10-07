import os
import json
import pandas as pd
from weather import get_rainfall_mm, rainfall_to_adjustment

POP_PATH = "data/population_per_zone.json"    # from population_overlay.py
FLOOD_PATH = "data/flood_input.json"          # Ishita's output
ROAD_PATH = "data/road_input.json"            # Priya's output
OUT_PATH = "sample_output/risk_output.json"

# Formula weights (tunable parameters, state this in your demo)
W_FLOOD, W_POP, W_ROAD, W_RAIN = 0.4, 0.3, 0.2, 0.1

# DUMMY flood data, used only if data/flood_input.json doesn't exist
DUMMY_FLOOD = [
    {"zone_id": "Z1", "flood_pct": 0.10, "mask_confidence": 0.90},
    {"zone_id": "Z2", "flood_pct": 0.35, "mask_confidence": 0.88},
    {"zone_id": "Z3", "flood_pct": 0.05, "mask_confidence": 0.92},
    {"zone_id": "Z4", "flood_pct": 0.62, "mask_confidence": 0.88},
    {"zone_id": "Z5", "flood_pct": 0.80, "mask_confidence": 0.85},
    {"zone_id": "Z6", "flood_pct": 0.45, "mask_confidence": 0.90},
    {"zone_id": "Z7", "flood_pct": 0.20, "mask_confidence": 0.91},
    {"zone_id": "Z8", "flood_pct": 0.55, "mask_confidence": 0.87},
    {"zone_id": "Z9", "flood_pct": 0.00, "mask_confidence": 0.93},
]


def load_json(path):
    with open(path) as f:
        data = json.load(f)
    if isinstance(data, dict):          # unwrap {"zones": [...]} style files
        data = next(iter(data.values()))
    return data


def main():
    # --- inputs ---
    pop = pd.DataFrame(load_json(POP_PATH))

    if os.path.exists(FLOOD_PATH):
        flood = pd.DataFrame(load_json(FLOOD_PATH))
        print("Using REAL flood data from Person A")
    else:
        flood = pd.DataFrame(DUMMY_FLOOD)
        print("Using DUMMY flood data")

    # join flood + population (df is created HERE)
    df = flood.merge(pop, on="zone_id", how="left")

    # safety checks on the flood input (must come after df exists)
    if not df["flood_pct"].between(0, 1).all():
        print("WARNING: flood_pct has values outside 0-1. Check Person A's file!")
    missing_flood = set(pop["zone_id"]) - set(flood["zone_id"])
    if missing_flood:
        print(f"WARNING: no flood data for zones: {sorted(missing_flood)}")
    if df["total_population"].isna().any():
        print("WARNING: some zone_ids have no population. Check zone IDs match!")
    df["total_population"] = df["total_population"].fillna(0)

    # road accessibility: dummy 0.5 until the real file exists
    if os.path.exists(ROAD_PATH):
        road = pd.DataFrame(load_json(ROAD_PATH))[["zone_id", "road_accessibility"]]
        df = df.merge(road, on="zone_id", how="left")
        missing_road = set(pop["zone_id"]) - set(road["zone_id"])
        if missing_road:
            print(f"WARNING: no road data for zones: {sorted(missing_road)} (using 0.5)")
        df["road_accessibility"] = df["road_accessibility"].fillna(0.5)
        if not df["road_accessibility"].between(0, 1).all():
            print("WARNING: road_accessibility has values outside 0-1. Check Priya's file!")
        print("Using REAL road accessibility from Person D")
    else:
        df["road_accessibility"] = 0.5
        print("Using DUMMY road accessibility (0.5)")

    # rainfall: one value for the whole region
    mm = get_rainfall_mm()
    rain_adj = rainfall_to_adjustment(mm)
    print(f"Rainfall next 24h: {mm} mm -> adjustment {rain_adj}")

    # --- formula ---
    df["population_affected"] = (df["flood_pct"] * df["total_population"]).round().astype(int)
    max_aff = df["population_affected"].max()
    df["norm_pop"] = df["population_affected"] / max_aff if max_aff > 0 else 0.0

    df["risk_score"] = (
        W_FLOOD * df["flood_pct"]
        + W_POP * df["norm_pop"]
        + W_ROAD * (1 - df["road_accessibility"])
        + W_RAIN * rain_adj
    ).clip(0, 1).round(2)

    df["priority_rank"] = df["risk_score"].rank(ascending=False, method="first").astype(int)
    df = df.sort_values("priority_rank")

    # --- output in the agreed schema ---
    cols = ["zone_id", "risk_score", "population_affected",
            "road_accessibility", "priority_rank"]
    os.makedirs("sample_output", exist_ok=True)
    df[cols].to_json(OUT_PATH, orient="records", indent=2)

    print()
    print(df[cols].to_string(index=False))
    print(f"\nSaved {OUT_PATH}")


if __name__ == "__main__":
    main()

