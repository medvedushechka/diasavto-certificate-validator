import io

import pytest
from fastapi.testclient import TestClient
from openpyxl import Workbook, load_workbook

from app import app
from auth import require_user
from diasavto_validator.catalog_io import CatalogFormatError, parse_catalog

client = TestClient(app)


@pytest.fixture(autouse=True)
def authenticated_user():
    app.dependency_overrides[require_user] = lambda: "synthetic-user-id"
    yield
    app.dependency_overrides.clear()


def test_csv_parses_and_preserves_raw_article() -> None:
    payload = (
        "article,manufacturer,product_group\n"
        "4vb0000,HI-LEX CORPORATION,тросы стояночного тормоза\n"
    )
    assert parse_catalog(payload.encode(), "catalog.csv")[0].article == "4vb0000"


def test_csv_rejects_missing_columns() -> None:
    with pytest.raises(CatalogFormatError):
        parse_catalog(b"article,manufacturer\n4VB0000,HI-LEX CORPORATION\n", "catalog.csv")


def test_excel_parses() -> None:
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(["article", "manufacturer", "product_group"])
    sheet.append(["4VB0000", "HI-LEX CORPORATION", "тросы стояночного тормоза"])
    buffer = io.BytesIO()
    workbook.save(buffer)
    assert parse_catalog(buffer.getvalue(), "catalog.xlsx")[0].article == "4VB0000"


def test_http_report_has_two_sheets() -> None:
    payload = (
        "article,manufacturer,product_group\n"
        "4VB0000,HI-LEX CORPORATION,тросы стояночного тормоза\n"
        "4QB1234,HI-LEX CORPORATION,тросы стояночного тормоза\n"
    )
    response = client.post(
        "/api/validate",
        files={"file": ("catalog.csv", payload.encode(), "text/csv")},
    )
    assert response.status_code == 200
    workbook = load_workbook(io.BytesIO(response.content), read_only=True)
    assert workbook.sheetnames == ["Подходят", "Исключения"]
    assert workbook.worksheets[0].max_row == 2
    assert workbook.worksheets[1].max_row == 2


def test_http_rejects_invalid_file() -> None:
    response = client.post(
        "/api/validate", files={"file": ("catalog.csv", b"bad", "text/csv")}
    )
    assert response.status_code == 422


def test_rejects_formula_injection_on_export() -> None:
    payload = (
        "article,manufacturer,product_group\n"
        "=1+2,HI-LEX CORPORATION,тросы стояночного тормоза\n"
    )
    response = client.post(
        "/api/validate", files={"file": ("catalog.csv", payload.encode(), "text/csv")}
    )
    assert response.status_code == 200
    sheet = load_workbook(io.BytesIO(response.content)).worksheets[1]
    assert sheet["A2"].data_type == "s"
