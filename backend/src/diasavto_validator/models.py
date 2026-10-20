from dataclasses import dataclass
from enum import StrEnum


class RejectionReason(StrEnum):
    INVALID_ARTICLE = "invalid_article"
    MANUFACTURER_MISMATCH = "manufacturer_mismatch"
    PRODUCT_GROUP_MISMATCH = "product_group_mismatch"
    MASK_MISMATCH = "mask_mismatch"


@dataclass(frozen=True, slots=True)
class CatalogItem:
    article: str
    manufacturer: str
    product_group: str


@dataclass(frozen=True, slots=True)
class ValidationResult:
    item: CatalogItem
    search_key: str
    matched_mask: str | None
    rejection_reason: RejectionReason | None

    @property
    def is_accepted(self) -> bool:
        return self.rejection_reason is None
