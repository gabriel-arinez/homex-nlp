"""Subordinate lists preserve owners without merging independent orders."""

import pytest

from homex_nlp.contracts import ExtractionRequest
from homex_nlp.engine import RulesEngine


def extract(text):
    result = RulesEngine().extract(
        ExtractionRequest(request_id="residual-composition", text=text, currency_context="BOB")
    )
    assert result.text_original == text
    assert all(c.text == text[c.start : c.end] for c in result.candidates)
    return result


@pytest.mark.parametrize("family", ["gabinete", "credenza", "estante", "cajonera", "módulo"])
def test_subordinate_upper_and_lower_elements_keep_distinct_widths(family):
    result = extract(
        f"Un mueble con {family} superior de un metro de ancho y "
        f"{family} inferior de dos metros de ancho"
    )
    item = result.item_proposal
    assert item is not None and item.quantity == 1
    upper = next(c for c in item.components if "superior" in c.name)
    lower = next(c for c in item.components if "inferior" in c.name)
    assert upper.component_id != lower.component_id
    assert any(
        d.value_mm == "1000" and d.component_ref == upper.component_id for d in item.dimensions
    )
    assert any(
        d.value_mm == "2000" and d.component_ref == lower.component_id for d in item.dimensions
    )
    assert not any(d.component_ref is None for d in item.dimensions)


@pytest.mark.parametrize(
    "text",
    [
        "Un mueble y un gabinete de un metro de ancho",
        "Un mueble con gabinete superior y un gabinete independiente",
        "Dos muebles y tres estantes",
        "Un escritorio con dos mesas de madera",
    ],
)
def test_independent_commercial_items_are_not_collapsed(text):
    result = extract(text)
    assert result.item_proposal is None
    assert any(w.code == "MULTIPLE_MAIN_PRODUCTS" for w in result.warnings)
