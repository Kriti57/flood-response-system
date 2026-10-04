import os
import numpy as np
import geopandas as gpd
from shapely.geometry import box
from rasterstats import zonal_stats

# ---------- SETTINGS (change these if needed) ----------
RASTER_PATH = "data/worldpop.tif"   # WorldPop population COUNTS file
ROWS, COLS = 4, 2                   # 4 x 2 grid = 8 zones (Z1..Z8)

# Approximate bounding box for Greater Mumbai (share this with Person A!)
MIN_LON, MAX_LON = 72.77, 72.99
MIN_LAT, MAX_LAT = 18.89, 19.27
# -------------------------------------------------------


def make_grid(min_lon, max_lon, min_lat, max_lat, rows, cols):
    """Split the bounding box into a rows x cols grid.
    Zones are numbered left to right, top to bottom (Z1 = top-left)."""
    xs = np.linspace(min_lon, max_lon, cols + 1)
    ys = np.linspace(max_lat, min_lat, rows + 1)  # top to bottom

    cells, ids, n = [], [], 1
    for r in range(rows):
        for c in range(cols):
            cells.append(box(xs[c], ys[r + 1], xs[c + 1], ys[r]))
            ids.append(f"Z{n}")
            n += 1
    return gpd.GeoDataFrame({"zone_id": ids}, geometry=cells, crs="EPSG:4326")


def add_population(zones, raster_path):
    """Add total_population = sum of WorldPop pixels inside each zone."""
    if not os.path.exists(raster_path):
        raise FileNotFoundError(
            f"Could not find {raster_path}. Check that worldpop.tif is inside "
            "module_b_risk_scoring/data/ and that you run this script from "
            "the module_b_risk_scoring folder."
        )
    stats = zonal_stats(zones, raster_path, stats=["sum"])
    zones["total_population"] = [
        int(round(s["sum"])) if s["sum"] is not None else 0 for s in stats
    ]
    return zones


if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)

    zones = make_grid(MIN_LON, MAX_LON, MIN_LAT, MAX_LAT, ROWS, COLS)
    zones = add_population(zones, RASTER_PATH)

    print()
    print(zones[["zone_id", "total_population"]].to_string(index=False))
    total = zones["total_population"].sum()
    print(f"\nTotal population in grid: {total:,}")

    if total == 0:
        print("WARNING: total is 0. The raster probably does not cover this city.")

    # Save for Day 2 (risk formula reads these)
    zones.to_file("data/zones.geojson", driver="GeoJSON")
    zones[["zone_id", "total_population"]].to_json(
        "data/population_per_zone.json", orient="records", indent=2
    )
    print("Saved data/zones.geojson and data/population_per_zone.json")