"""Money amount evidence is independent of its commercial mode."""

import pytest
from test_final_magnitudes import extract


@pytest.mark.parametrize(
    "raw,amount", [("13 mil 200", "13200"), ("mil cien", "1100"), ("2 mil 500", "2500")]
)
@pytest.mark.parametrize("quantity", ["Una", "Tres"])
def test_ambiguous_price_preserves_complete_amount(raw, amount, quantity):
    result = extract(f"{quantity} mesas. Precio de {raw} bolivianos.")
    assert result.item_proposal.price is None
    candidates = [c for c in result.candidates if c.label == "PRECIO_AMBIGUO"]
    assert len(candidates) == 1
    assert candidates[0].text == raw
    assert candidates[0].decision == "UNRESOLVED"
    assert any(amount in w.message.replace(".00", "") for w in result.warnings)


def test_postposed_total_is_explicit():
    result = extract("Tres mesas por dos mil bolivianos en total.")
    assert result.item_proposal.price.mode == "TOTAL_NEGOCIADO"
    assert result.item_proposal.price.stated_amount == "2000.00"


def test_explicit_unit_price_stays_explicit():
    result = extract("Tres mesas precio unitario 1200 bolivianos.")
    assert result.item_proposal.price.stated_amount == "1200.00"
    assert result.item_proposal.price.line_total == "3600.00"
