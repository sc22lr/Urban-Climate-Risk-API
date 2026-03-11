from typing import Optional

from fastapi import APIRouter, Query

from app.models.schemas import ObservationOut

router = APIRouter(tags=["Observations"])


@router.get("/observations", response_model=list[ObservationOut])
async def list_observations(
    station_id: Optional[str] = None,
    limit: int = Query(50, ge=1, le=500),
):
    from main import app

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