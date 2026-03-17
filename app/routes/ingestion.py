from datetime import datetime, timezone
import uuid

import httpx
from fastapi import APIRouter, Depends, Query, Request

from app.core.auth import TokenPayload, require_admin
from app.models.schemas import IngestResult
from app.services.openweather import fetch_air_pollution, geocode_city

router = APIRouter(prefix="/ingest", tags=["Ingestion"])


@router.post(
    "/openweather",
    response_model=IngestResult,
    status_code=201,
    summary="Ingest air pollution data from OpenWeather",
    description="Fetches real-time pollution data for a city using the OpenWeather API and stores it in the database."
)
async def ingest_openweather(
    request: Request,
    city: str = Query(..., min_length=2, max_length=80),
    _: TokenPayload = Depends(require_admin),
):
    app = request.app
    station_id = f"{city.strip().lower().replace(' ', '_')}_uk"

    async with httpx.AsyncClient() as client:
        lat, lon = await geocode_city(client, city)
        item = await fetch_air_pollution(client, lat, lon)

    observed_at = datetime.fromtimestamp(int(item["dt"]), tz=timezone.utc)
    c = item.get("components", {})

    pm25 = c.get("pm2_5")
    pm10 = c.get("pm10")
    no2 = c.get("no2")
    so2 = c.get("so2")
    co = c.get("co")
    o3 = c.get("o3")

    async with app.state.pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO stations_uk (station_id, city, country, lat, lon, source)
            VALUES ($1, $2, 'UK', $3, $4, 'openweather')
            ON CONFLICT (station_id)
            DO UPDATE SET
                lat = EXCLUDED.lat,
                lon = EXCLUDED.lon,
                source = EXCLUDED.source,
                city = EXCLUDED.city,
                country = EXCLUDED.country;
            """,
            station_id, city, lat, lon,
        )

        obs_id = uuid.uuid4()

        result = await conn.execute(
            """
            INSERT INTO observations_uk
              (observation_id, station_id, observed_at_utc, pm25, pm10, no2, so2, co, o3, source)
            VALUES
              ($1, $2, $3, $4, $5, $6, $7, $8, $9, 'openweather')
            ON CONFLICT (station_id, observed_at_utc)
            DO NOTHING;
            """,
            obs_id, station_id, observed_at, pm25, pm10, no2, so2, co, o3,
        )

        inserted = result.endswith("1")

    return IngestResult(
        station_id=station_id,
        city=city,
        lat=lat,
        lon=lon,
        observed_at_utc=observed_at,
        pm25=pm25,
        pm10=pm10,
        no2=no2,
        so2=so2,
        co=co,
        o3=o3,
        inserted=inserted,
    )