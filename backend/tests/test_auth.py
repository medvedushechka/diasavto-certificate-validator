from fastapi.testclient import TestClient

from app import app


def test_upload_does_not_require_authentication() -> None:
    response = TestClient(app).post(
        "/api/generation/plan",
        files={"certificate": ("rules.txt", b"4VB****", "text/plain")},
    )
    assert response.status_code == 200
    assert response.json()["masks"] == ["4VB****"]
