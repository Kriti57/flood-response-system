import json
from pathlib import Path

DATA_DIR = Path(__file__).parent / "mock_data"
REAL_ALLOCATION_PATH = Path(__file__).parent.parent / "module_c_allocation" / "allocation_output.json"
REAL_RISK_PATH = Path(__file__).parent.parent / "module_b_risk_scoring" / "sample_output" / "risk_output.json"
REAL_ROUTE_PATH = Path(__file__).parent.parent / "module_d_routing" / "route_output.json"

def load_json(filename):
    """Load a JSON file from the mock_data folder."""
    file_path = DATA_DIR / filename
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def load_real_allocation():
    """Load Person C's real allocation output."""
    with open(REAL_ALLOCATION_PATH, "r", encoding="utf-8") as file:
        return json.load(file)

def load_real_risk():
    with open(REAL_RISK_PATH, "r", encoding="utf-8") as file:
        return json.load(file)

def load_real_routes():
    with open(REAL_ROUTE_PATH, "r", encoding="utf-8") as file:
        return json.load(file)

def run_pipeline():
    """Returns all four stages as a dict. Used by app.py (Streamlit dashboard)."""
    return {
        "flood": load_json("a_flood_output.json"),          # TODO: Person A real output
        "risk": load_real_risk(),                             # Person B real output (merged)
        "allocation": load_real_allocation(),                # Person C real output (merged)
        "routes": load_real_routes(),                         # Person D real output (merged)
    }


def main():
    data = run_pipeline()

    print("=" * 60)
    print("FLOOD RESPONSE SYSTEM - PIPELINE")
    print("Scenario: Trishuli / Nuwakot, Nepal")
    print("=" * 60)

    print("\n[1] FLOOD DETECTION (mock)")
    for zone in data["flood"]:
        print(f"{zone['zone_id']}: Flood={zone['flood_pct']*100:.0f}% | Confidence={zone['mask_confidence']*100:.0f}%")

    print("\n[2] RISK SCORING (REAL - Person B)")
    for zone in data["risk"]:
        print(f"{zone['zone_id']}: Risk={zone['risk_score']:.2f} | Population={zone['population_affected']} | Priority={zone['priority_rank']}")

    print("\n[3] RESOURCE ALLOCATION (REAL - Person C)")
    for resource in data["allocation"]:
        print(f"{resource['resource_id']} -> {resource['assigned_zone']}")

    print("\n[4] DYNAMIC ROUTING (REAL - Person D)")
    for route in data["routes"]:
        print(f"{route['resource_id']}: ETA={route['eta_minutes']} minutes | Waypoints={len(route['route'])}")

    print("\n" + "=" * 60)
    print("PIPELINE COMPLETED SUCCESSFULLY")
    print("=" * 60)


if __name__ == "__main__":
    main()