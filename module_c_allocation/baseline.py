"""BASELINE: naive greedy allocation.

Rule: take zones from highest to lowest risk; for each, hand out still-available
eligible resources in fleet-list order until the zone's need is covered.
It does NOT match resource type to zone conditions and never looks ahead - which
is exactly what the optimized ILP (allocate.py) improves on.

Run:  python module_c_allocation/baseline.py [--risk FILE] [--resources FILE] [--out FILE]
"""
import argparse
from allocation_common import (HERE, UNASSIGNED, effectiveness, evaluate, load_resources,
                               load_zones, print_report, save_json, to_schema_output, zone_need)


def run_baseline(zones, resources):
    assignment = {r["resource_id"]: UNASSIGNED for r in resources}
    available = list(resources)
    for z in sorted(zones, key=lambda z: (-z["risk_score"], z["priority_rank"])):
        need, covered = zone_need(z), 0.0
        for r in list(available):
            if covered >= need:
                break
            e = effectiveness(r["type"], z["road_accessibility"])
            if e <= 0:                      # physically unusable here (e.g. boat on dry roads)
                continue
            assignment[r["resource_id"]] = z["zone_id"]
            covered += e * r["capacity_people"]
            available.remove(r)
    return assignment


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--risk", default=None, help="risk JSON (schema 2); default dummy_risk.json")
    ap.add_argument("--resources", default=None, help="resources JSON; default resources.json")
    ap.add_argument("--out", default=str(HERE / "baseline_output.json"))
    args = ap.parse_args()
    zones, resources = load_zones(args.risk), load_resources(args.resources)
    assignment = run_baseline(zones, resources)
    print_report("BASELINE (greedy)", evaluate(assignment, zones, resources))
    save_json(to_schema_output(assignment, resources), args.out)
    print(f"Wrote {args.out}")