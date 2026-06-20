import pytest
from fastapi.testclient import TestClient
from main import app
import uuid

client = TestClient(app)


# ── Helper: register a throwaway user and return their token ──────────
def register_user(role="manager"):
    email = f"test_{uuid.uuid4().hex[:8]}@test.com"
    response = client.post(
        "/auth/register",
        data={"username": email, "password": "testpass123", "role": role}
    )
    return response, email


# ── Registration ────────────────────────────────────────────────────
def test_register_creates_user():
    response, email = register_user(role="manager")
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["role"] == "manager"


def test_register_duplicate_email_fails():
    response1, email = register_user(role="manager")
    assert response1.status_code == 200

    response2 = client.post(
        "/auth/register",
        data={"username": email, "password": "testpass123", "role": "manager"}
    )
    assert response2.status_code == 400


def test_register_invalid_role_defaults_to_manager():
    response, email = register_user(role="superuser_hack_attempt")
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "manager"


def test_register_warehouse_role():
    response, email = register_user(role="warehouse")
    assert response.status_code == 200
    assert response.json()["role"] == "warehouse"


def test_register_finance_role():
    response, email = register_user(role="finance")
    assert response.status_code == 200
    assert response.json()["role"] == "finance"


# ── Login ────────────────────────────────────────────────────────────
def test_login_with_correct_credentials():
    _, email = register_user(role="manager")
    response = client.post(
        "/auth/login",
        data={"username": email, "password": "testpass123"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_login_with_wrong_password_fails():
    _, email = register_user(role="manager")
    response = client.post(
        "/auth/login",
        data={"username": email, "password": "wrongpassword"}
    )
    assert response.status_code == 401


def test_login_with_nonexistent_email_fails():
    response = client.post(
        "/auth/login",
        data={"username": "doesnotexist@nowhere.com", "password": "anything"}
    )
    assert response.status_code == 401


# ── RBAC: upload endpoint ───────────────────────────────────────────
def test_upload_blocked_without_token():
    response = client.post("/api/upload")
    assert response.status_code == 401


def test_upload_blocked_for_manager_role():
    register_response, _ = register_user(role="manager")
    token = register_response.json()["access_token"]
    response = client.post(
        "/api/upload",
        headers={"Authorization": f"Bearer {token}"}
    )
    # 403 = authenticated but wrong role (not 401)
    assert response.status_code == 403


def test_upload_blocked_for_warehouse_role():
    register_response, _ = register_user(role="warehouse")
    token = register_response.json()["access_token"]
    response = client.post(
        "/api/upload",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403


def test_reset_blocked_without_token():
    response = client.post("/api/upload/reset")
    assert response.status_code == 401


def test_reset_blocked_for_finance_role():
    register_response, _ = register_user(role="finance")
    token = register_response.json()["access_token"]
    response = client.post(
        "/api/upload/reset",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403


# ── Invalid token handling ──────────────────────────────────────────
def test_garbage_token_returns_401():
    response = client.post(
        "/api/upload/reset",
        headers={"Authorization": "Bearer this.is.not.a.valid.jwt"}
    )
    assert response.status_code == 401


def test_missing_bearer_prefix_returns_401():
    register_response, _ = register_user(role="manager")
    token = register_response.json()["access_token"]
    response = client.post(
        "/api/upload/reset",
        headers={"Authorization": token}  # missing "Bearer " prefix
    )
    assert response.status_code in (401, 403)


# ── History endpoints require auth ──────────────────────────────────
def test_history_get_blocked_without_token():
    response = client.get("/api/history")
    assert response.status_code == 401


def test_history_save_blocked_without_token():
    response = client.post("/api/history/save", json={
        "sku_id": "TEST",
        "stock": 10,
        "days_until_stockout": 5,
        "avg_daily_sales": 2.0,
        "advice": "test advice",
        "status": "WARNING"
    })
    assert response.status_code == 401


def test_history_save_works_with_valid_token():
    register_response, _ = register_user(role="manager")
    token = register_response.json()["access_token"]
    response = client.post(
        "/api/history/save",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "sku_id": "TEST_SKU",
            "stock": 100,
            "days_until_stockout": 10,
            "avg_daily_sales": 5.0,
            "advice": "test advice",
            "status": "SECURE"
        }
    )
    assert response.status_code == 200
    assert "id" in response.json()