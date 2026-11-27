"""Independent public-interface guards for the final regression correction."""

import pytest

from homex_nlp.contracts import ExtractionRequest
from homex_nlp.engine import RulesEngine


def extract(text):
    result = RulesEngine().extract(
        ExtractionRequest(request_id="closure", text=text, currency_context="BOB")
    )
    assert result.text_original == text
    assert all(c.text == text[c.start : c.end] for c in result.candidates)
    return result


@pytest.mark.parametrize(
    "text,expected",
    [
        ("Una mesa de ancho un metro y cuatro cajones.", [("ancho", "1000")]),
        (
            "Una mesa de ancho dos metros treinta y alto noventa centímetros.",
            [("ancho", "2300"), ("alto", "900")],
        ),
        (
            "Una mesa de 2 metros 40 de largo 1 metro 10 de ancho.",
            [("ancho", "1100"), ("largo", "2400")],
        ),
    ],
)
def test_numeric_conjunctions_preserve_separate_fields(text, expected):
    assert [(d.axis, d.value_mm) for d in extract(text).item_proposal.dimensions] == expected


@pytest.mark.parametrize(
    "phrase",
    [
        "un metro 030",
        "tres metro cuarenta",
        "un metros treinta",
        "1.4 metros treinta",
        "un metro 30 pulgadas",
    ],
)
def test_malformed_compound_never_yields_partial_axis(phrase):
    for text in (f"Una mesa de {phrase} de ancho", f"Una mesa de ancho {phrase}"):
        assert extract(text).item_proposal.dimensions == []


def test_thickness_correction_preserves_owner_and_rejected_evidence():
    result = extract("Una mesa con tapa de MDF blanco de 16 mm, perdón, de 22 mm")
    assert [(m.value, m.component_ref) for m in result.item_proposal.thicknesses] == [
        ("22", "pieza-1")
    ]
    assert any(
        c.label == "ESPESOR" and c.text == "16 mm" and c.decision == "REJECTED"
        for c in result.candidates
    )


def test_compact_chain_is_complete_and_does_not_invent_axes():
    result = extract("Una mesa de 42x52x72cm.")
    assert [(d.value_mm, d.axis) for d in result.item_proposal.dimensions] == [
        ("420", None),
        ("520", None),
        ("720", None),
    ]
    assert not result.item_proposal.thicknesses


@pytest.mark.parametrize(
    "values,expected", [("treinta y seis", ["36"]), ("dieciocho y treinta y seis", ["18", "36"])]
)
def test_explicit_substrate_gauges_keep_owner_pending(values, expected):
    result = extract(f"Una mesa de melamina de {values} milímetros.")
    assert [m.value_mm for m in result.item_proposal.thicknesses] == expected
    for measurement in result.item_proposal.thicknesses:
        assert measurement.component_ref is None
        assert any(
            c.label == "ESPESOR"
            and c.decision == "UNRESOLVED"
            and c.component_ref is None
            and c.candidate_id in result.item_proposal.unresolved
            for c in result.candidates
            if c.candidate_id in measurement.evidence_ids
        )
