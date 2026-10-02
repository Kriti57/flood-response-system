# Data Schemas Between Modules

Every module must output JSON matching the format below EXACTLY (same field names,
same structure). If your module isn't ready yet, use these as sample/dummy data so
downstream teammates can start building against the real shape immediately.

## 1. Person A (Flood Detection) → Person B (Risk Scoring)

One object per zone:
```json
{
  "zone_id": "Z1",
  "flood_pct": 0.62,
  "mask_confidence": 0.88
}
```

## 2. Person B (Risk Scoring) → Person C (Allocation) and Person D (Routing)

One object per zone:
```json
{
  "zone_id": "Z1",
  "risk_score": 0.81,
  "population_affected": 8400,
  "road_accessibility": 0.3,
  "priority_rank": 1
}
```

## 3. Person C (Allocation) → Person D (Routing) and Person E (Dashboard)

One object per resource:
```json
{
  "resource_id": "RescueTeam-2",
  "assigned_zone": "Z1",
  "base_lat": 0.0,
  "base_lng": 0.0
}
```

## 4. Person D (Routing) → Person E (Dashboard)

One object per resource:
```json
{
  "resource_id": "RescueTeam-2",
  "route": [[0.0, 0.0], [0.1, 0.1]],
  "eta_minutes": 14
}
```

## Rules
- Field names must match exactly (case-sensitive).
- If a field isn't ready yet, send it with a placeholder value (e.g. `0.5`), never omit it.
- Any schema CHANGE must be posted in the group chat and agreed by whoever sends/receives it.