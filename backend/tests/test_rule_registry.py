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


def test_api_checks_supplier_rules() -> None:
    from fastapi.testclient import TestClient

    from app import app
    from auth import require_user

    app.dependency_overrides[require_user] = lambda: "test-user"
    try:
        client = TestClient(app)
        response = client.post(
            "/api/rules/check",
            json={"supplier": "hi-lex", "article": "4VB12A9", "masks": ["4VB****"]},
        )
        assert response.status_code == 200
        assert response.json()["matches"] is True
        response = client.post(
            "/api/rules/check",
            json={"supplier": "hi-lex", "article": "9BB1234", "masks": ["4VB****"]},
        )
        assert response.status_code == 200
        assert response.json()["matches"] is False
        response = client.post(
            "/api/rules/check",
            json={"supplier": "hi-lex", "article": "4VB1234", "masks": ["4QB****"]},
        )
        assert response.status_code == 422
    finally:
        app.dependency_overrides.clear()


def test_approved_masks_endpoint_uses_registry() -> None:
    from fastapi.testclient import TestClient

    from app import app
    from auth import require_user

    app.dependency_overrides[require_user] = lambda: "test-user"
    try:
        response = TestClient(app).get("/api/rules/hi-lex")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == len(HI_LEX.masks) == 38
        assert data["masks"] == sorted(HI_LEX.masks)
        assert response.headers["cache-control"] == "no-store"
    finally:
        app.dependency_overrides.clear()
