"""Day 1 sanity check: confirms OR-Tools is installed and can solve a tiny assignment problem.

Run:  python module_c_allocation/day1_ortools_check.py
Expected: Status OPTIMAL, Resource 0->Zone 0, 1->Zone 1, 2->Zone 2, total value 25.
"""
from ortools.sat.python import cp_model

# value[r][z] = benefit of sending resource r to zone z (made-up numbers)
value = [
    [9, 4, 3],
    [6, 8, 2],
    [5, 7, 8],
]
n_res, n_zones = len(value), len(value[0])

model = cp_model.CpModel()
x = {(r, z): model.NewBoolVar(f"x_{r}_{z}") for r in range(n_res) for z in range(n_zones)}

for r in range(n_res):                       # each resource used at most once
    model.Add(sum(x[r, z] for z in range(n_zones)) <= 1)
for z in range(n_zones):                     # each zone gets at most one resource (toy version)
    model.Add(sum(x[r, z] for r in range(n_res)) <= 1)

model.Maximize(sum(value[r][z] * x[r, z] for r in range(n_res) for z in range(n_zones)))

solver = cp_model.CpSolver()
status = solver.Solve(model)
print("Status:", solver.StatusName(status))
for (r, z), var in x.items():
    if solver.Value(var):
        print(f"Resource {r} -> Zone {z}  (value {value[r][z]})")
print("Total value:", solver.ObjectiveValue())