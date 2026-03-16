import os

import httpx
from dotenv import load_dotenv
from fastapi import HTTPException

load_dotenv()

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")


async def geocode_city(client: httpx.AsyncClient, city: str) -> tuple[float, float]:
    if not OPENWEATHER_API_KEY:
        raise HTTPException(status_code=500, detail="OPENWEATHER_API_KEY is not configured")

    url = "https://api.openweathermap.org/geo/1.0/direct"
    params = {"q": f"{city},GB", "limit": 1, "appid": OPENWEATHER_API_KEY}
    r = await client.get(url, params=params, timeout=15)
    r.raise_for_status()
    data = r.json()

    if not data:
        raise HTTPException(status_code=404, detail=f"City not found via geocoding: {city}")

    return float(data[0]["lat"]), float(data[0]["lon"])


async def fetch_air_pollution(client: httpx.AsyncClient, lat: float, lon: float) -> dict:
    if not OPENWEATHER_API_KEY:
        raise HTTPException(status_code=500, detail="OPENWEATHER_API_KEY is not configured")

    url = "https://api.openweathermap.org/data/2.5/air_pollution"
    params = {"lat": lat, "lon": lon, "appid": OPENWEATHER_API_KEY}
    r = await client.get(url, params=params, timeout=15)
    r.raise_for_status()
    data = r.json()

    if "list" not in data or not data["list"]:
        raise HTTPException(status_code=502, detail="OpenWeather returned no pollution data")

    return data["list"][0]