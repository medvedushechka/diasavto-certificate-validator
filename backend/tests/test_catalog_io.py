import io

import pytest
from openpyxl import Workbook

from diasavto_validator.catalog_io import CatalogFormatError, parse_catalog

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


