"""Unit evidence follows its owner and does not read unrelated clauses."""

from homex_nlp.contracts import ExtractionRequest
from homex_nlp.engine import RulesEngine


def extract(text):
    return RulesEngine().extract(
        ExtractionRequest(request_id="unit-scope", text=text, currency_context="BOB")
    )


def test_later_board_description_does_not_override_main_furniture_profile():
    item = extract("Una mesa de dos por tres con tablero de melamina.").item_proposal
    assert len(item.dimensions) == 2
    assert all(d.unit == "m" and d.axis is None for d in item.dimensions)


def test_connector_terminates_explicit_unit_enumeration_even_without_punctuation():
    result = extract("Una mesa de 90 cm de ancho con soporte de 50 de profundidad.")
    evidence = [c for c in result.candidates if c.label == "PROFUNDIDAD"]
    assert evidence
    assert not any(c.reason and "same-owner" in c.reason for c in evidence)


def test_shared_board_thickness_unit_preserves_both_complete_values():
    result = extract("Un escritorio de melamina de dieciocho y treinta y seis milímetros.")
    assert [m.value_mm for m in result.item_proposal.thicknesses] == ["18", "36"]
    assert any(c.reason and "shared" in c.reason.lower() for c in result.candidates)


def test_single_cardinal_does_not_split_into_two_thicknesses():
    result = extract("Un escritorio de melamina de treinta y seis milímetros.")
    assert [m.value_mm for m in result.item_proposal.thicknesses] == ["36"]
