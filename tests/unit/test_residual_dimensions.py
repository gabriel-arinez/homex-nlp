"""Contextual units remain proposals rather than blind inheritance."""

import pytest

from homex_nlp.contracts import ExtractionRequest
from homex_nlp.engine import RulesEngine


def extract(text):
    result = RulesEngine().extract(
        ExtractionRequest(request_id="residual", text=text, currency_context="BOB")
    )
    assert all(text[c.start : c.end] == c.text for c in result.candidates)
    return result


@pytest.mark.parametrize(
    "text,values",
    [
        ("Una mesa de dos metros de largo, sesenta de ancho y setenta de alto", {"60", "70"}),
        ("Un escritorio de 2 metros de largo y 60 de fondo", {"60"}),
        ("Un escritorio con credenza de 1 metro de alto y 55 de profundidad", {"55"}),
        ("Una mesa de 1 metro de alto y 65 de ancho", {"65"}),
    ],
)
def test_implausible_meter_ellipsis(text, values):
    result = extract(text)
    dims = [d for d in result.item_proposal.dimensions if d.value in values]
    assert len(dims) == len(values)
    assert all(d.unit == "cm" for d in dims)
    assert all(
        any(
            c.candidate_id in d.evidence_ids and c.decision == "UNRESOLVED"
            for c in result.candidates
        )
        for d in dims
    )


def test_multiple_plausible_units_abstain():
    result = extract("Una mesa de 2 metros de largo y 600 de ancho")
    assert next(d for d in result.item_proposal.dimensions if d.value == "600").unit is None


def test_explicit_custom_size_retained_and_warned():
    result = extract("Una mesa de 60 metros de ancho")
    assert result.item_proposal.dimensions[0].unit == "m"
    assert any(w.severity == "REVIEW" and "atypical" in w.message.lower() for w in result.warnings)
