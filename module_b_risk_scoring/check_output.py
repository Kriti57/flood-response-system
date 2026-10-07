import json

REQUIRED = {"zone_id", "risk_score", "population_affected", "road_accessibility", "priority_rank"}
data = json.load(open("sample_output/risk_output.json"))

assert len(data) == 9, f"expected 9 zones, got {len(data)}"
for row in data:
    assert set(row) == REQUIRED, f"wrong fields in {row}"
    assert 0 <= row["risk_score"] <= 1, f"risk_score out of range: {row}"
    assert 0 <= row["road_accessibility"] <= 1, f"road_accessibility out of range: {row}"
assert sorted(r["priority_rank"] for r in data) == list(range(1, 10)), "ranks must be 1..9"
print("OK: risk_output.json matches the schema")