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


def test_api_checks_masks_from_certificate() -> None:
    from fastapi.testclient import TestClient

    from app import app

    client = TestClient(app)

    def check(article: str, certificate: bytes):
        return client.post(
            "/api/rules/check",
            data={"article": article},
            files={"certificate": ("rules.txt", certificate, "text/plain")},
        )

    assert check("4VB12A9", b"4VB****").json()["matches"] is True
    assert check("9BB1234", b"4VB****").json()["matches"] is False
    assert check("9BB1234", b"9BB****").json()["matches"] is True
    assert check("4VB1234", b"4QB****").status_code == 422
    assert client.post(
        "/api/rules/check",
        json={"article": "4VB12A9", "masks": ["4VB****"]},
    ).status_code == 422


def test_certificate_recognition_deduplicates_and_sorts() -> None:
    from fastapi.testclient import TestClient

    from app import app

    response = TestClient(app).post(
        "/api/generation/plan",
        files={"certificate": ("rules.txt", b"9BB**** 4VB**** 9BB****", "text/plain")},
    )
    assert response.status_code == 200
    assert response.json() == {"masks": ["4VB****", "9BB****"], "mask_count": 2}


def test_approved_masks_endpoint_uses_registry() -> None:
    from fastapi.testclient import TestClient

    from app import app

    response = TestClient(app).get("/api/rules/hi-lex")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == len(HI_LEX.masks) == 38
    assert data["masks"] == sorted(HI_LEX.masks)
    assert response.headers["cache-control"] == "no-store"
