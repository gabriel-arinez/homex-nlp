"""Independent language rules, not corpus identifiers or memorized products."""

import pytest

from homex_nlp.contracts import ExtractionRequest
from homex_nlp.engine import RulesEngine


def extract(text):
    result = RulesEngine().extract(
        ExtractionRequest(request_id="semantic-probe", text=text, currency_context="BOB")
    )
    assert result.text_original == text
    assert all(c.text == text[c.start : c.end] for c in result.candidates)
    return result


def test_referential_primary_and_introduced_drawer_are_one_commercial_product():
    result = extract(
        "Tres escritorios con cajonera rodante. Escritorio de 120 cm de ancho. Cajonera de 40 cm de ancho. Precio unitario 1700 bolivianos."
    )
    assert result.item_proposal is not None
    assert result.item_proposal.quantity == 3
    assert result.item_proposal.price.stated_amount == "1700.00"
    assert sum(c.name.lower() == "cajonera" for c in result.item_proposal.components) == 1
    drawer = next(
        c.component_id for c in result.item_proposal.components if c.name.lower() == "cajonera"
    )
    assert any(
        d.component_ref == drawer and d.value_mm == "400" for d in result.item_proposal.dimensions
    )
    assert any(
        d.component_ref is None and d.value_mm == "1200" for d in result.item_proposal.dimensions
    )


@pytest.mark.parametrize(
    "text",
    [
        "Una mesa y otra mesa de 90 cm de ancho.",
        "Una mesa. Dos mesas de 90 cm de ancho.",
        "Un escritorio y una cajonera.",
        "Un juego de mesas. Dos mesas de diferentes tamaños.",
    ],
)
def test_independent_and_ambiguous_products_still_abstain(text):
    assert extract(text).item_proposal is None


@pytest.mark.parametrize("product", ["cubos móviles", "estaciones de trabajo"])
def test_explicit_furniture_families_are_recognized_without_ids(product):
    result = extract(f"Dos {product} de 90 centímetros de ancho. Precio unitario 1800 bolivianos.")
    assert result.item_proposal is not None
    assert result.item_proposal.quantity == 2


def test_adjectival_height_does_not_steal_following_width_and_compound_height():
    result = extract(
        "Un armario alto de ochenta centímetros de ancho, cincuenta de profundidad y dos metros veinte de alto."
    )
    dims = result.item_proposal.dimensions
    assert [(d.axis, d.value_mm) for d in dims if d.axis == "alto"] == [("alto", "2200")]
    assert [(d.axis, d.value_mm) for d in dims if d.axis == "ancho"] == [("ancho", "800")]
    assert [(d.axis, d.value_mm) for d in dims if d.axis == "profundidad"] == [
        ("profundidad", None)
    ]
    depth = next(d for d in dims if d.axis == "profundidad")
    assert depth.value == "50" and depth.unit is None
    assert any(w.code == "MISSING_UNIT" for w in result.warnings)


def test_missing_leading_unit_and_new_component_never_borrow_later_units():
    result = extract("Una mesa de 120 de ancho y 75 cm de alto.")
    assert next(d for d in result.item_proposal.dimensions if d.axis == "ancho").unit is None
    result = extract("Una mesa de 80 cm de ancho. Cajones de 50 de profundidad.")
    assert all(d.unit is None for d in result.item_proposal.dimensions if d.axis == "profundidad")


def test_electrical_accessories_keep_explicit_counts_and_evidence():
    result = extract(
        "Una mesa con tablero y dos puertos USB, tres HDMI y cuatro tomacorrientes. Precio unitario 600 bolivianos."
    )
    accessories = result.item_proposal.accessories
    assert next(a for a in accessories if "USB" in a.name).quantity == 2
    assert next(a for a in accessories if "HDMI" in a.name).quantity == 3
    for accessory in accessories:
        evidence = [c for c in result.candidates if c.candidate_id in accessory.evidence_ids]
        assert any(c.label == "CANTIDAD_ACCESORIO" for c in evidence)


def test_accessory_negation_and_protocol_number_do_not_invent_counts():
    result = extract("Una mesa sin HDMI, con USB 3.0 y tomacorrientes.")
    assert not any("HDMI" in a.name for a in result.item_proposal.accessories)
    assert next(a for a in result.item_proposal.accessories if "USB" in a.name).quantity is None


def test_explicit_recognition_variant_is_unit_price_not_negotiated_total():
    result = extract("Dos escritorios en L. Presiunitario de 2,300 bolivianos.")
    assert result.item_proposal.price.mode == "PRECIO_UNITARIO"
    assert result.item_proposal.price.stated_amount == "2300.00"
    assert extract("Una mesa. Presiunitario de 80 centímetros.").item_proposal.price is None
