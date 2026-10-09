# Multimodal Geospatial AI for Disaster Response Optimization

An end-to-end decision-support prototype for flood emergency response. It takes Sentinel-1 satellite radar imagery and turns it into zone-level flood maps, risk scores, optimized resource assignments and road routes, all shown on one interactive dashboard.

The scenario is a simulated flood response centred on **Trishuli / Nuwakot, Nepal**, motivated by the August 2026 Bhote Koshi-Trishuli flash flood. It is a prototype of the approach, not an assessment of the real event.

---

## Research question

Can computer-vision-based flood detection, combined with dynamic resource optimization and routing, outperform static or naive emergency response planning?

---

## How it works

```
Sentinel-1 SAR imagery
        |
   Module A: Flood Detection (U-Net)        -> flood % per zone
        |
   Module B: Risk Scoring                   -> risk score + priority rank per zone
        |
   Module C: Resource Allocation (ILP)      -> resource-to-zone assignments
        |
   Module D: Flood-Aware Routing            -> routes + ETAs on the real road network
        |
   Module E: Dashboard & Integration        -> live map, tables, comparison metrics
```

The study area is a **3 x 3 grid (Z1-Z9)** covering about 20 km around the centre point **27.9226, 85.1490** (Z1 = top-left, numbered row by row). Every module uses this same grid.

Each module reads and writes JSON in a fixed format, documented in [`shared/schemas.md`](shared/schemas.md). This is what let five people build the stages in parallel.

---

## Modules

| Module | Folder | What it does | Main tools |
|---|---|---|---|
| A. Flood Detection | `module_a_flood_detection/` | Segments flooded pixels in Sentinel-1 VV/VH imagery and aggregates them into flood % and confidence per zone | PyTorch, segmentation-models-pytorch, rasterio |
| B. Risk Scoring | `module_b_risk_scoring/` | Combines flood extent, population, road accessibility and rainfall into a transparent weighted risk score | pandas, GeoPandas, rasterstats, OpenWeatherMap API |
| C. Resource Allocation | `module_c_allocation/` | Assigns rescue teams, ambulances and boats to zones using integer linear programming, and compares against a greedy baseline | Google OR-Tools |
| D. Routing | `module_d_routing/` | Builds a drivable road graph and computes shortest routes and ETAs, with support for blocking roads in flooded zones | OSMnx, NetworkX, Shapely |
| E. Dashboard & Integration | `module_e_dashboard/` | Loads all module outputs and presents them in one interface | Streamlit, Folium |

### Risk formula

```
risk = 0.4 x flood + 0.3 x population + 0.2 x (1 - road accessibility) + 0.1 x rainfall
```

The weights are tunable parameters, not learned values.

---

## Results

| Item | Result |
|---|---|
| Flood segmentation (U-Net, ResNet34 encoder) | Test IoU **0.59**, F1 **0.742** on held-out Sen1Floods11 chips (validation IoU 0.51) |
| Allocation objective, greedy baseline | 85.26 |
| Allocation objective, optimized (ILP) | **88.10** (+3.3%) |
| People covered, baseline vs optimized | 106.3 vs **125.4** with the same 16 resources |

The optimizer gains by matching resource type to zone conditions: rescue teams go to the highest-risk zone, boats go to the zone with the poorest road access, and ambulances go to a zone with usable roads. Details are in [`module_c_allocation/results.md`](module_c_allocation/results.md).

---

## Run the dashboard

```bash
git clone https://github.com/Kriti57/flood-response-system.git
cd flood-response-system/module_e_dashboard
pip install -r requirements.txt
streamlit run app.py
```

The dashboard reads the committed output files of each module, so you do not need to retrain or rerun anything to view it.

To rerun an individual module, see the README inside its folder:

```bash
# Module C: allocation comparison
cd module_c_allocation
pip install ortools
python compare.py

# Module D: offline routing tests
cd module_d_routing
pip install -r requirements.txt
python -m unittest test_route.py
```

Model weights for Module A are not stored in git. The Drive link is in `module_a_flood_detection/Model file`.

---

## Repository structure

```
flood-response-system/
├── module_a_flood_detection/   data loader, training, inference, zone aggregation
├── module_b_risk_scoring/      population overlay, weather, risk formula, zones.geojson
├── module_c_allocation/        ILP optimizer, greedy baseline, comparison, results.md
├── module_d_routing/           road graph, routing, flood-aware edge blocking
├── module_e_dashboard/         pipeline.py, Streamlit app, mock data
└── shared/                     JSON schemas shared by all modules
```

---

## Data sources

- **Sen1Floods11**: Sentinel-1 flood-labelled chips (Bonafilia et al., CVPRW 2020)
- **WorldPop**: gridded population estimates
- **OpenStreetMap** via OSMnx: road network
- **OpenWeatherMap**: rainfall forecast

---

## Limitations

- The flood model is trained and evaluated on the Sen1Floods11 benchmark. The sample zone output comes from a benchmark chip, **not Nepal imagery**.
- The resource fleet (5 rescue teams, 8 ambulances, 3 boats) and base locations are **assumed**, not official data. The fleet covers only a small share of the estimated need.
- Which roads are blocked is derived from zone-level flood percentages, not a live road-closure feed.
- Steep valleys cause radar shadow and layover that can resemble water, which a benchmark-trained model does not account for.

Future work: train on labelled Nepal-region imagery, use real fleet and hospital data, and re-optimize automatically when roads or flood conditions change.

---

## Team

| Name | Module |
|---|---|
| Ishita Kawadkar | A. Flood Detection |
| Nishita Kawadkar | B. Risk Scoring |
| Meshwa Verma | C. Resource Allocation |
| Priya | D. Routing |
| Kriti Gupta | E. Dashboard & Integration |