from fastapi.testclient import TestClient
from app.main import app


def test_root_endpoint():
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Self-Hosted AI Platform" in response.text


def test_favicon_endpoint():
    client = TestClient(app)
    response = client.get("/favicon.ico")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/svg+xml"
    assert "<svg" in response.text
