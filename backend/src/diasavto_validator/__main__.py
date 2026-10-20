"""Локальная генерация полного результата вне ограничений Vercel."""

import argparse
from pathlib import Path

from .certificates import extract_masks
from .generator import MaskRule, count_articles
from .pdf_certificates import extract_pdf_masks
from .export import export_zip


def main() -> None:
    parser = argparse.ArgumentParser(description="Генерация артикулов по сертификату HI-LEX")
    parser.add_argument("certificate", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--chunk-rows", type=int, default=250_000)
    args = parser.parse_args()
    payload = args.certificate.read_bytes()
    if args.certificate.suffix.lower() == ".pdf":
        masks = extract_pdf_masks(payload)
    else:
        masks = extract_masks(payload, args.certificate.name)
    rules = tuple(MaskRule(mask[:-4]) for mask in masks)
    total = count_articles(rules)
    print(f"Масок: {len(masks)}; ожидается артикулов: {total}")
    result = export_zip(args.output, rules, chunk_rows=args.chunk_rows)
    print(f"Готово: {result} артикулов, архив: {args.output}")


if __name__ == "__main__":
    main()
