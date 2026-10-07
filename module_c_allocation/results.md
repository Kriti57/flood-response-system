# Allocation results: optimized vs baseline

Input: `C:\Users\meshw\Documents\b_v3.json`

| Method | Objective (sum risk x covered) | People covered | Resources used |
|---|---|---|---|
| Baseline (greedy) | 85.26 | 106.3 / 953.1 | 16/16 |
| Optimized (ILP) | 88.10 | 125.4 / 953.1 | 16/16 |

**Optimized beats baseline by 3.3%.**

See `allocation_common.py` for the assumptions (rescue fraction, resource eligibility rules).
