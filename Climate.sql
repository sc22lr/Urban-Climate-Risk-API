CREATE TABLE IF NOT EXISTS stations (
  station_id TEXT PRIMARY KEY,
  city       TEXT NOT NULL,
  country    TEXT,
  lat        DOUBLE PRECISION,
  lon        DOUBLE PRECISION,
  source     TEXT NOT NULL DEFAULT 'kaggle'
);

CREATE TABLE IF NOT EXISTS observations (
  observation_id UUID PRIMARY KEY,
  station_id      TEXT NOT NULL REFERENCES stations(station_id) ON DELETE CASCADE,
  observed_at_utc TIMESTAMPTZ NOT NULL,
  pm25 DOUBLE PRECISION,
  pm10 DOUBLE PRECISION,
  no2  DOUBLE PRECISION,
  so2  DOUBLE PRECISION,
  co   DOUBLE PRECISION,
  o3   DOUBLE PRECISION,
  source TEXT NOT NULL DEFAULT 'kaggle',
  CONSTRAINT uq_station_time UNIQUE (station_id, observed_at_utc)
);

CREATE INDEX IF NOT EXISTS idx_obs_station_time
ON observations(station_id, observed_at_utc DESC);

CREATE TEMP TABLE observations_temp (
  observation_id UUID,
  station_id TEXT,
  observed_at_utc TIMESTAMPTZ,
  pm25 DOUBLE PRECISION,
  pm10 DOUBLE PRECISION,
  no2 DOUBLE PRECISION,
  so2 DOUBLE PRECISION,
  co DOUBLE PRECISION,
  o3 DOUBLE PRECISION,
  source TEXT
);