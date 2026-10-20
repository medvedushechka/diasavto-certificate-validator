"""Чтение текстового слоя PDF без OCR."""

import io

from pypdf import PdfReader

from .mask_report import MaskReport, classify_masks

MAX_PDF_BYTES = 2 * 1024 * 1024
MAX_PAGES = 30
MAX_EXTRACTED_CHARACTERS = 100_000


class PdfCertificateError(ValueError):
    pass


def analyze_pdf_certificate(payload: bytes) -> MaskReport:
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
    return classify_masks(text)


def extract_pdf_masks(payload: bytes) -> tuple[str, ...]:
    """Строгий режим для совместимости с существующими тестами."""
    report = analyze_pdf_certificate(payload)
    if not report.approved and not report.unapproved:
        raise PdfCertificateError("В PDF не найдены маски HI-LEX")
    if report.unapproved:
        raise PdfCertificateError(
            "Неутверждённые маски: " + ", ".join(report.unapproved)
        )
    return report.approved
