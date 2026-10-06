# Allocation Results: Optimized vs Baseline

## Status
Results below are from Meshwa's original 6-zone test data (Day 2), used to validate
the methodology. A rerun against the real Z1-Z9 zone grid is pending real
road_accessibility values from Person D (currently placeholder 0.5 for all zones,
which causes both methods to converge - see note below).

## Methodology
Both methods share the same scoring function (`allocation_common.py`):
- Each zone has a rescue need = population_affected x 0.02 (first-wave rescue fraction)
- A resource's effective capacity depends on its type and the zone's road_accessibility:
  - Rescue teams: work anywhere, better with road access
  - Ambulances: need accessible roads (ineligible below 0.25 accessibility)
  - Boats: most useful where roads are cut (ineligible above 0.70 accessibility)
- Objective = sum of (risk_score x people_covered) across all zones

**Baseline (greedy):** assigns resources to highest-risk zones first, in order,
without considering resource-to-zone fit.

**Optimized (ILP):** solved with Google OR-Tools, maximizes the same objective
while respecting resource type eligibility and capacity constraints.

## Day 2 Results (6-zone test data)
| Method | Objective | People Covered | Resources Used |
|---|---|---|---|
| Baseline (greedy) | 86.51 | 106.8 / 1054.0 | 16/16 |
| Optimized (ILP) | 92.02 | 126.4 / 1054.0 | 16/16 |

**Optimized beat baseline by 6.4%.** The optimizer spread resources across 3 zones
(Z1, Z2, Z4) by matching resource type to road conditions - e.g. boats were sent to
the zone with the worst road access (0.1) rather than piling everything into the
single highest-risk zone, as the baseline did.

## Known limitation (Day 3)
With all zones sharing an identical placeholder road_accessibility of 0.5, both
methods converge to sending all resources to the single highest-risk zone (Z5),
since there is no accessibility difference to optimize around. This produces a
0.0% improvement, which is a direct, correctly-diagnosed consequence of
incomplete input data, not a bug in the allocation logic. Once real road
accessibility values are available, the methodology above is expected to show
meaningful improvement again.