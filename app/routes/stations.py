from fastapi import APIRouter, Depends, HTTPException
import asyncpg

from app.models.schemas import StationOut, StationCreate
from app.core.auth import require_admin, TokenPayload

router = APIRouter(prefix="/stations", tags=["Stations"])


@router.get("", response_model=list[StationOut], 
            summary="List monitoring stations", 
            description="Returns all registered air quality monitoring stations in the database.")
async def list_stations():
    from main import app
    async with app.state.pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT station_id, city, country, lat, lon, source
            FROM stations_uk
            ORDER BY city;
        """)
    return [dict(r) for r in rows]


@router.post("", response_model=StationOut, status_code=201)
async def create_station(
    payload: StationCreate,
    _: TokenPayload = Depends(require_admin),
):
    from main import app

    async with app.state.pool.acquire() as conn:
        try:
            row = await conn.fetchrow("""
                INSERT INTO stations_uk (station_id, city, country, lat, lon, source)
                VALUES ($1,$2,$3,$4,$5,$6)
                RETURNING station_id, city, country, lat, lon, source
            """, payload.station_id, payload.city, payload.country,
               payload.lat, payload.lon, payload.source)
        except asyncpg.UniqueViolationError:
            raise HTTPException(status_code=409, detail="Station already exists")

    return dict(row)