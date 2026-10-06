import json
import os
import numpy as np

# Z1 = top-left ... Z9 = bottom-right, numbered row by row (team grid)
N = 3

def aggregate_grid(prob, valid=None, threshold=0.5, n=N):
    """Split a flood-probability map into an n x n grid.
    Returns one dict per zone: zone_id, flood_pct (0-1), mask_confidence (0.5-1)."""
    H, W = prob.shape
    if valid is None:
        valid = np.ones((H, W), dtype=bool)

    row_blocks = np.array_split(np.arange(H), n)   # top to bottom
    col_blocks = np.array_split(np.arange(W), n)   # left to right

    records = []
    k = 0
    for rows in row_blocks:
        for cols in col_blocks:
            k += 1
            p = prob[np.ix_(rows, cols)]
            v = valid[np.ix_(rows, cols)]
            p = p[v]
            if p.size == 0:                          # no valid pixels in this zone
                flood_pct, conf = 0.0, 0.0
            else:
                flood_pct = float((p > threshold).mean())
                conf = float(np.maximum(p, 1 - p).mean())
            records.append({
                "zone_id": f"Z{k}",
                "flood_pct": round(flood_pct, 4),
                "mask_confidence": round(conf, 4),
            })
    return records

def save_json(records, path):
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)