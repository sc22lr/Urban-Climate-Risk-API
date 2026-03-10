from fastapi.testclient import TestClient
from main import app


def test_root():
    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


def test_list_stations():
    with TestClient(app) as client:
        response = client.get("/stations")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


def test_observations_endpoint():
    with TestClient(app) as client:
        response = client.get("/observations?limit=5")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


def test_trends_endpoint():
    with TestClient(app) as client:
        response = client.get("/analytics/trends?station_id=london_uk&metric=pm25")
        assert response.status_code == 200
        data = response.json()
        assert "points" in data


def test_compare_endpoint():
    with TestClient(app) as client:
        response = client.get("/analytics/compare?metric=pm25")
        assert response.status_code == 200
        data = response.json()
        assert "stations" in data