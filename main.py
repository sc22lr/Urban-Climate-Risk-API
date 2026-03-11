import os

from dotenv import load_dotenv
from fastapi import FastAPI

from app.db.database import shutdown, startup
from app.routes import auth, stations, observations, analytics, ingestion

load_dotenv()

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
if not OPENWEATHER_API_KEY:
    raise RuntimeError("OPENWEATHER_API_KEY missing in .env")

app = FastAPI(
    title="Urban Climate Risk & Anomaly Intelligence API (UK)",
    description="A UK-focused environmental analytics API providing climate risk scoring, anomaly detection, trend analysis, station comparison, and live air-quality ingestion from OpenWeather.",
    version="1.0.0",
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

app.include_router(auth.router)
app.include_router(stations.router)
app.include_router(observations.router)
app.include_router(analytics.router)
app.include_router(ingestion.router)