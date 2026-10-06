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
python build_graph.py --distance-meters 12000
```

The graph is saved to `data/road_network.graphml`. It is intentionally excluded from source control; each teammate can download it locally. OpenStreetMap access and a working internet connection are required for this step.

## Run routing

The sample input contains one assignment and polygon-center destinations for Z1-Z9, based on `module_b_risk_scoring/data/zones.geojson`:

```powershell
python route.py --input sample_input.json --output sample_output.json
```

Input is a JSON object with `assignments`, `zone_destinations`, and optional `blocked_edges`, `flood_data`, and `zone_edges`. When flood data is present, the CLI derives zone-to-road mappings from the zone polygons automatically. Use `--zones` to provide a different GeoJSON file. Any explicit `zone_edges` are added to the derived mappings. Assignments use Person C's fields (`resource_id`, `assigned_zone`, `base_lat`, `base_lng`). A destination may instead be supplied directly on an assignment as `destination_lat` and `destination_lng`.

Example destination map:

```json
{"Z1": {"lat": 27.9827, "lng": 85.0810}}
```

The output is a JSON array, one object per successful resource, using the shared schema. Person E can load it as a list and pass each item's `route` directly to Folium `PolyLine`; use `resource_id` and `eta_minutes` for its label. Route coordinates are always `[lat, lng]`.

## Flood and blocked roads

Pass blocked graph edges as node pairs in `blocked_edges`. These edges are removed from a temporary graph copy, never from the loaded road graph. `flood_data` accepts Person A's `zone_id` / `flood_pct` records. At or above `FLOOD_THRESHOLD` (default `0.50`), roads intersecting that zone's polygon are blocked. The CLI warns when the loaded graph has no roads in one or more zones; increase the graph radius to cover the full grid before relying on routes for those zones.

Routing minimizes OSM road `length`. ETA uses OSMnx edge `travel_time`/`speed_kph` when available; otherwise it uses the configurable 30 km/h estimate. A blocked route or invalid input produces a clear CLI error and does not write a partial output file.

## Offline tests and limitations

Run the routing behavior tests without downloading OSM data:

```powershell
python -m unittest test_route.py
```

The tests use a small in-memory graph and do not represent the real city. Real routes need a GraphML extract covering the full zone grid. Zone-level flood percentages still use a threshold; a detailed flood mask is needed to determine which individual road segments are actually flooded.
