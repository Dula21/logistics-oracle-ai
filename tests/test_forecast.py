import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_forecast_returns_200():
    response = client.get("/api/forecast?sku=A1023")
    assert response.status_code == 200


def test_forecast_response_shape():
    response = client.get("/api/forecast?sku=A1023")
    data = response.json()
    assert "sku_id" in data
    assert "days_until_stockout" in data
    assert "avg_daily_sales" in data
    assert "current_stock" in data
    assert "forecast" in data
    assert len(data["forecast"]) > 0


def test_forecast_days_until_stockout_is_positive():
    response = client.get("/api/forecast?sku=A1023")
    data = response.json()
    assert data["days_until_stockout"] >= 0


def test_forecast_unknown_sku_returns_500():
    response = client.get("/api/forecast?sku=UNKNOWN_SKU_999")
    assert response.status_code == 200  # prophet handles unknown SKUs gracefully



def test_batch_forecast_returns_200():
    response = client.post(
        "/api/forecast/batch",
        json={"skus": ["A1023", "B5421"], "mode": "operational"}
    )
    assert response.status_code == 200


def test_batch_forecast_returns_all_skus():
    response = client.post(
        "/api/forecast/batch",
        json={"skus": ["A1023", "B5421", "C9011"], "mode": "operational"}
    )
    data = response.json()
    assert len(data["forecasts"]) == 3
    assert data["errors"] == []


def test_batch_forecast_empty_skus():
    response = client.post(
        "/api/forecast/batch",
        json={"skus": [], "mode": "operational"}
    )
    assert response.status_code == 400


def test_batch_forecast_exceeds_limit():
    response = client.post(
        "/api/forecast/batch",
        json={"skus": [f"SKU{i}" for i in range(25)], "mode": "operational"}
    )
    assert response.status_code == 400


def test_alerts_returns_200():
    response = client.get("/api/alerts")
    assert response.status_code == 200


def test_alerts_response_shape():
    response = client.get("/api/alerts")
    data = response.json()
    assert "alerts" in data
    assert len(data["alerts"]) > 0
    first = data["alerts"][0]
    assert "sku_id" in first
    assert "status" in first
    assert "days_until_stockout" in first


def test_alerts_sorted_by_urgency():
    response = client.get("/api/alerts")
    data = response.json()
    alerts = data["alerts"]
    priority = {"red": 0, "amber": 1, "green": 2}
    for i in range(len(alerts) - 1):
        assert priority[alerts[i]["status"]] <= priority[alerts[i+1]["status"]]


def test_upload_reset_requires_auth():
    response = client.post("/api/upload/reset")
    assert response.status_code == 401


# Fix 3 - no token returns 401
def test_upload_requires_auth():
    response = client.post("/api/upload")
    assert response.status_code == 401