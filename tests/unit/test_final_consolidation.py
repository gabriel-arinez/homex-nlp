"""Contract-derived consolidation regressions; no frozen case IDs or memorized outputs."""

import pytest

from homex_nlp.contracts import ExtractionRequest, ExtractionResult
from homex_nlp.engine import RulesEngine


def extract(text):
    return RulesEngine().extract(
        ExtractionRequest(request_id="final", text=text, currency_context="BOB")
    )


@pytest.mark.parametrize("prefix", ["Escritorio", "Mesa de reunión", "Credenza"])
@pytest.mark.parametrize(
    "prices", ["precio unitario 600,00. total 2400,00", "total 2400 precio unitario 600"]
)
def test_explicit_prices_survive_unknown_quantity(prefix, prices):
    r = extract(prefix + ". " + prices)
    assert r.item_proposal.quantity is None
    assert r.item_proposal.price.unit_price_input == "600.00"
    assert r.item_proposal.price.line_total is None
    assert any(
        c.label == "PRECIO_TOTAL" and c.normalized_value == "2400.00" and c.decision == "ACCEPTED"
        for c in r.candidates
    )
    assert any(w.code == "NO_QUANTITY" for w in r.warnings)
    ExtractionResult.model_validate_json(r.model_dump_json())


@pytest.mark.parametrize(
    "text",
    [
        "Un escritorio de melamina dieciocho milímetros",
        "Una credenza con tapacanto PVC de dos milímetros",
    ],
)
def test_oral_thickness_without_representable_piece_is_pending(text):
    r = extract(text)
    assert not r.item_proposal.thicknesses
    pending = [c for c in r.candidates if c.label == "ESPESOR"]
    assert pending and all(c.decision == "UNRESOLVED" for c in pending)
    assert all(c.candidate_id in r.item_proposal.unresolved for c in pending)
    assert all(text[c.start : c.end] == c.text for c in pending)


def test_scoped_spoken_thickness_keeps_exact_piece():
    r = extract(
        "Un escritorio con tapa de veinticinco milímetros y laterales de dieciocho milímetros"
    )
    assert [(m.value, m.component_ref) for m in r.item_proposal.thicknesses] == [
        ("25", "pieza-1"),
        ("18", "pieza-2"),
    ]


def test_conflict_keeps_independent_technical_fields():
    r = extract("Dos escritorios con tapa de 25 mm precio unitario 600 precio total 900")
    assert r.item_proposal.price is None
    assert r.item_proposal.quantity == 2
    assert r.item_proposal.thicknesses[0].value == "25"


def test_differing_totals_do_not_hide_behind_a_unit_without_quantity():
    r = extract("Escritorio precio unitario 600 total 1200 total 2400")
    assert r.item_proposal.price is None


def test_differing_units_remain_ambiguous_without_quantity():
    assert (
        extract("Escritorio precio unitario 600 total 1200 precio unitario 800").item_proposal.price
        is None
    )


@pytest.mark.parametrize(
    "chain",
    [
        "no mejor tres no mejor cuatro",
        "corrijo tres, corrijo cuatro",
        "no, mejor tres, no, mejor cuatro",
    ],
)
def test_chained_commercial_correction_never_keeps_intermediate_quantity(chain):
    r = extract("Dos escritorios " + chain + " con cinco cajones")
    assert r.item_proposal.quantity == 4
    assert [
        c.normalized_value
        for c in r.candidates
        if c.label == "CANTIDAD" and c.decision == "ACCEPTED"
    ] == [4]


def test_invalid_quantity_correction_is_pending():
    r = extract("Dos escritorios, corrijo cero con tres cajones")
    assert r.item_proposal.quantity is None


def test_component_rectification_does_not_choose_a_later_conflicting_price():
    r = extract(
        "Escritorio precio unitario 600 con tapa de 18 mm, perdón, de 25 mm; precio unitario 700"
    )
    assert r.item_proposal.price is None


def test_negative_thickness_is_not_made_positive():
    assert not extract("Un escritorio con tapa de -18 mm").item_proposal.thicknesses


def test_negative_commercial_quantity_does_not_become_positive():
    assert extract("Necesito -2 escritorios precio unitario 600").item_proposal.quantity is None


def test_prices_use_corrected_commercial_quantity():
    r = extract(
        "Dos escritorios, corrijo tres con dos cajones precio unitario 600 precio total 1800"
    )
    assert r.item_proposal.quantity == 3
    assert r.item_proposal.price.unit_price_input == "600.00"
    assert r.item_proposal.price.line_total == "1800.00"


def test_runtime_does_not_import_ner_or_research_packages(monkeypatch):
    import builtins

    original = builtins.__import__

    def guarded(name, *args, **kwargs):
        assert not name.startswith(("spacy", "training", "transformers"))
        return original(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded)
    r = extract("Dos escritorios con tres cajones precio unitario 700")
    assert r.engine.mode == "RULES_ONLY" and r.engine.model_version is None


def test_total_correction_may_repeat_its_modality():
    r = extract("Tres mesas total 1800, corrijo total 2100")
    assert r.item_proposal.price.line_total == "2100.00"
    assert any(c.text == "1800" and c.decision == "REJECTED" for c in r.candidates)


def test_color_alternative_does_not_cancel_independent_explicit_prices():
    r = extract("Escritorio precio unitario 600, color blanco o nogal, total 2400")
    assert r.item_proposal.price.unit_price_input == "600.00"
    assert any(c.label == "PRECIO_TOTAL" and c.decision == "ACCEPTED" for c in r.candidates)
    assert all(c.decision == "UNRESOLVED" for c in r.candidates if c.label == "COLOR")


def test_support_lateral_is_an_accessory_not_an_extra_lateral_piece():
    r = extract("Un escritorio con dos cajones y un soporte lateral para CPU")
    assert [c.name for c in r.item_proposal.components] == ["cajones"]
    assert any("soporte lateral para CPU" == a.name for a in r.item_proposal.accessories)


def test_compound_main_name_does_not_create_its_own_component():
    r = extract("Un estante de pared, una unidad, con cinco repisas abiertas")
    assert [c.name for c in r.item_proposal.components] == ["repisas abiertas"]
    assert not any(c.normalized_value == 1 for c in r.candidates if c.label == "CANTIDAD_INTERNA")


def test_integrated_drawer_unit_description_is_not_a_second_unit():
    r = extract("Un escritorio con cajonera rodante integrada. Cajonera con dos cajones")
    assert [c.name.casefold() for c in r.item_proposal.components] == ["cajonera", "cajones"]
