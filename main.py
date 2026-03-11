import os
from datetime import datetime, timezone
from typing import Literal, Optional

import httpx
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Query
from jose import jwt
from app.core.auth import TokenPayload, require_admin
from app.db.database import shutdown, startup
from app.services.openweather import fetch_air_pollution, geocode_city

from app.models.schemas import (
    AnomalyResponse,
    CompareResponse,
    IngestResult,
    LoginOut,
    ObservationOut,
    RiskScoreOut,
    StationCreate,
    StationOut,
    TrendResponse,
)

load_dotenv()

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
JWT_SECRET = os.getenv("JWT_SECRET", "change_me")
JWT_ALG = os.getenv("JWT_ALG", "HS256")

if not OPENWEATHER_API_KEY:
    raise RuntimeError("OPENWEATHER_API_KEY missing in .env")

app = FastAPI(
    title="Urban Climate Risk & Anomaly Intelligence API (UK)",
    description="A UK-focused environmental analytics API providing climate risk scoring, anomaly detection, trend analysis, station comparison, and live air-quality ingestion from OpenWeather.",
    version="1.0.0"
)

@app.get("/")
def root():
    return {"status": "ok", "docs": "/docs"}

@app.on_event("startup")
async def on_startup():
    await startup(app)


@app.on_event("shutdown")
async def on_shutdown():
    await shutdown(app)


# ---------- Routes ----------
@app.post("/auth/dev-token", response_model=LoginOut, tags=["Auth"])
def dev_token(role: Literal["admin", "user"] = "admin"):
    payload = {"sub": "dev", "role": role}
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)
    return {"token": token}


@app.get("/stations", response_model=list[StationOut], tags=["Stations"])
async def list_stations():
    async with app.state.pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT station_id, city, country, lat, lon, source
            FROM stations_uk
            ORDER BY city;
        """)
    return [dict(r) for r in rows]


@app.post("/stations", response_model=StationOut, status_code=201, tags=["Stations"])
async def create_station(
    payload: StationCreate,
    _: TokenPayload = Depends(require_admin),
):
    async with app.state.pool.acquire() as conn:
        try:
            row = await conn.fetchrow("""
                INSERT INTO stations_uk (station_id, city, country, lat, lon, source)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING station_id, city, country, lat, lon, source;
            """, payload.station_id, payload.city, payload.country, payload.lat, payload.lon, payload.source)
        except asyncpg.UniqueViolationError:
            raise HTTPException(status_code=409, detail="Station already exists")
    return dict(row)


@app.get("/observations", response_model=list[ObservationOut], tags=["Observations"])
async def list_observations(
    station_id: Optional[str] = None,
    limit: int = Query(50, ge=1, le=500),
):
    async with app.state.pool.acquire() as conn:
        if station_id:
            rows = await conn.fetch("""
                SELECT observation_id, station_id, observed_at_utc, pm25, pm10, no2, so2, co, o3, source
                FROM observations_uk
                WHERE station_id = $1
                ORDER BY observed_at_utc DESC
                LIMIT $2;
            """, station_id, limit)
        else:
            rows = await conn.fetch("""
                SELECT observation_id, station_id, observed_at_utc, pm25, pm10, no2, so2, co, o3, source
                FROM observations_uk
                ORDER BY observed_at_utc DESC
                LIMIT $1;
            """, limit)
    return [dict(r) for r in rows]


@app.get("/risk/score", response_model=RiskScoreOut, tags=["Analytics"])
async def risk_score(station_id: str):
    async with app.state.pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT station_id, observed_at_utc, pm25, no2, o3
            FROM observations_uk
            WHERE station_id = $1
            ORDER BY observed_at_utc DESC
            LIMIT 1;
        """, station_id)

    if not row:
        raise HTTPException(status_code=404, detail="No observations found for station")

    pm25 = row["pm25"] or 0
    no2 = row["no2"] or 0
    o3 = row["o3"] or 0

    score = min(
        100,
        (pm25 / 50) * 50 +
        (no2 / 100) * 30 +
        (o3 / 100) * 20
    )

    if score < 34:
        category = "Low"
    elif score < 67:
        category = "Medium"
    else:
        category = "High"

    return {
        "station_id": row["station_id"],
        "observed_at_utc": row["observed_at_utc"],
        "pm25": row["pm25"],
        "no2": row["no2"],
        "o3": row["o3"],
        "risk_score": round(score, 2),
        "category": category,
    }

@app.get("/analytics/anomalies", response_model=AnomalyResponse, tags=["Analytics"])
async def detect_anomalies(
    station_id: str,
    metric: Literal["pm25", "pm10", "no2", "so2", "co", "o3"],
    threshold: float = Query(2.0, ge=0.5, le=5.0),
):
    async with app.state.pool.acquire() as conn:
        metric_col = metric
        rows = await conn.fetch(f"""
            SELECT observation_id, station_id, observed_at_utc, {metric_col} AS value
            FROM observations_uk
            WHERE station_id = $1
              AND {metric} IS NOT NULL
            ORDER BY observed_at_utc ASC;
        """, station_id)

    if not rows:
        raise HTTPException(status_code=404, detail="No observations found for station/metric")

    values = [float(r["value"]) for r in rows]
    mean = sum(values) / len(values)

    if len(values) < 2:
        raise HTTPException(status_code=400, detail="Not enough observations to calculate anomalies")

    variance = sum((v - mean) ** 2 for v in values) / len(values)
    std_dev = variance ** 0.5

    if std_dev == 0:
        return {
            "station_id": station_id,
            "metric": metric,
            "threshold": threshold,
            "mean": round(mean, 2),
            "std_dev": 0.0,
            "anomalies": [],
        }

    anomalies = []
    for r in rows:
        value = float(r["value"])
        z = (value - mean) / std_dev
        if abs(z) >= threshold:
            anomalies.append({
                "observation_id": r["observation_id"],
                "station_id": r["station_id"],
                "observed_at_utc": r["observed_at_utc"],
                "metric": metric,
                "value": value,
                "z_score": round(z, 2),
            })

    return {
        "station_id": station_id,
        "metric": metric,
        "threshold": threshold,
        "mean": round(mean, 2),
        "std_dev": round(std_dev, 2),
        "anomalies": anomalies,
    }

@app.get("/analytics/trends", response_model=TrendResponse, tags=["Analytics"])
async def get_trends(
    station_id: str,
    metric: Literal["pm25", "pm10", "no2", "so2", "co", "o3"],
    limit: int = Query(30, ge=1, le=365),
):
    async with app.state.pool.acquire() as conn:
        rows = await conn.fetch(f"""
            SELECT observed_at_utc, {metric} AS value
            FROM observations_uk
            WHERE station_id = $1
              AND {metric} IS NOT NULL
            ORDER BY observed_at_utc DESC
            LIMIT $2;
        """, station_id, limit)

    if not rows:
        raise HTTPException(status_code=404, detail="No observations found for station/metric")

    # reverse so output is oldest -> newest
    rows = list(reversed(rows))
    values = [float(r["value"]) for r in rows]

    return {
        "station_id": station_id,
        "metric": metric,
        "points": [
            {
                "observed_at_utc": r["observed_at_utc"],
                "value": float(r["value"])
            }
            for r in rows
        ],
        "min_value": round(min(values), 2),
        "max_value": round(max(values), 2),
        "avg_value": round(sum(values) / len(values), 2),
    }

@app.get("/analytics/compare", response_model=CompareResponse, tags=["Analytics"])
async def compare_stations(
    metric: Literal["pm25", "pm10", "no2", "so2", "co", "o3"],
):
    async with app.state.pool.acquire() as conn:
        rows = await conn.fetch(f"""
            SELECT
                s.station_id,
                s.city,
                AVG(o.{metric}) AS avg_value,
                MIN(o.{metric}) AS min_value,
                MAX(o.{metric}) AS max_value,
                COUNT(o.{metric}) AS observation_count
            FROM stations_uk s
            JOIN observations_uk o ON s.station_id = o.station_id
            WHERE o.{metric} IS NOT NULL
            GROUP BY s.station_id, s.city
            ORDER BY AVG(o.{metric}) DESC;
        """)

    if not rows:
        raise HTTPException(status_code=404, detail="No comparison data found")

    return {
        "metric": metric,
        "stations": [
            {
                "station_id": r["station_id"],
                "city": r["city"],
                "metric": metric,
                "avg_value": round(float(r["avg_value"]), 2),
                "min_value": round(float(r["min_value"]), 2),
                "max_value": round(float(r["max_value"]), 2),
                "observation_count": int(r["observation_count"]),
            }
            for r in rows
        ]
    }

@app.get("/stations/{station_id}", response_model=StationOut, tags=["Stations"])
async def get_station(station_id: str):
    async with app.state.pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT station_id, city, country, lat, lon, source
            FROM stations_uk
            WHERE station_id = $1;
        """, station_id)

    if not row:
        raise HTTPException(status_code=404, detail="Station not found")

    return dict(row)

@app.delete("/stations/{station_id}", status_code=204, tags=["Stations"])
async def delete_station(
    station_id: str,
    _: TokenPayload = Depends(require_admin),
):
    async with app.state.pool.acquire() as conn:
        result = await conn.execute("""
            DELETE FROM stations_uk
            WHERE station_id = $1;
        """, station_id)

    if result.endswith("0"):
        raise HTTPException(status_code=404, detail="Station not found")
    
@app.put("/stations/{station_id}", response_model=StationOut, tags=["Stations"])
async def update_station(
    station_id: str,
    payload: StationCreate,
    _: TokenPayload = Depends(require_admin),
):
    async with app.state.pool.acquire() as conn:
        row = await conn.fetchrow("""
            UPDATE stations_uk
            SET city = $2,
                country = $3,
                lat = $4,
                lon = $5,
                source = $6
            WHERE station_id = $1
            RETURNING station_id, city, country, lat, lon, source;
        """,
        station_id,
        payload.city,
        payload.country,
        payload.lat,
        payload.lon,
        payload.source
        )

    if not row:
        raise HTTPException(status_code=404, detail="Station not found")

    return dict(row)
    
@app.get("/health", tags=["System"])
async def health():
    async with app.state.pool.acquire() as conn:
        station_count = await conn.fetchval("SELECT COUNT(*) FROM stations_uk;")
        observation_count = await conn.fetchval("SELECT COUNT(*) FROM observations_uk;")

    return {
        "status": "ok",
        "database": "connected",
        "stations_uk": station_count,
        "observations_uk": observation_count,
    }

@app.post("/ingest/openweather", response_model=IngestResult, tags=["Ingestion"])
async def ingest_openweather(
    city: str = Query(..., min_length=2, max_length=80),
    _: TokenPayload = Depends(require_admin),
):
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
            DO UPDATE SET lat = EXCLUDED.lat, lon = EXCLUDED.lon, source = EXCLUDED.source, city = EXCLUDED.city, country = EXCLUDED.country;
            """,
            station_id, city, lat, lon,
        )

        import uuid
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