"""Drawer morphology and explicit dimensional ownership through the public engine."""

import pytest

from homex_nlp.contracts import ExtractionRequest
from homex_nlp.engine import RulesEngine


def extract(text):
    result = RulesEngine().extract(
        ExtractionRequest(request_id="drawer-scope", text=text, currency_context="BOB")
    )
    assert result.text_original == text
    assert all(c.text == text[c.start : c.end] for c in result.candidates)
    return result


@pytest.mark.parametrize(
    "noun,count", [("cajón", 1), ("cajon", 1), ("cajones", 2), ("gaveta", 1), ("gavetas", 2)]
)
def test_drawer_dimensions_belong_to_the_component_not_the_commercial_item(noun, count):
    number = "un" if count == 1 else "dos"
    text = (
        "un escritorio de melamina de ciento veinte centímetros de largo y sesenta de ancho "
        f"con {number} {noun} de cuarenta centímetros de ancho y veinte centímetros de alto"
    )
    result = extract(text)
    item = result.item_proposal
    assert item is not None and item.quantity == 1
    assert len(item.components) == 1
    drawer = item.components[0]
    assert drawer.name == noun
    assert {(d.axis, d.value_mm, d.component_ref) for d in item.dimensions} == {
        ("largo", "1200", None),
        ("ancho", "600", None),
        ("ancho", "400", drawer.component_id),
        ("alto", "200", drawer.component_id),
    }
    assert any(
        c.label == "CANTIDAD_INTERNA"
        and c.normalized_value == count
        and c.component_ref == drawer.component_id
        and c.decision == "ACCEPTED"
        for c in result.candidates
    )
    assert not item.accessories


@pytest.mark.parametrize("noun", ["cajón", "cajon", "cajones", "gaveta", "gavetas"])
def test_negated_drawer_never_becomes_an_owner(noun):
    result = extract(f"Dos escritorios de 120 cm de ancho sin {noun}.")
    assert result.item_proposal.quantity == 2
    assert not result.item_proposal.components
    assert all(d.component_ref is None for d in result.item_proposal.dimensions)
    assert not result.item_proposal.accessories


@pytest.mark.parametrize("noun", ["cajón", "cajon", "gaveta"])
def test_explicit_correction_preserves_commercial_quantity(noun):
    result = extract(f"Dos escritorios con dos cajones, no, mejor un {noun} de 40 cm de ancho.")
    item = result.item_proposal
    assert item.quantity == 2 and len(item.components) == 1
    drawer = item.components[0]
    assert drawer.name == noun
    assert any(
        c.label == "CANTIDAD_INTERNA"
        and c.normalized_value == 1
        and c.component_ref == drawer.component_id
        and c.decision == "ACCEPTED"
        for c in result.candidates
    )
    assert all(d.component_ref == drawer.component_id for d in item.dimensions)


@pytest.mark.parametrize("noun", ["cajón", "cajon", "cajones", "gaveta", "gavetas"])
def test_independent_furniture_order_is_not_absorbed(noun):
    result = extract(f"Un escritorio con un {noun} de 40 cm de ancho y una mesa de 80 cm de ancho.")
    assert result.item_proposal is None
    assert any(w.code == "MULTIPLE_MAIN_PRODUCTS" for w in result.warnings)


@pytest.mark.parametrize("noun", ["cajón", "cajon", "gaveta"])
def test_explicit_other_drawer_is_not_deduplicated(noun):
    item = extract(
        f"Un escritorio con un {noun} de 40 cm de ancho. Otro {noun} de 30 cm de ancho."
    ).item_proposal
    assert item.quantity == 1 and len(item.components) == 2
    assert {d.value_mm for d in item.dimensions} == {"400", "300"}
    assert len({d.component_ref for d in item.dimensions}) == 2


@pytest.mark.parametrize("noun", ["cajón", "cajon", "cajones", "gaveta", "gavetas"])
def test_repeated_drawer_description_has_one_owner_and_no_accessory_duplicate(noun):
    item = extract(
        f"Un escritorio con dos {noun}. Dos {noun} con rieles telescópicos."
    ).item_proposal
    assert item.quantity == 1 and len(item.components) == 1
    assert not any(a.name == noun for a in item.accessories)


@pytest.mark.parametrize("noun", ["cajón", "cajon", "cajones", "gaveta", "gavetas"])
def test_lateral_qualifier_does_not_create_a_second_component(noun):
    item = extract(f"Dos escritorios con dos {noun} laterales de 40 cm de ancho.").item_proposal
    assert item.quantity == 2 and len(item.components) == 1
    assert item.dimensions[0].component_ref == item.components[0].component_id


@pytest.mark.parametrize("noun", ["cajón", "cajon", "cajones", "gaveta", "gavetas"])
def test_drawer_count_in_gavetero_definition_does_not_steal_envelope(noun):
    item = extract(f"Un gavetero de tres {noun} de 50 cm de ancho y 100 cm de alto.").item_proposal
    assert item.quantity == 1 and len(item.components) == 1
    assert all(d.component_ref is None for d in item.dimensions)


@pytest.mark.parametrize("noun", ["cajón", "cajon", "gaveta"])
def test_internal_count_after_metres_does_not_consume_the_length(noun):
    result = extract(f"Un escritorio de ancho un metro y un {noun}.")
    item = result.item_proposal
    assert item.quantity == 1 and len(item.components) == 1
    assert any(d.value_mm == "1000" and d.component_ref is None for d in item.dimensions)
