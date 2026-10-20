from fastapi.testclient import TestClient

from app import app


def test_health() -> None:
    response = TestClient(app).get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_upload_without_login() -> None:
    response = TestClient(app).post(
        "/api/generation/plan",
        files={"certificate": ("rules.txt", b"4VB****", "text/plain")},
    )
    assert response.status_code == 200
    assert response.json()["masks"] == ["4VB****"]
