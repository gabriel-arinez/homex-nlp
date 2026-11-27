"""Complete monetary evidence must not invent a spoken commercial mode."""

import pytest
from test_final_magnitudes import extract


@pytest.mark.parametrize(
    "text,amount",
    [
        ("Una mesa de 500 bolivianos", "500"),
        ("Una mesa de madera a mil doscientos cincuenta bolivianos", "1250"),
        ("Una mesa de madera de mil bolivianos, perdón, de novecientos bolivianos", "900"),
        ("Una mesa, precio de quinientos bolivianos", "500"),
        ("Una mesa a 2 mil 500 bolivianos", "2500"),
    ],
)
def test_complete_reviewable_amount(text, amount):
    result = extract(text)
    assert result.item_proposal.price is None
    selected = [
        c for c in result.candidates if c.label == "PRECIO_AMBIGUO" and c.decision == "UNRESOLVED"
    ]
    assert len(selected) == 1
    assert selected[0].normalized_value == amount
    assert "equivalence" in selected[0].reason


@pytest.mark.parametrize(
    "text",
    [
        "Dos mesas de 500 bolivianos",
        "Mesa de 500 bolivianos",
        "Una mesa con dos cajones de 500 bolivianos",
    ],
)
def test_only_explicit_root_quantity_supplies_equivalence(text):
    result = extract(text)
    assert result.item_proposal.price is None
    candidate = next(
        c for c in result.candidates if c.label == "PRECIO_AMBIGUO" and c.decision == "UNRESOLVED"
    )
    assert ("equivalence" in candidate.reason) is (
        result.item_proposal.quantity == 1 and text.startswith("Una mesa")
    )


@pytest.mark.parametrize(
    "text",
    [
        "Una mesa de 500 mil mil bolivianos",
        "Una mesa de -500 bolivianos",
        "Una mesa de 500 bolivianos o 600 bolivianos",
        "Una mesa de 500 dólares",
    ],
)
def test_invalid_conflicting_or_foreign_amount_is_not_suggested(text):
    result = extract(text)
    assert result.item_proposal.price is None
    assert not any(
        c.label == "PRECIO_AMBIGUO"
        and c.decision == "UNRESOLVED"
        and "equivalence" in (c.reason or "")
        for c in result.candidates
    )


@pytest.mark.parametrize(
    "text",
    [
        "Mesa de 500 bolivianos, precio total 1000 bolivianos",
        "Dos mesas precio total 1000 bolivianos y 500 bolivianos",
    ],
)
def test_mixed_ambiguous_evidence_cannot_supply_explicit_unit_mode(text):
    result = extract(text)
    assert result.item_proposal.price is None
    assert any(w.code in {"CONFLICTING_VALUES", "INVALID_PRICE"} for w in result.warnings)
