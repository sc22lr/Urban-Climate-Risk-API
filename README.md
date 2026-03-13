# Urban Climate Risk & Anomaly Intelligence API

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-API-green)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Database-blue)
![Tests](https://img.shields.io/badge/tests-pytest-success)
![License](https://img.shields.io/badge/license-academic-lightgrey)

A RESTful API for analysing urban air quality data across the United Kingdom.
The system ingests pollution data from external sources, stores observations in PostgreSQL, and provides environmental analytics including risk scoring, anomaly detection, and trend analysis.

This project was developed as part of a Web Services coursework assignment.

## Features

- Air quality data ingestion from the OpenWeather API
- Storage of environmental observations in PostgreSQL
- Environmental risk scoring
- Anomaly detection using statistical thresholds
- Trend analysis for pollution metrics
- Station comparison across cities
- JWT authentication for protected endpoints
- Modular FastAPI architecture
- Automated API tests using pytest

## Technology Stack

| Technology        | Purpose                        |
| ----------------- | ------------------------------ |
| FastAPI           | REST API framework             |
| PostgreSQL        | Relational database            |
| asyncpg           | Asynchronous PostgreSQL driver |
| httpx             | External API requests          |
| Pydantic          | Data validation and schemas    |
| JWT (python-jose) | Authentication                 |
| pytest            | Automated testing              |
| OpenWeather API   | Air pollution data source      |

## Project Architecture

app/
│
├── core/
│   └── auth.py              # Authentication logic
│
├── db/
│   └── database.py          # PostgreSQL connection pool
│
├── models/
│   └── schemas.py           # Pydantic request/response models
│
├── routes/
│   ├── auth.py              # Authentication endpoints
│   ├── stations.py          # Station management
│   ├── observations.py      # Observation queries
│   ├── analytics.py         # Risk, anomaly, and trend analysis
│   ├── ingestion.py         # External data ingestion
│   └── system.py            # Root and health endpoints
│
├── services/
│   └── openweather.py       # OpenWeather API integration
│
tests/
│   └── test_api.py          # API endpoint tests
│
main.py                      # Application entry point
requirements.txt             # Project dependencies
README.md                    # Project documentation

The architecture separates concerns into routes, services, models, database access, and core logic, improving maintainability and scalability.

## Installation

Clone the repository:
```bash 
git clone <repository-url>
cd web-services
```

Install dependencies:
```bash 
pip install -r requirements.txt
```

## Environment Variables

Create a .env file in the project root:
```env
OPENWEATHER_API_KEY=your_openweather_key

PGUSER=postgres
PGPASSWORD=your_password
PGDATABASE=climate_api
PGHOST=localhost
PGPORT=5432

JWT_SECRET=your_secret_key
```

## Running the API

Start the FastAPI server:
```bash
uvicorn main:app --reload
```

The API will run at:
```bash
http://127.0.0.1:8000
```

Interactive API documentation:
```bash
http://127.0.0.1:8000/docs
```

## Running Tests

Run the automated test suite:
```bash
pytest
```
The tests verify the behaviour of key API endpoints.

## Example Endpoints

| Endpoint                   | Description                            |
| -------------------------- | -------------------------------------- |
| `GET /`                    | API root                               |
| `GET /health`              | System health check                    |
| `GET /stations`            | Retrieve monitoring stations           |
| `POST /stations`           | Create a new station                   |
| `GET /observations`        | Retrieve pollution observations        |
| `GET /risk/score`          | Calculate environmental risk score     |
| `GET /analytics/anomalies` | Detect pollution anomalies             |
| `GET /analytics/trends`    | Pollution trend analysis               |
| `GET /analytics/compare`   | Compare stations                       |
| `POST /ingest/openweather` | Ingest pollution data from OpenWeather |

## Example Request

Example ingestion request:
```bash
POST /ingest/openweather?city=London
```

Example response:
```json
{
  "station_id": "london_uk",
  "city": "London",
  "lat": 51.5074,
  "lon": -0.1278,
  "pm25": 12.4,
  "pm10": 18.1,
  "risk_score": 32.5,
  "category": "Low"
}
```

## Author

Developed for the Web Services module coursework.