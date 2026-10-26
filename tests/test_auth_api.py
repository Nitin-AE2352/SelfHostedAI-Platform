import uuid

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def make_user():
    return "test_" + uuid.uuid4().hex[:12], "StrongTest123!"


def test_register_login_and_access_protected_endpoint():
    username, password = make_user()

    response = client.post(
        "/api/v1/auth/register",
        json={"username": username, "password": password},
    )
    assert response.status_code == 201

    response = client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password},
    )
    assert response.status_code == 200

    token = response.json()["access_token"]
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["user"]["username"] == username


def test_wrong_password_is_rejected():
    username, password = make_user()
    client.post(
        "/api/v1/auth/register",
        json={"username": username, "password": password},
    )

    response = client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": "WrongPassword123!"},
    )
    assert response.status_code == 401


def test_duplicate_username_is_rejected():
    username, password = make_user()
    payload = {"username": username, "password": password}

    first_response = client.post("/api/v1/auth/register", json=payload)
    second_response = client.post("/api/v1/auth/register", json=payload)

    assert first_response.status_code == 201
    assert second_response.status_code == 409


def test_protected_endpoint_rejects_missing_token():
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
