import pytest

from diasavto_validator.rule_registry import HI_LEX, SupplierRules, supplier_rules


def test_hi_lex_registry_preserves_38_approved_masks() -> None:
    assert len(HI_LEX.masks) == 38
    assert HI_LEX.matches("4VB12A9", ("4VB****",))
    assert HI_LEX.matches(" 4vb12a9 ", ("4VB****",))
    assert not HI_LEX.matches("4VB12-9", ("4VB****",))
    assert not HI_LEX.matches("9BB1234", ("4VB****",))


def test_rules_support_wildcards_in_the_middle() -> None:
    example = SupplierRules(
        code="example",
        name="Тестовый производитель",
        version="1",
        masks=("AB**CD",),
    )
    assert example.matches("AB12CD", ("AB**CD",))
    assert not example.matches("AB1-CD", ("AB**CD",))


def test_unknown_mask_is_rejected() -> None:
    with pytest.raises(ValueError):
        HI_LEX.matches("4QB1234", ("4QB****",))


def test_duplicate_masks_are_rejected() -> None:
    with pytest.raises(ValueError):
        SupplierRules("demo", "Demo", "1", ("AB**", "AB**"))


def test_unknown_supplier_is_rejected() -> None:
    with pytest.raises(ValueError):
        supplier_rules("unknown")
