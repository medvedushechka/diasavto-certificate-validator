import io
from zipfile import ZIP_DEFLATED, ZipFile

import pytest

from diasavto_validator.certificates import CertificateFormatError, extract_masks


def test_reads_txt_masks() -> None:
    assert extract_masks(b"4VB**** 9BB**** 4VB****", "mask.txt") == (
        "4VB****",
        "9BB****",
    )


def test_rejects_unknown_mask() -> None:
    with pytest.raises(CertificateFormatError, match="неутвержд"):
        extract_masks(b"4QB****", "mask.txt")


def test_rejects_missing_masks() -> None:
    with pytest.raises(CertificateFormatError, match="не найдены"):
        extract_masks(b"no masks", "mask.txt")


def test_extracts_docx_masks() -> None:
    buffer = io.BytesIO()
    with ZipFile(buffer, "w", compression=ZIP_DEFLATED) as archive:
        archive.writestr(
            "word/document.xml",
            '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
            "<w:body><w:p><w:r><w:t>4VB**** 9BB****</w:t></w:r></w:p></w:body>"
            "</w:document>",
        )
    assert extract_masks(buffer.getvalue(), "mask.docx") == ("4VB****", "9BB****")

