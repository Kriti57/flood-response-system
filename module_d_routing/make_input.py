import json
from pathlib import Path

root = Path(__file__).parent.parent

alloc = json.loads((root / "module_c_allocation" / "allocation_output.json").read_text(encoding="utf-8"))
sample = json.loads((Path(__file__).parent / "sample_input.json").read_text(encoding="utf-8"))
flood = json.loads((root / "module_a_flood_detection" / "outputs" /
                    "sample_output_DEMO_sen1floods11_chip.json.json").read_text(encoding="utf-8"))

# Skip unassigned resources (assigned_zone is null)
assignments = [a for a in alloc if a["assigned_zone"] is not None]

data = {
    "assignments": assignments,
    "zone_destinations": sample["zone_destinations"],
    "flood_data": [{"zone_id": z["zone_id"], "flood_pct": z["flood_pct"]} for z in flood],
    "zone_edges": {},
    "blocked_edges": [],
}

out = Path(__file__).parent / "real_input.json"
out.write_text(json.dumps(data, indent=2), encoding="utf-8")
print(f"Wrote {out.name}: {len(assignments)} assignments")
from collections import Counter
print(Counter(a["assigned_zone"] for a in assignments))