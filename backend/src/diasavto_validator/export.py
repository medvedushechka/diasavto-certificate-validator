"""Формирование ZIP без накопления полного списка в памяти."""

import csv
import io
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from .generator import MaskRule, count_articles

DEFAULT_CHUNK_ROWS = 250_000


def export_zip(
    output_path: Path,
    rules: tuple[MaskRule, ...],
    *,
    chunk_rows: int = DEFAULT_CHUNK_ROWS,
) -> int:
    if chunk_rows < 1 or chunk_rows > 1_000_000:
        raise ValueError("Размер части должен быть от 1 до 1 000 000 строк")
    expected = count_articles(rules)
    processed = 0
    index = 0
    archive_path = Path(output_path)
    if archive_path.exists():
        raise FileExistsError("Файл результата уже существует")
    # Файлы создаются последовательно. При ошибке незавершённый архив удаляется.
    try:
        with ZipFile(archive_path, mode="x", compression=ZIP_DEFLATED, allowZip64=True) as archive:
            for rule in rules:
                iterator = rule.generate()
                while True:
                    index += 1
                    name = f"articles-{index:05d}.csv"
                    rows_in_part = 0
                    with archive.open(name, mode="w", force_zip64=True) as binary:
                        with io.TextIOWrapper(binary, encoding="utf-8", newline="", write_through=True) as text:
                            writer = csv.writer(text)
                            writer.writerow(["article"])
                            for article in iterator:
                                writer.writerow([article])
                                rows_in_part += 1
                                processed += 1
                                if rows_in_part >= chunk_rows:
                                    break
                    if rows_in_part < chunk_rows:
                        break
            archive.writestr(
                "manifest.json",
                json.dumps(
                    {"format": "diasavto-articles-v1",
                     "total": processed,
                     "expected": expected,
                     "masks": [r.mask for r in rules]},
                    ensure_ascii=False, indent=2,
                ),
            )
    except BaseException:
        archive_path.unlink(missing_ok=True)
        raise
    if processed != expected:
        archive_path.unlink(missing_ok=True)
        raise RuntimeError("Число записей не совпадает с ожидаемым")
    return processed
