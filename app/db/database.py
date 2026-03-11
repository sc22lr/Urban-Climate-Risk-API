import os

import asyncpg


async def startup(app):
    app.state.pool = await asyncpg.create_pool(
        user=os.getenv("PGUSER", "postgres"),
        password=os.getenv("PGPASSWORD"),
        database=os.getenv("PGDATABASE", "climate_api"),
        host=os.getenv("PGHOST", "localhost"),
        port=int(os.getenv("PGPORT", "5432")),
        min_size=1,
        max_size=5,
    )


async def shutdown(app):
    await app.state.pool.close()