from fastapi.testclient import TestClient
from main import app


def get_dev_token(client: TestClient) -> str:
    response = client.post("/auth/dev-token", params={"role": "admin"})
    assert response.status_code == 200
    data = response.json()
    assert "token" in data
    return data["token"]


def test_root():
    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


def test_health():
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data


def test_dev_token():
    with TestClient(app) as client:
        response = client.post("/auth/dev-token", params={"role": "admin"})
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert isinstance(data["token"], str)
        assert len(data["token"]) > 20


def test_list_stations():
    with TestClient(app) as client:
        response = client.get("/stations")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


def test_observations_endpoint():
    with TestClient(app) as client:
        response = client.get("/observations", params={"limit": 5})
        assert response.status_code == 200
        assert isinstance(response.json(), list)


def test_trends_endpoint():
    with TestClient(app) as client:
        response = client.get(
            "/analytics/trends",
            params={"station_id": "london_uk", "metric": "pm25"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "points" in data


def test_compare_endpoint():
    with TestClient(app) as client:
        response = client.get("/analytics/compare", params={"metric": "pm25"})
        assert response.status_code == 200
        data = response.json()
        assert "stations" in data


def test_summary_endpoint():
    with TestClient(app) as client:
        response = client.get("/analytics/summary")
        assert response.status_code == 200
        data = response.json()
        assert "stations" in data
        assert "observations" in data
        assert "avg_pm25" in data


def test_compare_invalid_metric():
    with TestClient(app) as client:
        response = client.get("/analytics/compare", params={"metric": "invalid_metric"})
        assert response.status_code in (400, 422)


def test_ingest_requires_token():
    with TestClient(app) as client:
        response = client.post("/ingest/openweather", params={"city": "Leeds"})
        assert response.status_code == 401


def test_ingest_rejects_invalid_token():
    with TestClient(app) as client:
        response = client.post(
            "/ingest/openweather",
            params={"city": "Leeds"},
            headers={"Authorization": "Bearer invalid-token"},
        )
        assert response.status_code == 401


def test_ingest_with_valid_admin_token():
    with TestClient(app) as client:
        token = get_dev_token(client)
        response = client.post(
            "/ingest/openweather",
            params={"city": "York"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["city"] == "York"
        assert "pm25" in data


def test_update_station_requires_token():
    with TestClient(app) as client:
        response = client.put(
            "/stations/london_uk",
            json={"city": "London Updated"},
        )
        assert response.status_code == 401


def test_update_station_not_found():
    with TestClient(app) as client:
        token = get_dev_token(client)
        response = client.put(
            "/stations/nonexistent_station_xyz",
            json={"city": "Nowhere"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404


def test_create_update_delete_station():
    with TestClient(app) as client:
        token = get_dev_token(client)
        headers = {"Authorization": f"Bearer {token}"}

        # Create
        create_resp = client.post(
            "/stations",
            json={
                "station_id": "test_station_comp3011",
                "city": "TestCity",
                "country": "UK",
                "lat": 52.0,
                "lon": -1.0,
                "source": "manual",
            },
            headers=headers,
        )
        assert create_resp.status_code == 201
        assert create_resp.json()["station_id"] == "test_station_comp3011"

        # Update
        update_resp = client.put(
            "/stations/test_station_comp3011",
            json={"city": "TestCityUpdated"},
            headers=headers,
        )
        assert update_resp.status_code == 200
        assert update_resp.json()["city"] == "TestCityUpdated"

        # Delete
        delete_resp = client.delete(
            "/stations/test_station_comp3011",
            headers=headers,
        )
        assert delete_resp.status_code == 204


def test_delete_station_not_found():
    with TestClient(app) as client:
        token = get_dev_token(client)
        response = client.delete(
            "/stations/nonexistent_station_xyz",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404

def test_risk_score_endpoint():
    with TestClient(app) as client:
        response = client.get(
            "/analytics/risk-score",
            params={"station_id": "london_uk"},
        )
        assert response.status_code == 200


def test_anomalies_endpoint():
    with TestClient(app) as client:
        response = client.get(
            "/analytics/anomalies",
            params={"station_id": "london_uk", "metric": "pm25"},
        )
        assert response.status_code == 200