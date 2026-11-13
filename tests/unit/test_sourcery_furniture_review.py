"""Public regression probes for the reproduced furniture review findings."""

import inspect

import pytest

from homex_nlp.contracts import ExtractionRequest
from homex_nlp.engine import RulesEngine
from homex_nlp.rules import find_accessory_quantity


def extract(text):
    result = RulesEngine().extract(
        ExtractionRequest(request_id="review", text=text, currency_context="BOB")
    )
    assert result.text_original == text
    assert all(c.text == text[c.start : c.end] for c in result.candidates)
    return result


@pytest.mark.parametrize(
    "text",
    [
        "Mesa, mesa de madera",
        "Escritorio con cajonera, cajonera de madera",
        "Dos mesas, una de madera y otra metálica",
        "Mesa y un escritorio",
        "Escritorio y una cajonera independiente",
    ],
)
def test_independent_or_ambiguous_mentions_are_not_silently_merged(text):
    result = extract(text)
    assert result.item_proposal is None or any(
        c.decision == "UNRESOLVED" for c in result.candidates
    )


@pytest.mark.parametrize(
    "phrase", ["casillero", "una cajonera", "dos cajoneras", "cajonera integrada"]
)
def test_explicit_composition_preserves_component_and_evidence(phrase):
    result = extract(f"Un escritorio con {phrase}")
    assert result.item_proposal is not None
    assert result.item_proposal.quantity == 1
    component = next(c for c in result.item_proposal.components if c.name in phrase)
    assert any(
        c.candidate_id in component.evidence_ids and c.label == "COMPONENTE"
        for c in result.candidates
    )


@pytest.mark.parametrize(
    "text,expected",
    [
        ("Mesa. Ancho 60 cm alto 75 cm", {"ancho": "600", "alto": "750"}),
        ("Armario. Alto 180 cm ancho 80 cm", {"alto": "1800", "ancho": "800"}),
        ("Armario alto de 80 cm de ancho", {"ancho": "800"}),
        (
            "Mesa. Largo 150 cm, ancho 60 cm y alto 75 cm",
            {"largo": "1500", "ancho": "600", "alto": "750"},
        ),
        ("Mesa de 60 cm de ancho y 75 cm de alto", {"ancho": "600", "alto": "750"}),
    ],
)
def test_separately_valued_adjacent_axes_and_adjective_guard(text, expected):
    item = extract(text).item_proposal
    assert item is not None
    assert {d.axis: d.value_mm for d in item.dimensions} == expected


@pytest.mark.parametrize(
    "phrase,count",
    [
        ("USB, 2 unidades", 2),
        ("Dos puertos USB", 2),
        ("USB a 20 BOB", None),
        ("USB a 20", None),
        ("4 HDMI a 30 BOB", 4),
        ("USB 3.0", None),
        ("USB (2)", 2),
        ("dos o tres USB", None),
        ("menos dos USB", None),
    ],
)
def test_explicit_accessory_units_never_infer_money_or_protocol_counts(phrase, count):
    item = extract(f"Una mesa con {phrase}").item_proposal
    assert item is not None
    assert item.accessories[0].quantity == count


@pytest.mark.parametrize(
    "text,count",
    [
        ("Veinte escritorios, no, mejor veinticinco", 25),
        ("Doce mesas, perdón, mejor quince", 15),
        ("Diez mesas, no, mejor dos", 2),
        ("Una mesa con dos cajones", 1),
    ],
)
def test_full_commercial_correction_grammar_and_existing_counts(text, count):
    assert extract(text).item_proposal.quantity == count


def test_different_product_is_not_a_same_product_count_correction():
    result = extract("Diez mesas, no veinte escritorios")
    assert result.item_proposal is None


def test_compound_internal_correction_never_keeps_stale_count():
    result = extract("Un escritorio con treinta cajones, corrijo mejor treinta y dos")
    assert result.item_proposal is not None
    quantities = [c for c in result.candidates if c.label == "CANTIDAD_INTERNA"]
    assert any(c.normalized_value == 32 for c in quantities)
    assert not any(c.normalized_value == 30 and c.decision == "ACCEPTED" for c in quantities)
    assert not any(
        c.normalized_value == 30 and c.decision == "ACCEPTED"
        for c in result.candidates
        if c.label == "CANTIDAD_ACCESORIO"
    )


def test_accessory_context_search_is_bounded_not_full_prefix():
    source = inspect.getsource(find_accessory_quantity)
    assert "text[: offset" not in source
    result = extract("Una mesa sin USB y con dos HDMI")
    assert all("USB" not in a.name for a in result.item_proposal.accessories)
    assert result.item_proposal.accessories[0].quantity == 2


def test_legacy_component_correction_also_retires_stale_accessory_evidence():
    result = extract("Una mesa con tres cajones, no, mejor dos")
    assert any(
        c.label == "CANTIDAD_INTERNA" and c.normalized_value == 2 and c.decision == "ACCEPTED"
        for c in result.candidates
    )
    assert not any(
        c.label == "CANTIDAD_ACCESORIO" and c.normalized_value == 3 and c.decision == "ACCEPTED"
        for c in result.candidates
    )


def test_negated_article_product_and_coordinated_dimension_piece_keep_prior_behavior():
    item = extract("Una mesa, no un escritorio").item_proposal
    assert item is not None and item.name == "mesa" and item.quantity == 1
    result = extract("Un escritorio de ancho un metro y dos cajones.")
    assert [(d.axis, d.value_mm) for d in result.item_proposal.dimensions] == [("ancho", "1000")]
    assert [c.normalized_value for c in result.candidates if c.label == "CANTIDAD_INTERNA"] == [2]


@pytest.mark.parametrize(
    "text,expected",
    [
        (
            "Armario alto de 80 centímetros de ancho 50 de profundidad",
            [("ancho", "80", "cm", "800"), ("profundidad", "50", None, None)],
        ),
        (
            "Mesa de 3 metros 20 de largo 1 metro 30 de ancho",
            [("ancho", "130", "cm", "1300"), ("largo", "320", "cm", "3200")],
        ),
    ],
)
def test_postfix_axis_role_is_not_reused_as_the_next_dimension_prefix(text, expected):
    item = extract(text).item_proposal
    assert item is not None
    assert [(d.axis, d.value, d.unit, d.value_mm) for d in item.dimensions] == expected
