import os
import requests

CENTER_LAT, CENTER_LON = 27.9226, 85.1490   # Trishuli / Nuwakot
HEAVY_RAIN_MM = 50.0   # 24h rainfall treated as "maximum" risk (tunable)
DEFAULT_ADJUSTMENT = 0.5   # neutral value used if the API call fails


def get_rainfall_mm(lat=CENTER_LAT, lon=CENTER_LON):
    """Total forecast rainfall (mm) over the next 24 hours, or None if unavailable."""
    key = os.environ.get("OPENWEATHER_API_KEY")
    if not key:
        print("No OPENWEATHER_API_KEY set.")
        return None
    try:
        r = requests.get(
            "https://api.openweathermap.org/data/2.5/forecast",
            params={"lat": lat, "lon": lon, "appid": key, "units": "metric"},
            timeout=10,
        )
        r.raise_for_status()
        next_24h = r.json()["list"][:8]   # 8 forecast steps x 3 hours = 24 h
        return sum(item.get("rain", {}).get("3h", 0.0) for item in next_24h)
    except Exception as e:
        print(f"Weather request failed: {e}")
        return None


def rainfall_to_adjustment(mm):
    """Convert rainfall in mm to a 0-1 number (0 = dry, 1 = very heavy rain)."""
    if mm is None:
        return DEFAULT_ADJUSTMENT
    return round(min(mm / HEAVY_RAIN_MM, 1.0), 2)


if __name__ == "__main__":
    mm = get_rainfall_mm()
    print("Forecast rain next 24h (mm):", mm)
    print("rainfall_adjustment:", rainfall_to_adjustment(mm))