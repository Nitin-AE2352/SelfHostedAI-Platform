from fastapi.testclient import TestClient
from app.main import app


def test_root_endpoint():
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Self-Hosted AI Platform" in response.text
