"# Module D - Dynamic Routing" 

Builds a drivable OpenStreetMap graph and returns shortest routes for resource assignments. Each successful output item matches `shared/schemas.md` exactly: `resource_id`, `route` as `[latitude, longitude]` pairs, and `eta_minutes`.

## Install

From this directory, install the dependencies:

```powershell
python -m pip install -r requirements.txt
```

## Download the road graph

The default place follows the dashboard scenario (Trishuli / Nuwakot, Nepal). OSMnx downloads a 5 km drivable-road radius around the geocoded place center; adjust it with `--distance-meters`:

```powershell
python build_graph.py
python build_graph.py --city "Bhopal, Madhya Pradesh, India"
python build_graph.py --distance-meters 8000
```

The graph is saved to `data/road_network.graphml`. It is intentionally excluded from source control; each teammate can download it locally. OpenStreetMap access and a working internet connection are required for this step.

## Run routing

The sample input contains one assignment and a demo destination point (the dashboard's current map center). Replace that point with a verified zone destination/centroid when the team has one:

```powershell
python route.py --input sample_input.json --output sample_output.json
```

Input is a JSON object with `assignments`, `zone_destinations`, and optional `blocked_edges`, `flood_data`, and `zone_edges`. Assignments use Person C's fields (`resource_id`, `assigned_zone`, `base_lat`, `base_lng`). A destination may instead be supplied directly on an assignment as `destination_lat` and `destination_lng`.

Example destination map:

```json
{"Z1": {"lat": 27.9226, "lng": 85.1490}}
```

The output is a JSON array, one object per successful resource, using the shared schema. Person E can load it as a list and pass each item's `route` directly to Folium `PolyLine`; use `resource_id` and `eta_minutes` for its label. Route coordinates are always `[lat, lng]`.

## Flood and blocked roads

Pass blocked graph edges as node pairs in `blocked_edges`. These edges are removed from a temporary graph copy, never from the loaded road graph. `flood_data` accepts Person A's `zone_id` / `flood_pct` records. At or above `FLOOD_THRESHOLD` (default `0.50`), a zone is considered heavily flooded. Flood data only affects routing when `zone_edges` maps that zone to graph node pairs; the repository has no zone polygons or road-to-zone data, so no geographic matching is fabricated.

Routing minimizes OSM road `length`. ETA uses OSMnx edge `travel_time`/`speed_kph` when available; otherwise it uses the configurable 30 km/h estimate. A blocked route or invalid input produces a clear CLI error and does not write a partial output file.

## Offline tests and limitations

Run the routing behavior tests without downloading OSM data:

```powershell
python -m unittest test_route.py
```

The tests use a small in-memory graph and do not represent the real city. Real routes need the downloaded GraphML and accurate zone destination coordinates. Flood-zone polygon matching is not implemented.
