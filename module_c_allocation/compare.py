"""Run BOTH methods on the same input and report the improvement - your headline result.

Run:  python module_c_allocation/compare.py [--risk FILE] [--write-md]
--write-md writes results.md (do this on Day 3 with REAL risk data, not the dummy file).
"""
import argparse
from allocation_common import HERE, evaluate, load_resources, load_zones, print_report
from baseline import run_baseline
from allocate import run_optimized

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--risk", default=None)
    ap.add_argument("--resources", default=None)
    ap.add_argument("--write-md", action="store_true")
    args = ap.parse_args()
    zones, resources = load_zones(args.risk), load_resources(args.resources)
    base = evaluate(run_baseline(zones, resources), zones, resources)
    opt = evaluate(run_optimized(zones, resources), zones, resources)
    print_report("BASELINE (greedy)", base)
    print_report("OPTIMIZED (ILP)", opt)
    gain = 100 * (opt["objective"] - base["objective"]) / base["objective"] if base["objective"] else 0.0
    print(f"\nIMPROVEMENT: optimized beats baseline by {gain:.1f}% "
          f"({opt['objective']:.2f} vs {base['objective']:.2f})")
    if args.write_md:
        src = args.risk or "dummy_risk.json"
        lines = ["# Allocation results: optimized vs baseline", "", f"Input: `{src}`", "",
                 "| Method | Objective (sum risk x covered) | People covered | Resources used |", "|---|---|---|---|",
                 f"| Baseline (greedy) | {base['objective']:.2f} | {base['total_covered']:.1f} / {base['total_need']:.1f} | {base['resources_used']}/{base['resources_total']} |",
                 f"| Optimized (ILP) | {opt['objective']:.2f} | {opt['total_covered']:.1f} / {opt['total_need']:.1f} | {opt['resources_used']}/{opt['resources_total']} |",
                 "", f"**Optimized beats baseline by {gain:.1f}%.**", "",
                 "See `allocation_common.py` for the assumptions (rescue fraction, resource eligibility rules)."]
        (HERE / "results.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
        print("Wrote results.md")