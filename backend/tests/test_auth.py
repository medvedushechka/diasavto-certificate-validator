from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


def test_upload_requires_authentication() -> None:
    response = client.post(
        "/api/generation/plan",
        files={"certificate": ("rules.txt", b"4VB****", "text/plain")},
    )
    assert response.status_code == 401
