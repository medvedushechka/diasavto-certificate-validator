import io
import re
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

from .hi_lex import PREFIX_SET

MAX_CERTIFICATE_BYTES = 1024 * 1024
MAX_UNCOMPRESSED_XML = 2 * 1024 * 1024
MASK_PATTERN = re.compile(r"(?<![A-Za-z0-9*])([A-Z0-9]{3})\*{4}(?![A-Za-z0-9*])")
DOCUMENT_NS = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


class CertificateFormatError(ValueError):
    pass


def extract_masks(content: bytes, filename: str) -> tuple[str, ...]:
    if not content or len(content) > MAX_CERTIFICATE_BYTES:
        raise CertificateFormatError("Сертификат пустой или превышает 1 МБ")

    extension = Path(filename).suffix.lower()
    if extension == ".txt":
        try:
            text = content.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise CertificateFormatError("Текстовый файл должен быть в UTF-8") from exc
    elif extension == ".docx":
        if not zipfile.is_zipfile(io.BytesIO(content)):
            raise CertificateFormatError("Некорректный DOCX")
        try:
            with zipfile.ZipFile(io.BytesIO(content)) as archive:
                entry = archive.getinfo("word/document.xml")
                if entry.file_size > MAX_UNCOMPRESSED_XML:
                    raise CertificateFormatError("Документ слишком большой")
                xml = archive.read(entry)
            root = ET.fromstring(xml)
            text = " ".join(
                "".join(element.itertext())
                for element in root.iter(DOCUMENT_NS + "p")
            )
        except (KeyError, zipfile.BadZipFile, ET.ParseError, RuntimeError, OSError) as exc:
            raise CertificateFormatError("Не удалось прочитать содержимое DOCX") from exc
    else:
        raise CertificateFormatError("Поддерживаются сертификаты DOCX и TXT")

    found = {match.group(1) for match in MASK_PATTERN.finditer(text)}
    if not found:
        raise CertificateFormatError("В документе не найдены маски формата ABC****")
    unsupported = found - PREFIX_SET
    if unsupported:
        raise CertificateFormatError(
            "Обнаружены неутверждённые маски: " + ", ".join(sorted(unsupported))
        )
    return tuple(prefix + "****" for prefix in sorted(found))
