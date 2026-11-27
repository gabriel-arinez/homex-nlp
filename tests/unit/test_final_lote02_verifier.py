"""Independent same-element dimensional ellipses remain reviewable."""

from decimal import Decimal

import pytest

from homex_nlp.contracts import ExtractionRequest
from homex_nlp.engine import RulesEngine


def extract(text):
    result = RulesEngine().extract(
        ExtractionRequest(request_id="contextual-ellipse", text=text, currency_context="BOB")
    )
    assert result.text_original == text
    assert all(c.text == text[c.start : c.end] for c in result.candidates)
    return result


@pytest.mark.parametrize(
    "text,value",
    [
        (
            "Un armario de 85 centímetros de ancho, 48 de profundidad y dos metros de alto, "
            "fabricado en melamina de 16 milímetros.",
            "48",
        ),
        (
            "Una estantería de noventa centímetros de ancho, cincuenta y dos de profundidad "
            "y tres metros de alto. Tablero de veinte milímetros de espesor.",
            "52",
        ),
        (
            "Un escritorio con credenza. Escritorio de tres metros de ancho, "
            "noventa centímetros de alto y setenta de profundidad. "
            "Credenza de dos metros de ancho, sesenta centímetros de alto y cincuenta de profundidad.",
            "70",
        ),
    ],
)
def test_same_owner_same_scale_context_precedes_profile(text, value):
    result = extract(text)
    depth = next(
        d for d in result.item_proposal.dimensions if d.axis == "profundidad" and d.value == value
    )
    assert depth.unit == "cm"
    assert Decimal(depth.value_mm) == Decimal(value) * 10
    own = [c for c in result.candidates if c.candidate_id in depth.evidence_ids]
    inferred = [
        c
        for c in own
        if isinstance(c.normalized_value, dict) and c.normalized_value.get("unit_inferred")
    ]
    assert inferred
    assert all(c.decision == "UNRESOLVED" for c in inferred)
    assert all(c.candidate_id in result.item_proposal.unresolved for c in inferred)
    assert any(c.candidate_id not in {i.candidate_id for i in inferred} for c in own)
    assert any(w.code == "MISSING_UNIT" and w.severity == "REVIEW" for w in result.warnings)
    assert all(
        c.component_ref == depth.component_ref
        for c in own
        if c.label in {"ANCHO", "ALTO", "PROFUNDIDAD"}
    )


@pytest.mark.parametrize(
    "text",
    [
        "Un escritorio de 95 cm de ancho y 90 mm de alto y 55 de profundidad.",
        "Un escritorio con credenza. Escritorio de 90 cm de ancho. Credenza de 1 metro de alto y 55 de profundidad.",
        "Un escritorio de 90 cm de ancho con soporte de 55 de profundidad y 2 metros de alto.",
    ],
)
def test_conflicting_or_other_owner_units_do_not_license_ellipsis(text):
    result = extract(text)
    depth = next(d for d in result.item_proposal.dimensions if d.axis == "profundidad")
    evidence = [c for c in result.candidates if c.candidate_id in depth.evidence_ids]
    assert not any(c.reason and "same-magnitude" in c.reason for c in evidence)


def test_explicit_atypical_depth_is_never_replaced():
    result = extract("Un armario de 85 cm de ancho, 48 metros de profundidad y dos metros de alto.")
    depth = next(d for d in result.item_proposal.dimensions if d.axis == "profundidad")
    assert depth.unit == "m" and depth.value_mm == "48000"
