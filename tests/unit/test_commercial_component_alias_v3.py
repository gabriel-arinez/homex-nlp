"""Literal furniture variants must preserve the same explicit component scope."""

import pytest

from homex_nlp.contracts import ExtractionRequest
from homex_nlp.engine import RulesEngine


def extract(text):
    result = RulesEngine().extract(
        ExtractionRequest(request_id="component-variant-probe", text=text, currency_context="BOB")
    )
    assert result.text_original == text
    assert all(c.text == text[c.start : c.end] for c in result.candidates)
    return result


@pytest.mark.parametrize("variant", ["Credenza", "Credencia"])
def test_literal_integrated_sideboard_spelling_keeps_component_axes_and_material(variant):
    result = extract(
        "Dos escritorios de 160 cm de ancho y 80 cm de alto. "
        f"{variant} integrada de MDF de 110 cm de ancho, 65 cm de alto y 45 cm de profundidad. "
        "Precio unitario 1900 bolivianos."
    )
    assert result.status == "REQUIRES_REVIEW"
    item = result.item_proposal
    assert item.quantity == 2 and item.price.stated_amount == "1900.00"
    component = next(
        c for c in item.components if c.name.casefold() == f"{variant.lower()} integrada"
    )
    assert {
        (d.axis, d.value_mm) for d in item.dimensions if d.component_ref == component.component_id
    } == {("ancho", "1100"), ("alto", "650"), ("profundidad", "450")}
    assert {(d.axis, d.value_mm) for d in item.dimensions if d.component_ref is None} == {
        ("ancho", "1600"),
        ("alto", "800"),
    }
    material = next(c for c in result.candidates if c.label == "MATERIAL" and c.text == "MDF")
    assert material.component_ref == component.component_id


@pytest.mark.parametrize("word", ["creencia", "credencial", "credencia lateral"])
def test_non_furniture_or_unintegrated_words_do_not_become_integrated_components(word):
    result = extract(f"Un escritorio de 160 cm de ancho. {word} de MDF de 110 cm de ancho.")
    assert result.item_proposal is not None
    assert not any(c.name.casefold().startswith(word) for c in result.item_proposal.components)


def test_counted_independent_sideboard_variant_is_not_merged_into_the_desk():
    result = extract("Un escritorio y una credencia de 110 cm de ancho, cuerpo de MDF.")
    assert result.status == "NO_PROPOSAL"
    assert result.item_proposal is None
    assert any(w.code == "MULTIPLE_MAIN_PRODUCTS" for w in result.warnings)
