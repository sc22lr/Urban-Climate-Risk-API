import os

import asyncpg


async def startup(app):
    database_url = os.getenv("DATABASE_URL")

    if database_url:
        # Render provides a postgres:// URL — asyncpg needs postgresql://
        database_url = database_url.replace("postgres://", "postgresql://", 1)
        app.state.pool = await asyncpg.create_pool(
            dsn=database_url,
            min_size=1,
            max_size=5,
        )
    else:
        # Local development — use individual environment variables
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