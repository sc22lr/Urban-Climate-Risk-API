from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class LoginOut(BaseModel):
    token: str


class IngestResult(BaseModel):
    station_id: str
    city: str
    country: str = "UK"
    lat: float
    lon: float
    observed_at_utc: datetime
    pm25: Optional[float] = None
    pm10: Optional[float] = None
    no2: Optional[float] = None
    so2: Optional[float] = None
    co: Optional[float] = None
    o3: Optional[float] = None
    inserted: bool = Field(..., description="True if a new observation row was inserted; false if deduped by unique constraint")

    class Config:
        json_schema_extra = {
            "example": {
                "station_id": "manchester_uk",
                "city": "Manchester",
                "country": "UK",
                "lat": 53.4808,
                "lon": -2.2426,
                "observed_at_utc": "2026-03-13T12:00:00Z",
                "pm25": 11.7,
                "pm10": 18.3,
                "no2": 9.6,
                "so2": 1.5,
                "co": 210.2,
                "o3": 71.4,
                "inserted": True
            }
        }

class StationOut(BaseModel):
    station_id: str
    city: str
    country: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    source: str


class StationCreate(BaseModel):
    station_id: str
    city: str
    country: str = "UK"
    lat: Optional[float] = None
    lon: Optional[float] = None
    source: str = "manual"

    class Config:
        json_schema_extra = {
            "example": {
                "station_id": "leeds_uk",
                "city": "Leeds",
                "country": "UK",
                "lat": 53.8008,
                "lon": -1.5491,
                "source": "manual"
            }
        }


class StationUpdate(BaseModel):
    city: Optional[str] = None
    country: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    source: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "city": "Leeds",
                "country": "UK",
                "lat": 53.8008,
                "lon": -1.5491,
                "source": "manual"
            }
        }


class ObservationOut(BaseModel):
    observation_id: UUID
    station_id: str
    observed_at_utc: datetime
    pm25: Optional[float] = None
    pm10: Optional[float] = None
    no2: Optional[float] = None
    so2: Optional[float] = None
    co: Optional[float] = None
    o3: Optional[float] = None
    source: str


class RiskScoreOut(BaseModel):
    station_id: str
    observed_at_utc: datetime
    pm25: Optional[float]
    no2: Optional[float]
    o3: Optional[float]
    risk_score: float
    category: str

    class Config:
        json_schema_extra = {
            "example": {
                "station_id": "london_uk",
                "observed_at_utc": "2023-12-25T00:00:00Z",
                "pm25": 42.5,
                "no2": 31.8,
                "o3": 67.4,
                "risk_score": 53.26,
                "category": "Medium"
            }
        }


class AnomalyItem(BaseModel):
    observation_id: UUID
    station_id: str
    observed_at_utc: datetime
    metric: str
    value: float
    z_score: float


class AnomalyResponse(BaseModel):
    station_id: str
    metric: str
    threshold: float
    mean: float
    std_dev: float
    anomalies: list[AnomalyItem]


class TrendPoint(BaseModel):
    observed_at_utc: datetime
    value: float


class TrendResponse(BaseModel):
    station_id: str
    metric: str
    points: list[TrendPoint]
    min_value: float
    max_value: float
    avg_value: float


class CompareItem(BaseModel):
    station_id: str
    city: str
    metric: str
    avg_value: float
    min_value: float
    max_value: float
    observation_count: int


class CompareResponse(BaseModel):
    metric: str
    stations: list[CompareItem]