# Module E - Dashboard & Integration

Reads output from Modules A-D and displays it on a live dashboard (Streamlit + Folium map).

## Install
```powershell
pip install -r requirements.txt
```

## Run
```powershell
streamlit run app.py
```

## Status
- Resource allocation: REAL (Person C, merged)
- Flood detection, risk scoring, routing: still mocked (mock_data/ folder), will be swapped in as each module's real output lands

## Files
| File | Purpose |
|---|---|
| `pipeline.py` | Loads all 4 stages, used by app.py |
| `app.py` | Streamlit dashboard |
| `mock_data/` | Placeholder JSON for stages not yet real |# Module E - Dashboard & Integration

Reads output from Modules A-D and displays it on a live dashboard (Streamlit + Folium map).

## Install
```powershell
pip install -r requirements.txt
```

## Run
```powershell
streamlit run app.py
```

## Status
- Resource allocation: REAL (Person C, merged)
- Flood detection, risk scoring, routing: still mocked (mock_data/ folder), will be swapped in as each module's real output lands

## Files
| File | Purpose |
|---|---|
| `pipeline.py` | Loads all 4 stages, used by app.py |
| `app.py` | Streamlit dashboard |
| `mock_data/` | Placeholder JSON for stages not yet real |