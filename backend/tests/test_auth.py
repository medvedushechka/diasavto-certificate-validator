from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


def test_upload_requires_authentication() -> None:
    response = client.post(
        "/api/validate",
        files={"file": ("items.csv", b"article,manufacturer,product_group", "text/csv")},
    )
    assert response.status_code == 401
