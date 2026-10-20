"""Потоковое перечисление артикулов по проверенным правилам."""

from dataclasses import dataclass
from itertools import product
from typing import Iterator

ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
HI_LEX_WILDCARDS = 4


@dataclass(frozen=True, slots=True)
class MaskRule:
    prefix: str
    wildcards: int = HI_LEX_WILDCARDS
    alphabet: str = ALPHABET

    def __post_init__(self) -> None:
        if not self.prefix or not self.prefix.isascii() or not self.prefix.isalnum():
            raise ValueError("Некорректный префикс маски")
        if not 1 <= self.wildcards <= 8:
            raise ValueError("Недопустимое количество переменных символов")
        if not self.alphabet or len(self.alphabet) != len(set(self.alphabet)):
            raise ValueError("Алфавит должен содержать уникальные символы")
        if not self.alphabet.isascii() or not self.alphabet.isalnum():
            raise ValueError("Алфавит должен состоять из букв и цифр ASCII")

    @property
    def count(self) -> int:
        return len(self.alphabet) ** self.wildcards

    @property
    def mask(self) -> str:
        return self.prefix + "*" * self.wildcards

    def generate(self) -> Iterator[str]:
        for suffix in product(self.alphabet, repeat=self.wildcards):
            yield self.prefix + "".join(suffix)


def generate_articles(rules: tuple[MaskRule, ...]) -> Iterator[str]:
    """Вызывает генератор для непересекающихся правил.

    Не использовать для произвольных пересекающихся масок без проверки.
    """
    if len({rule.prefix for rule in rules}) != len(rules):
        raise ValueError("Маски с одинаковым префиксом не допускаются")
    for rule in rules:
        yield from rule.generate()


def count_articles(rules: tuple[MaskRule, ...]) -> int:
    if len({rule.prefix for rule in rules}) != len(rules):
        raise ValueError("Маски с одинаковым префиксом не допускаются")
    return sum(rule.count for rule in rules)
