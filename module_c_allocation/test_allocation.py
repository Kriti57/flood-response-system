"""Simple self-checks (no pytest needed).  Run:  python module_c_allocation/test_allocation.py"""
from allocation_common import (UNASSIGNED, effectiveness, evaluate, load_resources, load_zones,
                               to_schema_output, zone_need)
from baseline import run_baseline
from allocate import run_optimized

zones, resources = load_zones(), load_resources()
base_assign, opt_assign = run_baseline(zones, resources), run_optimized(zones, resources)
zone_ids = {z["zone_id"] for z in zones}


def check_schema(assignment, name):
    out = to_schema_output(assignment, resources)
    assert len(out) == len(resources), f"{name}: must output one row per resource"
    assert {r["resource_id"] for r in out} == {r["resource_id"] for r in resources}
    for row in out:
        assert set(row) == {"resource_id", "assigned_zone", "base_lat", "base_lng"}, f"{name}: bad fields"
        assert row["assigned_zone"] in zone_ids | {UNASSIGNED}, f"{name}: unknown zone {row['assigned_zone']}"


def check_feasible(assignment, name):
    zmap = {z["zone_id"]: z for z in zones}
    for r in resources:
        zid = assignment[r["resource_id"]]
        if zid != UNASSIGNED:
            assert effectiveness(r["type"], zmap[zid]["road_accessibility"]) > 0, \
                f"{name}: {r['resource_id']} sent to ineligible {zid}"


def test_all():
    for name, a in (("baseline", base_assign), ("optimized", opt_assign)):
        check_schema(a, name)
        check_feasible(a, name)
        res = evaluate(a, zones, resources)
        for p in res["per_zone"]:
            assert p["covered"] <= p["need"] + 1e-9, f"{name}: coverage exceeds need"
    b, o = evaluate(base_assign, zones, resources), evaluate(opt_assign, zones, resources)
    assert o["objective"] >= b["objective"] - 1e-6, "optimized must never be worse than baseline"
    try:
        effectiveness("helicopter", 0.5)
        raise AssertionError("unknown type should raise")
    except ValueError:
        pass
    print(f"All checks passed. baseline={b['objective']:.2f}  optimized={o['objective']:.2f}")


if __name__ == "__main__":
    test_all()