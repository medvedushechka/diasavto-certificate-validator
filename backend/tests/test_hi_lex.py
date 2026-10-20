import pytest

from diasavto_validator.hi_lex import PREFIXES, search_key, validate_item
from diasavto_validator.models import CatalogItem, RejectionReason

MANUFACTURER = "HI-LEX CORPORATION"
GROUP = "тросы стояночного тормоза"


def item(article: str, manufacturer: str = MANUFACTURER, group: str = GROUP) -> CatalogItem:
    return CatalogItem(article=article, manufacturer=manufacturer, product_group=group)


@pytest.mark.parametrize("article", ["4VB0000", "9BBA1Z9", "4vb0000", " 4VB0000 "])
def test_accepts_valid_articles(article: str) -> None:
    result = validate_item(item(article))
    assert result.is_accepted
    assert result.matched_mask is not None
    assert result.item.article == article


@pytest.mark.parametrize(
    ("article", "reason"),
    [
        ("4VB123", RejectionReason.INVALID_ARTICLE),
        ("4VB12345", RejectionReason.INVALID_ARTICLE),
        ("4VB12-3", RejectionReason.INVALID_ARTICLE),
        ("4VB12А3", RejectionReason.INVALID_ARTICLE),
        ("4VB12 3", RejectionReason.INVALID_ARTICLE),
        ("4VB12\n3", RejectionReason.INVALID_ARTICLE),
        ("4QB1234", RejectionReason.MASK_MISMATCH),
    ],
)
def test_rejects_bad_articles(article: str, reason: RejectionReason) -> None:
    assert validate_item(item(article)).rejection_reason == reason


def test_checks_manufacturer_and_product_group() -> None:
    assert validate_item(item("4VB0000", manufacturer="OTHER")).rejection_reason == (
        RejectionReason.MANUFACTURER_MISMATCH
    )
    assert validate_item(item("4VB0000", group="OTHER")).rejection_reason == (
        RejectionReason.PRODUCT_GROUP_MISMATCH
    )


def test_preserves_ambiguous_characters_and_original() -> None:
    source = "4vbo0i1"
    result = validate_item(item(source))
    assert result.item.article == source
    assert result.search_key == "4VBO0I1"
    assert result.is_accepted


def test_nbsp_normalization_at_edges_only() -> None:
    assert search_key("\u00a04vb0000\u00a0") == "4VB0000"
    assert validate_item(item("4VB\u00a0000")).rejection_reason == (
        RejectionReason.INVALID_ARTICLE
    )


def test_has_exactly_38_distinct_prefixes() -> None:
    assert len(PREFIXES) == len(set(PREFIXES)) == 38


@pytest.mark.parametrize("prefix", PREFIXES)
def test_each_approved_prefix_matches(prefix: str) -> None:
    assert validate_item(item(prefix + "0000")).matched_mask == prefix + "****"
