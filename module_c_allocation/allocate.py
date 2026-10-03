"""OPTIMIZED allocation: integer linear program solved with Google OR-Tools.

Decision variables
  x[r,z]    = 1 if resource r is sent to zone z (only created if r is eligible for z)
  cov[z]    = people covered in zone z   (0 <= cov[z] <= need[z])
Constraints
  each resource is assigned to at most one zone
  cov[z] <= sum_r  effectiveness(r,z) * capacity[r] * x[r,z]
Objective (maximize)
  sum_z risk[z] * cov[z]  -  EPS * sum x      (EPS breaks ties: no pointless assignments)

Run:  python module_c_allocation/allocate.py [--risk FILE] [--resources FILE] [--out FILE]
"""
import argparse
from ortools.linear_solver import pywraplp
from allocation_common import (HERE, UNASSIGNED, effectiveness, evaluate, load_resources,
                               load_zones, print_report, save_json, to_schema_output, zone_need)

EPS = 1e-3  # far smaller than any real benefit, so it only removes useless assignments


def run_optimized(zones, resources):
    solver = pywraplp.Solver.CreateSolver("SCIP") or pywraplp.Solver.CreateSolver("CBC")
    if solver is None:
        raise RuntimeError("No MIP solver available in this OR-Tools install")
    inf = solver.infinity()

    x, eff = {}, {}
    for r in resources:
        for z in zones:
            e = effectiveness(r["type"], z["road_accessibility"])
            if e > 0:
                eff[r["resource_id"], z["zone_id"]] = e
                x[r["resource_id"], z["zone_id"]] = solver.BoolVar(f"x_{r['resource_id']}_{z['zone_id']}")
    cov = {z["zone_id"]: solver.NumVar(0, zone_need(z), f"cov_{z['zone_id']}") for z in zones}

    for r in resources:                                   # each resource used at most once
        ct = solver.Constraint(-inf, 1)
        for z in zones:
            if (r["resource_id"], z["zone_id"]) in x:
                ct.SetCoefficient(x[r["resource_id"], z["zone_id"]], 1)

    cap = {r["resource_id"]: r["capacity_people"] for r in resources}
    for z in zones:                                       # coverage limited by assigned capacity
        ct = solver.Constraint(-inf, 0)
        ct.SetCoefficient(cov[z["zone_id"]], 1)
        for r in resources:
            key = (r["resource_id"], z["zone_id"])
            if key in x:
                ct.SetCoefficient(x[key], -eff[key] * cap[r["resource_id"]])

    obj = solver.Objective()
    for z in zones:
        obj.SetCoefficient(cov[z["zone_id"]], z["risk_score"])
    for var in x.values():
        obj.SetCoefficient(var, -EPS)
    obj.SetMaximization()

    status = solver.Solve()
    if status != pywraplp.Solver.OPTIMAL:
        raise RuntimeError(f"Solver did not reach an optimal solution (status code {status})")

    assignment = {r["resource_id"]: UNASSIGNED for r in resources}
    for (rid, zid), var in x.items():
        if var.solution_value() > 0.5:
            assignment[rid] = zid
    return assignment


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--risk", default=None, help="risk JSON (schema 2); default dummy_risk.json")
    ap.add_argument("--resources", default=None, help="resources JSON; default resources.json")
    ap.add_argument("--out", default=str(HERE / "allocation_output.json"))
    args = ap.parse_args()
    zones, resources = load_zones(args.risk), load_resources(args.resources)
    assignment = run_optimized(zones, resources)
    print_report("OPTIMIZED (ILP)", evaluate(assignment, zones, resources))
    save_json(to_schema_output(assignment, resources), args.out)
    print(f"Wrote {args.out}")