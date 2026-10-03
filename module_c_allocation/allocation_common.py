"""Shared logic for the baseline (greedy) and optimized (ILP) allocators.

Both methods use the SAME model of the world and the SAME scoring function,
so the comparison between them is fair.

MODEL (all assumptions are tunable constants below - state them in your report):
  * Each zone has a rescue NEED (in people) = population_affected * RESCUE_FRACTION.
  * A resource of capacity C sent to a zone with road accessibility a delivers
    effective capacity  C * effectiveness(type, a).
  * Zone coverage = min(need, sum of effective capacity assigned to it).
  * Score (objective) = sum over zones of  risk_score * coverage.
    i.e. "risk_score x population_covered", as in the sprint plan.
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent

# ---- Tunable assumptions ---------------------------------------------------
RESCUE_FRACTION = 0.02      # share of affected people needing rescue in the first response wave
AMBULANCE_MIN_ACCESS = 0.25  # ambulances need roads: ineligible below this road_accessibility
BOAT_MAX_ACCESS = 0.70       # boats only useful where roads are cut: ineligible above this
UNASSIGNED = None          # value of assigned_zone for an unused resource (confirm with Persons D/E)
# ---------------------------------------------------------------------------

RESOURCE_FIELDS = ("resource_id", "type", "capacity_people", "base_lat", "base_lng")
ZONE_FIELDS = ("zone_id", "risk_score", "population_affected", "road_accessibility", "priority_rank")


def load_resources(path=None):
    path = Path(path) if path else HERE / "resources.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    resources = data["resources"] if isinstance(data, dict) else data
    for i, r in enumerate(resources):
        missing = [f for f in RESOURCE_FIELDS if f not in r]
        if missing:
            raise ValueError(f"resources[{i}] missing fields: {missing}")
    ids = [r["resource_id"] for r in resources]
    if len(ids) != len(set(ids)):
        raise ValueError("resources.json contains duplicate resource_id values")
    return resources


def load_zones(path=None):
    """Load Person B's risk output (schema 2): a JSON list with one object per zone."""
    path = Path(path) if path else HERE / "dummy_risk.json"
    zones = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(zones, list):
        raise ValueError("risk file must be a JSON list (one object per zone)")
    for i, z in enumerate(zones):
        missing = [f for f in ZONE_FIELDS if f not in z]
        if missing:
            raise ValueError(f"zones[{i}] missing fields: {missing}")
        if not 0 <= z["risk_score"] <= 1 or not 0 <= z["road_accessibility"] <= 1:
            raise ValueError(f"zones[{i}] risk_score / road_accessibility must be within 0-1")
    ids = [z["zone_id"] for z in zones]
    if len(ids) != len(set(ids)):
        raise ValueError("risk file contains duplicate zone_id values")
    return zones


def effectiveness(rtype, road_accessibility):
    """Fraction (0-1) of a resource's capacity that is usable in a zone. 0 = ineligible."""
    a = road_accessibility
    if rtype == "rescue_team":          # works anywhere, better with road access
        return 0.6 + 0.4 * a
    if rtype == "ambulance":            # needs usable roads
        return a if a >= AMBULANCE_MIN_ACCESS else 0.0
    if rtype == "boat":                 # useful where roads are flooded/cut
        return (1 - a) if a <= BOAT_MAX_ACCESS else 0.0
    raise ValueError(f"unknown resource type: {rtype!r}")


def zone_need(zone):
    return zone["population_affected"] * RESCUE_FRACTION


def evaluate(assignment, zones, resources):
    """Score an assignment {resource_id: zone_id or UNASSIGNED}. Used for BOTH methods."""
    zmap = {z["zone_id"]: z for z in zones}
    rmap = {r["resource_id"]: r for r in resources}
    capacity = {z["zone_id"]: 0.0 for z in zones}
    count = {z["zone_id"]: 0 for z in zones}
    for rid, zid in assignment.items():
        if zid == UNASSIGNED:
            continue
        e = effectiveness(rmap[rid]["type"], zmap[zid]["road_accessibility"])
        if e <= 0:
            raise ValueError(f"{rid} ({rmap[rid]['type']}) is not eligible for {zid}")
        capacity[zid] += e * rmap[rid]["capacity_people"]
        count[zid] += 1
    per_zone, objective = [], 0.0
    for z in zones:
        zid, need = z["zone_id"], zone_need(z)
        covered = min(need, capacity[zid])
        objective += z["risk_score"] * covered
        per_zone.append({"zone_id": zid, "risk_score": z["risk_score"], "need": need,
                         "resources_assigned": count[zid], "covered": covered,
                         "coverage_pct": 100 * covered / need if need else 100.0})
    total_need = sum(p["need"] for p in per_zone)
    total_cov = sum(p["covered"] for p in per_zone)
    return {"objective": objective, "per_zone": per_zone, "total_need": total_need,
            "total_covered": total_cov, "resources_used": sum(count.values()),
            "resources_total": len(resources)}


def to_schema_output(assignment, resources):
    """Schema 3 (shared/schemas.md): one object per resource, no field ever omitted."""
    return [{"resource_id": r["resource_id"],
             "assigned_zone": assignment.get(r["resource_id"], UNASSIGNED),
             "base_lat": r["base_lat"], "base_lng": r["base_lng"]} for r in resources]


def save_json(rows, path):
    Path(path).write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")


def print_report(title, result):
    print(f"\n=== {title} ===")
    print(f"{'Zone':<5}{'Risk':>6}{'Need':>8}{'#Res':>6}{'Covered':>9}{'Cov %':>8}")
    for p in result["per_zone"]:
        print(f"{p['zone_id']:<5}{p['risk_score']:>6.2f}{p['need']:>8.1f}"
              f"{p['resources_assigned']:>6}{p['covered']:>9.1f}{p['coverage_pct']:>7.0f}%")
    print(f"Resources used: {result['resources_used']}/{result['resources_total']}   "
          f"People covered: {result['total_covered']:.1f}/{result['total_need']:.1f}")
    print(f"OBJECTIVE (sum risk x covered): {result['objective']:.2f}")