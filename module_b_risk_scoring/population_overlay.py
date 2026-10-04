import os
import numpy as np
import geopandas as gpd
from shapely.geometry import box
from rasterstats import zonal_stats

# ---------- SETTINGS (change these if needed) ----------
RASTER_PATH = "data/worldpop.tif"   # WorldPop NEPAL population COUNTS file
CENTER_LAT, CENTER_LON = 27.9226, 85.1490   # Trishuli / Nuwakot
HALF_SIZE_KM = 10                   # box extends 10 km each way = 20 km x 20 km
ROWS, COLS = 3, 3                   # 3 x 3 grid = 9 zones (Z1..Z9)
# -------------------------------------------------------


def make_grid(center_lat, center_lon, half_size_km, rows, cols):
    """Build a rows x cols grid centered on a point.
    Zones are numbered left to right, top to bottom (Z1 = top-left)."""
    dlat = half_size_km / 111.0
    dlon = half_size_km / (111.0 * np.cos(np.radians(center_lat)))
    min_lat, max_lat = center_lat - dlat, center_lat + dlat
    min_lon, max_lon = center_lon - dlon, center_lon + dlon
    print(f"Bounding box: lon {min_lon:.4f} to {max_lon:.4f}, "
          f"lat {min_lat:.4f} to {max_lat:.4f}")

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

    zones = make_grid(CENTER_LAT, CENTER_LON, HALF_SIZE_KM, ROWS, COLS)
    zones = add_population(zones, RASTER_PATH)

    print()
    print(zones[["zone_id", "total_population"]].to_string(index=False))
    total = zones["total_population"].sum()
    print(f"\nTotal population in grid: {total:,}")

    if total == 0:
        print("WARNING: total is 0. The raster probably does not cover this region.")

    zones.to_file("data/zones.geojson", driver="GeoJSON")
    zones[["zone_id", "total_population"]].to_json(
        "data/population_per_zone.json", orient="records", indent=2
    )
    print("Saved data/zones.geojson and data/population_per_zone.json")