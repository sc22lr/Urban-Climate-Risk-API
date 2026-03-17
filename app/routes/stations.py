from fastapi import APIRouter, Depends, HTTPException
import asyncpg

from app.models.schemas import StationOut, StationCreate, StationUpdate
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


@router.post("", response_model=StationOut, status_code=201,
             summary="Create a monitoring station",
             description="Creates a new air quality monitoring station. Requires admin token.")
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


@router.put("/{station_id}", response_model=StationOut,
            summary="Update a monitoring station",
            description="Updates one or more fields of an existing station. Requires admin token.")
async def update_station(
    station_id: str,
    payload: StationUpdate,
    _: TokenPayload = Depends(require_admin),
):
    from main import app

    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No fields provided to update")

    set_clause = ", ".join(f"{col} = ${i + 2}" for i, col in enumerate(updates))
    values = list(updates.values())

    async with app.state.pool.acquire() as conn:
        row = await conn.fetchrow(
            f"""
            UPDATE stations_uk
            SET {set_clause}
            WHERE station_id = $1
            RETURNING station_id, city, country, lat, lon, source
            """,
            station_id, *values
        )

    if not row:
        raise HTTPException(status_code=404, detail="Station not found")

    return dict(row)


@router.delete("/{station_id}", status_code=204,
               summary="Delete a monitoring station",
               description="Deletes a station and all associated observations (cascade). Requires admin token.")
async def delete_station(
    station_id: str,
    _: TokenPayload = Depends(require_admin),
):
    from main import app

    async with app.state.pool.acquire() as conn:
        result = await conn.execute(
            "DELETE FROM stations_uk WHERE station_id = $1;",
            station_id
        )

    if result == "DELETE 0":
        raise HTTPException(status_code=404, detail="Station not found")