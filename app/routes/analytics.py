from typing import Literal

from fastapi import APIRouter, HTTPException, Query

from app.models.schemas import AnomalyResponse, CompareResponse, RiskScoreOut, TrendResponse

router = APIRouter(tags=["Analytics"])


@router.get(
    "/risk/score",
    response_model=RiskScoreOut,
    summary="Calculate environmental risk score",
    description="Computes a pollution risk score using PM2.5, NO2 and O3 measurements from the most recent observation."
)
async def risk_score(station_id: str):
    from main import app

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


@router.get(
    "/analytics/anomalies",
    response_model=AnomalyResponse,
    summary="Detect anomalous pollution values",
    description="Identifies unusual pollutant readings for a station using z-score based anomaly detection."
)
async def detect_anomalies(
    station_id: str,
    metric: Literal["pm25", "pm10", "no2", "so2", "co", "o3"],
    threshold: float = Query(2.0, ge=0.5, le=5.0),
):
    from main import app

    async with app.state.pool.acquire() as conn:
        rows = await conn.fetch(f"""
            SELECT observation_id, station_id, observed_at_utc, {metric} AS value
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


@router.get(
    "/analytics/trends",
    response_model=TrendResponse,
    summary="Retrieve pollution trends",
    description="Returns a chronological series of pollutant values for a station together with min, max, and average statistics."
)
async def get_trends(
    station_id: str,
    metric: Literal["pm25", "pm10", "no2", "so2", "co", "o3"],
    limit: int = Query(30, ge=1, le=365),
):
    from main import app

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


@router.get(
    "/analytics/compare",
    response_model=CompareResponse,
    summary="Compare stations by pollutant level",
    description="Compares stations using average, minimum, and maximum pollutant values."
)
async def compare_stations(
    metric: Literal["pm25", "pm10", "no2", "so2", "co", "o3"],
):
    from main import app

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