import json
import os

MOCK_DIR = os.path.join(os.path.dirname(__file__), "mock_data")

def load_json(filename):
    path = os.path.join(MOCK_DIR, filename)
    with open(path, "r") as f:
        return json.load(f)

def run_pipeline():
    """
    Reads each stage's output in sequence. Right now everything is mocked.
    As teammates finish their real modules, replace the load_json() call for
    that stage with a call to their actual script/function instead.
    """
    flood_data = load_json("a_flood_output.json")             # TODO: replace with Person A's real output
    risk_data = load_json("b_risk_output.json")                # TODO: replace with Person B's real output
    allocation_data = load_json("c_allocation_output.json")    # TODO: replace with Person C's real output
    route_data = load_json("d_route_output.json")               # TODO: replace with Person D's real output

    return {
        "flood": flood_data,
        "risk": risk_data,
        "allocation": allocation_data,
        "routes": route_data,
    }

if __name__ == "__main__":
    result = run_pipeline()
    print(json.dumps(result, indent=2))