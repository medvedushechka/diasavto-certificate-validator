"""Чтение текстового слоя PDF без OCR."""

import io
import re

from pypdf import PdfReader

from .hi_lex import PREFIX_SET

MAX_PDF_BYTES = 2 * 1024 * 1024
MAX_PAGES = 30
MAX_EXTRACTED_CHARACTERS = 100_000
MASK_PATTERN = re.compile(r"(?<![A-Za-z0-9*])([A-Z0-9]{3})\*{4}(?![A-Za-z0-9*])")


class PdfCertificateError(ValueError):
    pass


def extract_pdf_masks(payload: bytes) -> tuple[str, ...]:
    if not payload or len(payload) > MAX_PDF_BYTES:
        raise PdfCertificateError("PDF пустой или превышает 2 МБ")
    if not payload.startswith(b"%PDF-"):
        raise PdfCertificateError("Файл не является PDF")
    try:
        reader = PdfReader(io.BytesIO(payload), strict=True)
        if reader.is_encrypted:
            raise PdfCertificateError("PDF с паролем не поддерживается")
        if not 1 <= len(reader.pages) <= MAX_PAGES:
            raise PdfCertificateError("Допускается не более 30 страниц")
        text_chunks: list[str] = []
        size = 0
        for page in reader.pages:
            text = page.extract_text() or ""
            size += len(text)
            if size > MAX_EXTRACTED_CHARACTERS:
                raise PdfCertificateError("Слишком много извлечённого текста")
            text_chunks.append(text)
    except PdfCertificateError:
        raise
    except Exception as exc:
        raise PdfCertificateError("Не удалось безопасно прочитать PDF") from exc

    text = "\n".join(text_chunks)
    if not text.strip():
        raise PdfCertificateError("Нет текстового слоя. OCR не входит в задание")
    found = {match.group(1) for match in MASK_PATTERN.finditer(text)}
    if not found:
        raise PdfCertificateError("В PDF не найдены маски HI-LEX")
    unknown = found - PREFIX_SET
    if unknown:
        raise PdfCertificateError(
            "Неутверждённые маски: " + ", ".join(sorted(unknown))
        )
    return tuple(prefix + "****" for prefix in sorted(found))
