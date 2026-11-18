"""Generic furniture uses positive description evidence, not dimensions as a gate."""

import pytest

from homex_nlp.contracts import ExtractionRequest
from homex_nlp.engine import RulesEngine


def extract(text):
    result = RulesEngine().extract(
        ExtractionRequest(request_id="generic-0130", text=text, currency_context="BOB")
    )
    assert all(c.text == text[c.start : c.end] for c in result.candidates)
    return result


@pytest.mark.parametrize(
    "detail",
    [
        "de MDF",
        "de vidrio",
        "con ruedas",
        "con iluminación LED",
        "con acabado lacado",
        "con superficie antimicrobiana",
        "con revestimiento de corcho",
    ],
)
def test_described_generic_furniture_is_a_partial_proposal(detail):
    result = extract(f"Un mueble {detail}")
    proposal = result.item_proposal
    assert proposal is not None
    assert proposal.name == "mueble"
    assert proposal.price is None
    assert not proposal.dimensions
    assert not proposal.thicknesses
    assert proposal.primary_color is None
    assert proposal.observations is None


@pytest.mark.parametrize(
    "text",
    [
        "Un mueble",
        "mueble",
        "Un mueble con",
        "Un mueble de",
        "Un mueble con eso",
        "Un mueble con el micrófono para probar el audio",
    ],
)
def test_missing_or_noncommercial_description_abstains(text):
    assert extract(text).item_proposal is None


def test_unknown_description_is_preserved_for_review_not_invented_as_an_attribute():
    text = "Un mueble con revestimiento de corcho"
    result = extract(text)
    assert result.item_proposal is not None
    detail = [c for c in result.candidates if c.label == "DESCRIPCION_COMERCIAL"]
    assert detail and all(c.decision == "UNRESOLVED" for c in detail)
    assert detail[0].text == "con revestimiento de corcho"
    assert any(w.code == "UNKNOWN_TERM" for w in result.warnings)


def test_existing_detailed_furniture_keeps_its_values():
    result = extract("Un mueble de madera de 120 cm de ancho. Precio unitario 500 bolivianos.")
    assert result.item_proposal is not None
    assert result.item_proposal.price.stated_amount == "500.00"
    assert any(d.axis == "ancho" and d.value_mm == "1200" for d in result.item_proposal.dimensions)
