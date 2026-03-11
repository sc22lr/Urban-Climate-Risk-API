from fastapi import APIRouter

router = APIRouter(tags=["System"])


@router.get("/")
def root():
    return {"status": "ok", "docs": "/docs"}


@router.get("/health")
async def health():
    from main import app

    async with app.state.pool.acquire() as conn:
        station_count = await conn.fetchval("SELECT COUNT(*) FROM stations_uk;")
        observation_count = await conn.fetchval("SELECT COUNT(*) FROM observations_uk;")

    return {
        "status": "ok",
        "database": "connected",
        "stations_uk": station_count,
        "observations_uk": observation_count,
    }