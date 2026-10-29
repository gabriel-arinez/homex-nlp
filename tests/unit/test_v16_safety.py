"""Independent requirements-derived cases; no audio IDs or frozen holdout texts."""

import pytest

from homex_nlp.contracts import ExtractionRequest, ExtractionResult
from homex_nlp.engine import RulesEngine


def extract(text, currency="BOB"):
    result = RulesEngine().extract(
        ExtractionRequest(request_id="v16", text=text, currency_context=currency)
    )
    assert result.text_original == text
    assert all(text[c.start : c.end] == c.text for c in result.candidates)
    return ExtractionResult.model_validate_json(result.model_dump_json())


@pytest.mark.parametrize(
    "text",
    [
        "Un escritorio con espacio para silla",
        "Un estante a 20 cm del piso",
        "Un mueble con casilleros",
        "Una mesa sin sillas",
    ],
)
def test_secondary_out_of_scope_words_do_not_reject_furniture(text):
    assert extract(text).item_proposal is not None


@pytest.mark.parametrize("text", ["Dos sillas", "Piso flotante", "Una mesa y dos sillas"])
def test_out_of_scope_orders_still_rejected(text):
    assert extract(text).item_proposal is None


@pytest.mark.parametrize("correction", ["corrijo", "perdón", "no, mejor"])
def test_price_correction_is_exact_and_traceable(correction):
    r = extract(f"Dos escritorios precio unitario 1.500, {correction}, 1.700")
    assert r.item_proposal.price.unit_price_input == "1700.00"
    assert any(c.text == "1.500" and c.decision == "REJECTED" for c in r.candidates)


@pytest.mark.parametrize(
    "phrase",
    [
        "precio unitario -1500",
        "precio total −2500",
        "precio unitario 100 precio unitario 200",
        "precio unitario 100 o precio total 200",
    ],
)
def test_invalid_or_unresolved_prices_are_not_effective(phrase):
    r = extract("Dos escritorios " + phrase)
    assert r.item_proposal.price is None
    assert any(c.label == "PRECIO" and c.decision == "UNRESOLVED" for c in r.candidates)


def test_thicknesses_assigned_to_explicit_laterals_not_top():
    r = extract(
        "Un escritorio de melamina con tapa de 25 milímetros y laterales de 18 milímetros y tres cajones con rieles telescópicos"
    )
    assert [c.name for c in r.item_proposal.components] == ["tapa", "laterales", "cajones"]
    assert [m.component_ref for m in r.item_proposal.thicknesses] == ["pieza-1", "pieza-2"]
    assert r.item_proposal.accessories[0].component_ref == "pieza-3"


def test_color_alternative_never_projects_as_two_selected_values():
    r = extract("Un escritorio blanco o nogal")
    colors = [c for c in r.candidates if c.label == "COLOR"]
    assert len(colors) == 2
    assert all(c.decision == "UNRESOLVED" for c in colors)
    assert r.item_proposal.primary_color is None


def test_wood_color_does_not_create_wood_material_without_color_prefix():
    r = extract("Un escritorio de melamina madera clara")
    assert [c.text for c in r.candidates if c.label == "MATERIAL"] == ["melamina"]


@pytest.mark.parametrize("value", ["0.125", "0,125", "1.2345"])
def test_dimension_decimals_are_not_money_thousands(value):
    r = extract(f"Un escritorio ancho {value} metros")
    assert r.item_proposal.dimensions[0].value == value.replace(",", ".")


@pytest.mark.parametrize("case", [str.lower, str.upper, lambda t: t.replace(" ", "   ")])
def test_spacing_case_currency_and_internal_quantities(case):
    r = extract(case("Dos escritorios con tres cajones y cuatro repisas precio unitario 870"))
    assert r.item_proposal.quantity == 2
    assert r.item_proposal.price.unit_price_input == "870.00"
    assert sorted(c.normalized_value for c in r.candidates if c.label == "CANTIDAD_INTERNA") == [
        3,
        4,
    ]
    usd = extract(
        case("Dos escritorios con tres cajones y cuatro repisas precio unitario 870"), "USD"
    )
    assert usd.item_proposal.price.stated_amount == r.item_proposal.price.stated_amount


def test_thickness_correction_keeps_cancelled_value_evidence():
    r = extract("Un escritorio con tapa de 18 mm, perdón, de 25 mm")
    assert [m.value for m in r.item_proposal.thicknesses] == ["25"]
    assert any(c.text == "18 mm" and c.decision == "REJECTED" for c in r.candidates)


@pytest.mark.parametrize(
    "phrase", ["sin precio unitario 100", "precio unitario 1500, corrijo, 18 mm"]
)
def test_price_negation_or_measurement_correction_is_pending(phrase):
    assert extract("Un escritorio " + phrase).item_proposal.price is None


def test_negated_piece_color_never_becomes_general_color():
    r = extract("Un escritorio sin puertas blancas")
    assert not r.item_proposal.components
    assert not any(c.label == "COLOR" and c.decision == "ACCEPTED" for c in r.candidates)


def test_negative_measurement_not_proposed():
    r = extract("Un escritorio sin ancho 120 cm")
    assert not r.item_proposal.dimensions


def test_spoken_thickness_and_price_are_exact():
    r = extract(
        "Un escritorio con tablero de dieciocho milímetros. Precio unitario mil novecientos bolivianos"
    )
    assert r.item_proposal.thicknesses[0].value == "18"
    assert r.item_proposal.price.unit_price_input == "1900.00"


def test_internal_qualifier_is_preserved_literally():
    r = extract("Un escritorio con dos puertas abatibles y tres repisas interiores")
    assert [c.name for c in r.item_proposal.components] == [
        "puertas abatibles",
        "repisas interiores",
    ]


@pytest.mark.parametrize("marker", ["corrijo", "perdón", "no, mejor"])
def test_commercial_quantity_correction_does_not_multiply_internal_counts(marker):
    r = extract(f"Dos escritorios, {marker}, tres, con cuatro cajones")
    assert r.item_proposal.quantity == 3
    assert any(
        c.label == "CANTIDAD" and c.normalized_value == 2 and c.decision == "REJECTED"
        for c in r.candidates
    )


def test_correction_to_an_internal_count_does_not_become_commercial():
    r = extract("Dos escritorios con dos cajones no, mejor tres")
    assert r.item_proposal.quantity == 2


@pytest.mark.parametrize("verb", ["Anula", "Anulá", "Cancela", "Cancelá"])
def test_cancelled_order_never_produces_a_new_proposal(verb):
    assert extract(f"{verb} el pedido de tres escritorios").item_proposal is None


def test_explicit_consistent_unit_and_total_are_compatible():
    r = extract("Dos escritorios precio unitario 250 precio total 500")
    assert r.item_proposal.price.unit_price_input == "250.00"


def test_explicit_inconsistent_unit_and_total_are_unresolved():
    assert (
        extract("Dos escritorios precio unitario 250 precio total 700").item_proposal.price is None
    )


def test_reference_rounding_agrees_with_contract_and_never_changes_total():
    r = extract("128 escritorios precio total 1")
    assert r.item_proposal.price.line_total == "1.00"
    assert r.item_proposal.price.unit_price_reference == "0.007813"
    assert r.item_proposal.price.reference_is_approximate is True
    assert r.item_proposal.price.unit_price_input is None
