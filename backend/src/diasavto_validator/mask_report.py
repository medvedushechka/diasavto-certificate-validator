"""Классификация масок сертификата по утверждённому реестру HI-LEX."""

import re
from dataclasses import dataclass

from .hi_lex import PREFIX_SET

MASK_PATTERN = re.compile(r"(?<![A-Za-z0-9*])([A-Z0-9]{3})\*{4}(?![A-Za-z0-9*])")


@dataclass(frozen=True, slots=True)
class MaskReport:
    approved: tuple[str, ...]
    unapproved: tuple[str, ...]

    @property
    def approved_count(self) -> int:
        return len(self.approved)

    @property
    def unapproved_count(self) -> int:
        return len(self.unapproved)


def classify_masks(text: str) -> MaskReport:
    """Считаем уникальные маски точного формата ABC****, а не их упоминания."""
    prefixes = {match.group(1) for match in MASK_PATTERN.finditer(text)}
    return MaskReport(
        approved=tuple(prefix + "****" for prefix in sorted(prefixes & PREFIX_SET)),
        unapproved=tuple(prefix + "****" for prefix in sorted(prefixes - PREFIX_SET)),
    )
