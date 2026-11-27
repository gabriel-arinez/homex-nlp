"""Public-contract regressions for scalar parsing and reviewable unit inference."""

from decimal import Decimal

import pytest

from homex_nlp.contracts import ExtractionRequest, ExtractionResult
from homex_nlp.engine import RulesEngine


def extract(text):
    result = RulesEngine().extract(
        ExtractionRequest(request_id="magnitudes", text=text, currency_context="BOB")
    )
    assert result.text_original == text
    assert all(text[c.start : c.end] == c.text for c in result.candidates)
    ExtractionResult.model_validate_json(result.model_dump_json())
    return result


@pytest.mark.parametrize(
    "phrase,cm",
    [
        ("un metro veinte", "120"),
        ("un metro y medio", "150"),
        ("medio metro", "50"),
        ("dos metros y cuarto", "225"),
        ("dos metros con treinta centímetros", "230"),
    ],
)
def test_complete_compound_measurement(phrase, cm):
    result = extract(f"Una mesa de {phrase} de largo.")
    dimensions = result.item_proposal.dimensions
    assert len(dimensions) == 1
    assert Decimal(dimensions[0].value_mm) == Decimal(cm) * 10
    assert phrase in dimensions[0].original_text


@pytest.mark.parametrize(
    "phrase,unit,values",
    [
        ("dos por tres", "m", [2, 3]),
        ("cincuenta y cinco por cincuenta y cinco", "cm", [55, 55]),
        ("ciento veinte por sesenta", "cm", [120, 60]),
        ("120 × 60 cm", "cm", [120, 60]),
        ("1,2 x 0.6 metros", "m", [1.2, 0.6]),
    ],
)
def test_chain_keeps_axes_pending_and_units_traceable(phrase, unit, values):
    result = extract(f"Una mesa de {phrase}.")
    dims = result.item_proposal.dimensions
    assert [float(d.value) for d in dims] == values
    assert all(d.axis is None and d.unit == unit for d in dims)
    assert any(w.code == "MISSING_AXIS" for w in result.warnings)
    if "cm" not in phrase and "metros" not in phrase:
        assert all(
            any(
                c.reason and "infer" in c.reason.lower()
                for c in result.candidates
                if c.candidate_id in d.evidence_ids
            )
            for d in dims
        )
        assert result.item_proposal.unresolved


def test_local_enumeration_unit_is_inferred_without_changing_axes():
    result = extract("Una mesa de 90 centímetros de ancho, 43 de profundidad y 70 de alto.")
    dims = result.item_proposal.dimensions
    assert {d.axis: d.unit for d in dims} == {"ancho": "cm", "profundidad": "cm", "alto": "cm"}
    assert any(c.reason and "infer" in c.reason.lower() for c in result.candidates)


def test_explicit_atypical_unit_is_not_replaced():
    result = extract("Una mesa de 120 metros de ancho.")
    assert result.item_proposal.dimensions[0].unit == "m"


def test_accessory_length_is_not_thickness():
    result = extract("Una mesa con rieles de 450 mm.")
    assert not result.item_proposal.thicknesses


@pytest.mark.parametrize("phrase,mm", [("espesor de 1,8 cm", 18), ("espesor de dieciocho mm", 18)])
def test_explicit_thickness_units(phrase, mm):
    result = extract(f"Una mesa de melamina con {phrase}.")
    assert len(result.item_proposal.thicknesses) == 1
    assert Decimal(result.item_proposal.thicknesses[0].value_mm) == mm


@pytest.mark.parametrize(
    "phrase", ["300 por 300", "2 por 3 por 4 por 5", "-2 x 3", "dos metros y cinco de largo"]
)
def test_ambiguous_or_invalid_measurements_are_not_guessed(phrase):
    result = extract(f"Una mesa de {phrase}.")
    assert all(d.unit is None for d in result.item_proposal.dimensions)


def test_internal_counts_and_prices_are_not_dimensions():
    result = extract("Una mesa con tres cajones y cuatro ruedas. Precio de 13 mil 200 bolivianos.")
    assert result.item_proposal.quantity == 1
    assert not result.item_proposal.dimensions
    assert not result.item_proposal.thicknesses


def test_unitless_thickness_stays_pending():
    result = extract("Una mesa de 90 cm de ancho con espesor de 18.")
    assert result.item_proposal.thicknesses[0].unit is None
    assert any(
        w.path == "/item_proposal/thicknesses" and w.code == "MISSING_UNIT" for w in result.warnings
    )
