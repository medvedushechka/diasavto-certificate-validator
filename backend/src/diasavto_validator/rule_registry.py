"""Расширяемый реестр правил поставщиков.

Поддерживаемые наборы регистрируются вручную после проверки документов.
Новые варианты масок не выводятся автоматически из текста или ответов LLM.
"""

import re
from dataclasses import dataclass

from .hi_lex import PREFIXES, search_key


@dataclass(frozen=True, slots=True)
class SupplierRules:
    code: str
    name: str
    version: str
    masks: tuple[str, ...]
    symbols: str = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    def __post_init__(self) -> None:
        if not self.code or not self.version or not self.masks:
            raise ValueError("Набор правил должен содержать код, версию и маски")
        if len(set(self.masks)) != len(self.masks):
            raise ValueError("В наборе правил есть повторяющиеся маски")
        if not self.symbols or not self.symbols.isascii() or not self.symbols.isalnum():
            raise ValueError("Некорректный алфавит масок")
        if len(set(self.symbols)) != len(self.symbols):
            raise ValueError("Алфавит содержит повторы")
        for mask in self.masks:
            if not mask or "*" not in mask or not re.fullmatch(r"[A-Z0-9*]+", mask):
                raise ValueError(f"Некорректная маска: {mask!r}")

    def matches(self, article: str, selected_masks: tuple[str, ...]) -> bool:
        value = search_key(article)
        allowed = set(self.masks)
        if not selected_masks or not set(selected_masks).issubset(allowed):
            raise ValueError("Указаны неразрешённые маски")
        for mask in selected_masks:
            if len(value) != len(mask):
                continue
            if all(
                (char in self.symbols if pattern == "*" else char == pattern)
                for char, pattern in zip(value, mask, strict=True)
            ):
                return True
        return False


HI_LEX = SupplierRules(
    code="hi-lex",
    name="HI-LEX CORPORATION",
    version="2026-10-20",
    masks=tuple(prefix + "****" for prefix in PREFIXES),
)

REGISTRY: dict[str, SupplierRules] = {HI_LEX.code: HI_LEX}


def supplier_rules(code: str) -> SupplierRules:
    try:
        return REGISTRY[code]
    except KeyError as exc:
        raise ValueError("Неизвестный производитель") from exc
