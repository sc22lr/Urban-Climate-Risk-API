import pandas as pd
import uuid
from pathlib import Path

INPUT = Path("global_air_quality_data_10000.csv")
OUT_STATIONS = Path("stations.csv")
OUT_OBS = Path("observations.csv")

def norm_cols(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = (
        df.columns.str.strip()
        .str.lower()
        .str.replace(" ", "_")
        .str.replace(".", "_", regex=False)
        .str.replace("__", "_")
    )
    return df

def pick_first(df, candidates):
    for c in candidates:
        if c in df.columns:
            return c
    return None

df = pd.read_csv(INPUT)
df = norm_cols(df)

# Map likely columns (edit if your Kaggle file differs)
col_city = pick_first(df, ["city", "location", "town"])
col_country = pick_first(df, ["country", "country_code"])
col_time = pick_first(df, ["date", "datetime", "timestamp", "time"])

# Pollutants (accept multiple naming styles)
col_pm25 = pick_first(df, ["pm2_5", "pm25", "pm2_5_ugm3"])
col_pm10 = pick_first(df, ["pm10", "pm10_ugm3"])
col_no2  = pick_first(df, ["no2", "nitrogen_dioxide"])
col_so2  = pick_first(df, ["so2", "sulfur_dioxide", "sulphur_dioxide"])
col_co   = pick_first(df, ["co", "carbon_monoxide"])
col_o3   = pick_first(df, ["o3", "ozone"])
col_aqi  = pick_first(df, ["aqi", "air_quality_index"])

required = [col_city, col_time]
missing = [name for name, col in [("city", col_city), ("time", col_time)] if col is None]
if missing:
    raise ValueError(f"Missing required columns: {missing}. Open the CSV and adjust the mapping section.")

# Parse time
df[col_time] = pd.to_datetime(df[col_time], errors="coerce", utc=True)
df = df.dropna(subset=[col_time, col_city])

# Build station_id from city+country (country optional)
def make_station_id(row):
    city = str(row[col_city]).strip().lower().replace(" ", "_")
    country = str(row[col_country]).strip().lower() if col_country else "xx"
    return f"{city}_{country}"

df["station_id"] = df.apply(make_station_id, axis=1)

# Keep only relevant columns
keep = ["station_id", col_city, col_country, col_time, col_pm25, col_pm10, col_no2, col_so2, col_co, col_o3, col_aqi]
keep = [c for c in keep if c is not None]
df2 = df[keep].copy()

# Rename to your canonical schema
rename_map = {
    col_city: "city",
    col_country: "country",
    col_time: "observed_at_utc",
    col_pm25: "pm25",
    col_pm10: "pm10",
    col_no2: "no2",
    col_so2: "so2",
    col_co: "co",
    col_o3: "o3",
    col_aqi: "aqi",
}
df2 = df2.rename(columns={k:v for k,v in rename_map.items() if k is not None})

# Basic cleaning rules
for x in ["pm25", "pm10", "no2", "so2", "co", "o3"]:
    if x in df2.columns:
        df2.loc[df2[x] < 0, x] = pd.NA  # no negative pollution

# If AQI is present and not integer-ish, coerce
if "aqi" in df2.columns:
    df2["aqi"] = pd.to_numeric(df2["aqi"], errors="coerce")

# Build stations.csv (no lat/lon in Kaggle file typically)
stations = (
    df2[["station_id", "city"] + (["country"] if "country" in df2.columns else [])]
    .drop_duplicates()
    .assign(lat=pd.NA, lon=pd.NA, source="kaggle")
)

# Build observations.csv
obs = df2.copy()
obs.insert(0, "observation_id", [uuid.uuid4() for _ in range(len(obs))])
obs["source"] = "kaggle"

# Order columns exactly
stations_cols = ["station_id", "city", "country", "lat", "lon", "source"]
stations = stations.reindex(columns=[c for c in stations_cols if c in stations.columns])

obs_cols = ["observation_id","station_id","observed_at_utc","pm25","pm10","no2","so2","co","o3","aqi","source"]
obs = obs.reindex(columns=[c for c in obs_cols if c in obs.columns])

stations.to_csv(OUT_STATIONS, index=False)
obs.to_csv(OUT_OBS, index=False)

print("Wrote:", OUT_STATIONS, "and", OUT_OBS)