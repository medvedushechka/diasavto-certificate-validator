import io
import json
from zipfile import ZipFile

import pytest
from pypdf import PdfWriter

from diasavto_validator.export import export_zip
from diasavto_validator.generator import MaskRule, count_articles, generate_articles
from diasavto_validator.pdf_certificates import PdfCertificateError, extract_pdf_masks


def test_hi_lex_count_and_boundaries() -> None:
    rule = MaskRule("4VB")
    assert rule.count == 1_679_616
    generated = rule.generate()
    assert next(generated) == "4VB0000"
    assert next(generated) == "4VB0001"


def test_all_hi_lex_masks_count() -> None:
    from diasavto_validator.hi_lex import PREFIXES

    assert count_articles(tuple(MaskRule(p) for p in PREFIXES)) == 63_825_408


def test_small_rules_are_complete_and_unique() -> None:
    rules = (MaskRule("4VB", 1, "01"), MaskRule("9BB", 1, "01"))
    output = list(generate_articles(rules))
    assert output == ["4VB0", "4VB1", "9BB0", "9BB1"]
    assert len(output) == len(set(output)) == count_articles(rules)


def test_rejects_duplicate_prefixes() -> None:
    with pytest.raises(ValueError):
        list(generate_articles((MaskRule("4VB", 1, "01"), MaskRule("4VB", 1, "XY"))))


def test_streaming_zip_chunks(tmp_path) -> None:
    destination = tmp_path / "result.zip"
    assert export_zip(destination, (MaskRule("4VB", 1, "012"),), chunk_rows=2) == 3
    with ZipFile(destination) as archive:
        assert sorted(archive.namelist()) == [
            "articles-00001.csv", "articles-00002.csv", "manifest.json"
        ]
        rows = archive.read("articles-00001.csv").decode()
        assert "4VB0" in rows and "4VB1" in rows
        manifest = json.loads(archive.read("manifest.json"))
        assert manifest["total"] == 3


def test_rejects_encrypted_pdf() -> None:
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    writer.encrypt("password")
    buffer = io.BytesIO()
    writer.write(buffer)
    with pytest.raises(PdfCertificateError, match="паролем"):
        extract_pdf_masks(buffer.getvalue())


def test_rejects_pdf_without_text_layer() -> None:
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    buffer = io.BytesIO()
    writer.write(buffer)
    with pytest.raises(PdfCertificateError, match="текстового слоя"):
        extract_pdf_masks(buffer.getvalue())
