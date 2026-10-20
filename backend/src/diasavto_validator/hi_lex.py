import re

from .models import CatalogItem, RejectionReason, ValidationResult

MANUFACTURER = "HI-LEX CORPORATION"
PRODUCT_GROUP = "тросы стояночного тормоза"

# Утверждённые маски из документа HI-LEX. Не расширять без согласования.
PREFIXES = (
    "4VB", "4JB", "4AB", "9TB", "4TB", "4HB", "9CB", "9NB",
    "4GB", "4RB", "4PB", "9VB", "4UB", "4CB", "4NB", "4DB",
    "9AB", "4FB", "4BB", "4ZB", "9HB", "4MB", "9DB", "9ZB",
    "1PB", "5PB", "9JB", "2HB", "5CB", "2JB", "2PB", "9RB",
    "9YB", "2KB", "9GB", "2YB", "7HB", "9BB",
)
PREFIX_SET = frozenset(PREFIXES)
ARTICLE_PATTERN = re.compile(r"[A-Z0-9]{7}\Z", flags=re.ASCII)


def search_key(article: str) -> str:
    # Сохраняем внутренние пробелы и символы для корректного учёта исключений.
    return article.replace("\u00a0", " ").strip(" ").translate(
        str.maketrans("abcdefghijklmnopqrstuvwxyz", "ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    )


def validate_item(item: CatalogItem) -> ValidationResult:
    key = search_key(item.article)
    if not ARTICLE_PATTERN.fullmatch(key):
        return ValidationResult(item, key, None, RejectionReason.INVALID_ARTICLE)
    if item.manufacturer != MANUFACTURER:
        return ValidationResult(item, key, None, RejectionReason.MANUFACTURER_MISMATCH)
    if item.product_group != PRODUCT_GROUP:
        return ValidationResult(item, key, None, RejectionReason.PRODUCT_GROUP_MISMATCH)
    prefix = key[:3]
    if prefix not in PREFIX_SET:
        return ValidationResult(item, key, None, RejectionReason.MASK_MISMATCH)
    return ValidationResult(item, key, prefix + "****", None)


def validate_catalog(items: list[CatalogItem]) -> list[ValidationResult]:
    return [validate_item(item) for item in items]
