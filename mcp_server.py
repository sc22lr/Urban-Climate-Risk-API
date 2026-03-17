"""
Urban Climate Risk & Anomaly Intelligence API — MCP Server

Exposes key API endpoints as MCP tools so AI assistants (e.g. Claude)
can query UK air quality data directly.

Usage:
    python mcp_server.py

The API must be running at the URL set by API_BASE_URL (default: http://127.0.0.1:8000).
For the deployed version, set the environment variable:
    API_BASE_URL=https://urban-climate-risk-api.onrender.com python mcp_server.py
"""

import os
import httpx
from mcp.server.fastmcp import FastMCP

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")

mcp = FastMCP(
    name="Urban Climate Risk API",
    instructions=(
        "Tools for querying UK urban air quality data. "
        "Use get_stations to discover available station IDs before calling "
        "other tools that require a station_id parameter."
    ),
)


def _client() -> httpx.Client:
    return httpx.Client(base_url=API_BASE_URL, timeout=15)


# ── Tool 1: List all monitoring stations ─────────────────────────────────────

@mcp.tool()
def get_stations() -> list[dict]:
    """
    Returns all registered UK air quality monitoring stations.
    Each station has a station_id, city, country, lat, lon, and source.
    Use the station_id values returned here when calling other tools.
    """
    with _client() as client:
        response = client.get("/stations")
        response.raise_for_status()
        return response.json()


# ── Tool 2: Get pollution observations ───────────────────────────────────────

@mcp.tool()
def get_observations(station_id: str = None, limit: int = 10) -> list[dict]:
    """
    Returns stored air quality observations (PM2.5, PM10, NO2, SO2, CO, O3).

    Args:
        station_id: Optional. Filter results to a specific station.
                    Use get_stations() to find valid station IDs.
        limit:      Number of observations to return (1–500). Default is 10.
    """
    params = {"limit": limit}
    if station_id:
        params["station_id"] = station_id

    with _client() as client:
        response = client.get("/observations", params=params)
        response.raise_for_status()
        return response.json()


# ── Tool 3: Environmental risk score ─────────────────────────────────────────

@mcp.tool()
def get_risk_score(station_id: str) -> dict:
    """
    Calculates an environmental risk score (0–100) for a station based on
    its most recent pollution observation.

    The score uses PM2.5 (up to 50 pts), NO2 (up to 30 pts), and O3 (up to 20 pts).
    Categories: Low (0–33), Medium (34–66), High (67–100).

    Args:
        station_id: The station to score. Use get_stations() to find valid IDs.
    """
    with _client() as client:
        response = client.get("/analytics/risk-score", params={"station_id": station_id})
        response.raise_for_status()
        return response.json()


# ── Tool 4: Anomaly detection ─────────────────────────────────────────────────

@mcp.tool()
def detect_anomalies(
    station_id: str,
    metric: str = "pm25",
    threshold: float = 2.0,
) -> dict:
    """
    Detects anomalous pollution readings for a station using z-score analysis.
    Returns observations that deviate beyond the threshold from the mean.

    Args:
        station_id: The station to analyse. Use get_stations() to find valid IDs.
        metric:     Pollutant to analyse. One of: pm25, pm10, no2, so2, co, o3.
                    Default is pm25.
        threshold:  Z-score threshold for anomaly detection (0.5–5.0).
                    Default is 2.0 (±2 standard deviations).
    """
    with _client() as client:
        response = client.get(
            "/analytics/anomalies",
            params={"station_id": station_id, "metric": metric, "threshold": threshold},
        )
        response.raise_for_status()
        return response.json()


# ── Tool 5: Pollution trend analysis ─────────────────────────────────────────

@mcp.tool()
def get_trends(
    station_id: str,
    metric: str = "pm25",
    limit: int = 30,
) -> dict:
    """
    Returns a time-series of pollutant values for a station with summary
    statistics (min, max, average).

    Args:
        station_id: The station to analyse. Use get_stations() to find valid IDs.
        metric:     Pollutant to trend. One of: pm25, pm10, no2, so2, co, o3.
                    Default is pm25.
        limit:      Number of data points to return (1–365). Default is 30.
    """
    with _client() as client:
        response = client.get(
            "/analytics/trends",
            params={"station_id": station_id, "metric": metric, "limit": limit},
        )
        response.raise_for_status()
        return response.json()


# ── Tool 6: Cross-city station comparison ────────────────────────────────────

@mcp.tool()
def compare_stations(metric: str = "pm25") -> dict:
    """
    Compares all stations by average, minimum, and maximum pollutant levels.
    Results are ordered from highest to lowest average concentration.

    Args:
        metric: Pollutant to compare across stations.
                One of: pm25, pm10, no2, so2, co, o3. Default is pm25.
    """
    with _client() as client:
        response = client.get("/analytics/compare", params={"metric": metric})
        response.raise_for_status()
        return response.json()


# ── Tool 7: Dataset summary statistics ───────────────────────────────────────

@mcp.tool()
def get_dataset_summary() -> dict:
    """
    Returns overall statistics about the environmental dataset:
    total station count, total observation count, time range covered,
    and average pollutant levels (PM2.5, PM10, NO2) across all stations.
    """
    with _client() as client:
        response = client.get("/analytics/summary")
        response.raise_for_status()
        return response.json()


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print(f"Starting Urban Climate Risk MCP Server")
    print(f"Connecting to API at: {API_BASE_URL}")
    print(f"Tools available: get_stations, get_observations, get_risk_score,")
    print(f"                 detect_anomalies, get_trends, compare_stations,")
    print(f"                 get_dataset_summary")
    mcp.run()