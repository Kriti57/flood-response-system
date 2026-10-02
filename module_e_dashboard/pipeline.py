import json
from pathlib import Path


# Folder containing the mock outputs
DATA_DIR = Path(__file__).parent / "mock_data"


def load_json(filename):
    """Load a JSON file from the mock_data folder."""
    file_path = DATA_DIR / filename

    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def main():
    # 1. Flood Detection output
    flood_data = load_json("a_flood_output.json")

    # 2. Risk Scoring output
    risk_data = load_json("b_risk_output.json")

    # 3. Resource Allocation output
    allocation_data = load_json("c_allocation_output.json")

    # 4. Dynamic Routing output
    route_data = load_json("d_route_output.json")

    print("=" * 60)
    print("FLOOD RESPONSE SYSTEM - MOCK PIPELINE")
    print("Scenario: Trishuli / Nuwakot, Nepal")
    print("=" * 60)

    print("\n[1] FLOOD DETECTION")
    for zone in flood_data:
        print(
            f"{zone['zone_id']}: "
            f"Flood={zone['flood_pct'] * 100:.0f}% | "
            f"Confidence={zone['mask_confidence'] * 100:.0f}%"
        )

    print("\n[2] RISK SCORING")
    for zone in risk_data:
        print(
            f"{zone['zone_id']}: "
            f"Risk={zone['risk_score']:.2f} | "
            f"Population={zone['population_affected']} | "
            f"Priority={zone['priority_rank']}"
        )

    print("\n[3] RESOURCE ALLOCATION")
    for resource in allocation_data:
        print(
            f"{resource['resource_id']} -> "
            f"{resource['assigned_zone']}"
        )

    print("\n[4] DYNAMIC ROUTING")
    for route in route_data:
        print(
            f"{route['resource_id']}: "
            f"ETA={route['eta_minutes']} minutes | "
            f"Waypoints={len(route['route'])}"
        )

    print("\n" + "=" * 60)
    print("PIPELINE COMPLETED SUCCESSFULLY")
    print("=" * 60)


if __name__ == "__main__":
    main()