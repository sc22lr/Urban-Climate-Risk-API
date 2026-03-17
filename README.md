# Urban Climate Risk & Anomaly Intelligence API

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-API-green)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Database-blue)
![Tests](https://img.shields.io/badge/tests-pytest-success)
![License](https://img.shields.io/badge/license-academic-lightgrey)

A RESTful API for analysing urban air quality data across the United Kingdom. The system ingests pollution data from the OpenWeather Air Pollution API, stores observations in PostgreSQL, and provides environmental analytics including risk scoring, anomaly detection, trend analysis, and cross-city station comparison.

Developed as part of the COMP3011 Web Services & Web Data coursework assignment.

---

## Features

- Real-time air quality data ingestion from the OpenWeather API
- Full CRUD for monitoring stations across UK cities
- Storage of pollution observations (PM2.5, PM10, NO₂, SO₂, CO, O₃) in PostgreSQL
- Environmental risk scoring (PM2.5, NO₂, O₃ weighted formula, 0–100 scale)
- Anomaly detection using z-score statistical thresholds
- Pollution trend analysis with min/max/average statistics
- Cross-city station comparison by pollutant
- JWT authentication for protected admin endpoints
- Auto-generated interactive API documentation (Swagger UI)
- Automated API tests using pytest

---

## Technology Stack

| Technology        | Purpose                                      |
| ----------------- | -------------------------------------------- |
| FastAPI           | REST API framework with auto OpenAPI docs    |
| PostgreSQL        | Relational database for stations & observations |
| asyncpg           | Asynchronous PostgreSQL driver               |
| httpx             | Async HTTP client for external API requests  |
| Pydantic          | Data validation and request/response schemas |
| python-jose       | JWT token creation and verification          |
| pytest            | Automated endpoint testing                   |
| OpenWeather API   | Live air pollution data source               |

---

## Project Structure

```
app/
├── core/
│   └── auth.py              # JWT authentication and role enforcement
├── db/
│   └── database.py          # asyncpg connection pool management
├── models/
│   └── schemas.py           # Pydantic request/response schemas
├── routes/
│   ├── auth.py              # Token generation endpoint
│   ├── stations.py          # Station CRUD endpoints
│   ├── observations.py      # Observation query endpoints
│   ├── analytics.py         # Risk score, anomaly, trend, compare endpoints
│   ├── ingestion.py         # OpenWeather data ingestion endpoint
│   └── system.py            # Root and health check endpoints
└── services/
    └── openweather.py       # OpenWeather geocoding and pollution API client

scripts/
└── ingest_uk_cities.py      # Batch ingestion script for 40 UK cities

tests/
└── test_api.py              # Automated API tests (14 tests)

main.py                      # Application entry point
mcp_server.py                # MCP server for AI assistant integration
Climate.sql                  # Database schema (run this first)
requirements.txt             # Python dependencies
```

---

## Live Deployment

The API is live on Render.com:

| | URL |
|---|---|
| **API** | https://urban-climate-risk-api.onrender.com |
| **Swagger UI** | https://urban-climate-risk-api.onrender.com/docs |

> **Note:** The free tier spins down after inactivity — the first request may take 30–60 seconds to wake up.

---

## Local Installation & Setup

### 1. Clone the repository

```bash
git clone https://github.com/sc22lr/Urban-Climate-Risk-API
cd Urban-Climate-Risk-API
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set up environment variables

Create a `.env` file in the project root with the following:

```env
OPENWEATHER_API_KEY=your_openweather_api_key

PGUSER=postgres
PGPASSWORD=your_postgres_password
PGDATABASE=climate_api
PGHOST=localhost
PGPORT=5432

JWT_SECRET=your_secret_key
JWT_ALG=HS256
```

You can obtain a free OpenWeather API key at https://openweathermap.org/api.

### 4. Create the database

Create the PostgreSQL database and run the schema:

```bash
psql -U postgres -c "CREATE DATABASE climate_api;"
psql -U postgres -d climate_api -f Climate.sql
```

This creates the `stations_uk` and `observations_uk` tables with the required indexes.

### 5. Seed the database (optional)

To pre-populate the database with pollution data for 40 UK cities, start the API first (step 6), then run:

```bash
python scripts/ingest_uk_cities.py
```

This calls the ingestion endpoint for each city, geocodes it via OpenWeather, and stores live pollution measurements. Each request is rate-limited to one per second.

> **Note:** The `.csv` data files used during development are excluded from the repository (`.gitignore`). Use the ingestion script above to populate the database from the live OpenWeather API.

### 6. Start the API

```bash
uvicorn main:app --reload
```

The API will be available at:

```
http://127.0.0.1:8000
```

Interactive Swagger documentation:

```
http://127.0.0.1:8000/docs
```

---

## Running Tests

```bash
pytest tests/test_api.py -v
```

The test suite contains 18 automated tests covering endpoint behaviour, status codes, response structure, authentication, and edge cases.

> **Note:** The test `test_ingest_with_valid_admin_token` makes a live call to the OpenWeather API. Ensure your `.env` file is configured with a valid API key before running tests.

---

## API Endpoints

### System

| Method | Endpoint  | Description              | Auth     |
| ------ | --------- | ------------------------ | -------- |
| GET    | `/`       | API root                 | Public   |
| GET    | `/health` | Database health check    | Public   |

### Authentication

| Method | Endpoint          | Description                    | Auth   |
| ------ | ----------------- | ------------------------------ | ------ |
| POST   | `/auth/dev-token` | Generate JWT token (dev only)  | Public |

### Stations

| Method | Endpoint               | Description                   | Auth   |
| ------ | ---------------------- | ----------------------------- | ------ |
| GET    | `/stations`            | List all monitoring stations  | Public |
| POST   | `/stations`            | Create a new station          | Admin  |
| PUT    | `/stations/{id}`       | Update an existing station    | Admin  |
| DELETE | `/stations/{id}`       | Delete a station (cascade)    | Admin  |

### Observations

| Method | Endpoint         | Description                              | Auth   |
| ------ | ---------------- | ---------------------------------------- | ------ |
| GET    | `/observations`  | Retrieve observations (filter by station) | Public |

### Analytics

| Method | Endpoint                   | Description                                  | Auth   |
| ------ | -------------------------- | -------------------------------------------- | ------ |
| GET    | `/analytics/risk-score`    | Environmental risk score for a station       | Public |
| GET    | `/analytics/anomalies`     | Z-score anomaly detection for a pollutant    | Public |
| GET    | `/analytics/trends`        | Time-series trend analysis for a pollutant   | Public |
| GET    | `/analytics/compare`       | Cross-city pollutant comparison              | Public |
| GET    | `/analytics/summary`       | Dataset-wide summary statistics              | Public |

### Ingestion

| Method | Endpoint                | Description                              | Auth  |
| ------ | ----------------------- | ---------------------------------------- | ----- |
| POST   | `/ingest/openweather`   | Ingest live pollution data for a city    | Admin |

---

## Risk Score Formula

The `/analytics/risk-score` endpoint computes a weighted score (0–100) from the three pollutants with the strongest health evidence:

```
score = (pm25 / 50) × 50 + (no2 / 100) × 30 + (o3 / 100) × 20
score = min(score, 100)
```

| Band    | Score Range | Meaning                        |
| ------- | ----------- | ------------------------------ |
| Low     | 0 – 33      | Air quality within normal range |
| Medium  | 34 – 66     | Elevated — sensitive groups affected |
| High    | 67 – 100    | Poor — general population at risk |

---

## Example Requests

**Ingest pollution data for a city:**
```bash
# First get a token
curl -X POST "http://127.0.0.1:8000/auth/dev-token?role=admin"

# Then ingest
curl -X POST "http://127.0.0.1:8000/ingest/openweather?city=London" \
  -H "Authorization: Bearer <your-token>"
```

**Get risk score for a station:**
```bash
curl "http://127.0.0.1:8000/analytics/risk-score?station_id=london_uk"
```

**Detect anomalies:**
```bash
curl "http://127.0.0.1:8000/analytics/anomalies?station_id=london_uk&metric=pm25&threshold=2.0"
```

---

## MCP Server

The API includes an MCP (Model Context Protocol) server that exposes air quality tools for AI assistants such as Claude.

### Available Tools

| Tool | Description |
| ---- | ----------- |
| `get_stations` | List all monitoring stations |
| `get_observations` | Retrieve pollution observations |
| `get_risk_score` | Environmental risk score for a station |
| `detect_anomalies` | Z-score anomaly detection for a pollutant |
| `get_trends` | Time-series trend analysis |
| `compare_stations` | Cross-city pollutant comparison |
| `get_dataset_summary` | Dataset-wide summary statistics |

### Running the MCP Server

Start the API first, then in a separate terminal:

```bash
# Local
python mcp_server.py

# Against live deployment
API_BASE_URL=https://urban-climate-risk-api.onrender.com python mcp_server.py
```

---

## API Documentation

Full interactive documentation is available at `/docs` (Swagger UI) once the server is running. A PDF export of the API documentation is included in the repository root.

---

## Author

Developed for the COMP3011 Web Services & Web Data module coursework.