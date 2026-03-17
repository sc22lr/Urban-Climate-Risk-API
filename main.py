import os
from dotenv import load_dotenv
from fastapi import FastAPI
from app.db.database import shutdown, startup
from app.routes import auth, stations, observations, analytics, ingestion, system

load_dotenv() 
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
if not OPENWEATHER_API_KEY:
    raise RuntimeError("OPENWEATHER_API_KEY missing in .env")

tags_metadata = [
    {"name": "Auth", "description": "Authentication and token generation"},
    {"name": "Stations", "description": "Manage air quality monitoring stations"},
    {"name": "Observations", "description": "Retrieve air pollution observations"},
    {"name": "Analytics", "description": "Environmental analytics and anomaly detection"},
    {"name": "Ingestion", "description": "External air quality data ingestion"},
    {"name": "System", "description": "System-level operations and maintenance"}
]

app = FastAPI(
    title="Urban Climate Risk & Anomaly Intelligence API (UK)",
    description="API for analysing urban air quality data using environmental risk scoring, anomaly detection, and trend analysis.",
    version="1.0.0",
    openapi_tags=tags_metadata
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
app.include_router(system.router)