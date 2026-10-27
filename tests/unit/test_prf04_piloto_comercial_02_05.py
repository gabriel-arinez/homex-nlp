"""Regresiones estrictas del piloto: precios y cantidad comercial pospuesta."""

from decimal import Decimal

import pytest

from homex_nlp.contracts import ExtractionRequest
from homex_nlp.engine import RulesEngine
from homex_nlp.rules import find_price, find_products, find_quantity


def extract(text):
    return RulesEngine().extract(
        ExtractionRequest(request_id="piloto-02-05", text=text, currency_context="BOB")
    )


def test_audio_02_punctuation_before_cada_uno_is_not_a_price():
    text = (
        "Cotiza cuatro veladores de dos cajones cada uno, cada uno mide "
        "0.45 metros de ancho, 0.45 metros de profundidad y 0.60 metros "
        "de alto. Me lamina de 18 milímetros con tapacanto de PVC, "
        "color blanco, presionitario, 690 bolivianos."
    )
    match, mode = find_price(text)
    assert match is not None
    assert text[match.start : match.end] == "690"
    assert match.value == Decimal("690")
    assert mode == "PRECIO_UNITARIO"
    result = extract(text)
    assert result.status == "REQUIRES_REVIEW"
    assert result.item_proposal.quantity == 4
    assert result.item_proposal.price.stated_amount == "690.00"
    assert not any(w.code == "INVALID_PRICE" for w in result.warnings)


def test_audio_05_commercial_units_followed_by_furniture_dimension():
    text = (
        "cotiza credenza, dos unidades de 1.50 metros de ancho, "
        "0.45 metros de profundidad y 0.75 metros de alto, "
        "cuerpo de melamina de 18 milímetros, dos puertas abatibles, "
        "una división interior y dos cajones con rieles telescopicos, "
        "color gris claro, precio total negociado, "
        "5.400 bolivianos por las dos."
    )
    result = extract(text)
    assert result.status == "REQUIRES_REVIEW"
    assert result.item_proposal.quantity == 2
    assert result.item_proposal.price.mode == "TOTAL_NEGOCIADO"
    assert result.item_proposal.price.stated_amount == "5400.00"
    assert result.item_proposal.price.line_total == "5400.00"
    assert not any(w.code == "NO_QUANTITY" for w in result.warnings)
    assert any(
        text[c.start : c.end] == c.text == "dos"
        and c.label == "CANTIDAD"
        and c.decision == "ACCEPTED"
        for c in result.candidates
    )


@pytest.mark.parametrize(
    "text",
    [
        "Una credenza, dos piezas de vidrio templado.",
        "Una credenza, dos unidades de 18 milímetros.",
        "Una credenza, dos unidades de mesa.",
        "Una credenza, dos unidades de 45 centímetros de espesor.",
        "Una credenza, dos unidades para el tablero.",
    ],
)
def test_component_quantities_must_not_become_commercial_units(text):
    product = find_products(text)[0]
    assert find_quantity(text, main_product=product).value == 1
    # The product's initial «una» remains the only commercial quantity.
    result = extract(text)
    if "unidades de mesa" in text:
        # Dos muebles principales compiten; mantener la abstención segura.
        assert result.status == "NO_PROPOSAL"
        assert result.item_proposal is None
    else:
        assert result.item_proposal.quantity == 1


@pytest.mark.parametrize(
    "text",
    [
        "Cotiza credenza, dos piezas de vidrio.",
        "Cotiza credenza, dos unidades de 18 milímetros.",
        "Cotiza credenza, dos unidades de tablero.",
        "Cotiza credenza, dos unidades de 45 centímetros de espesor.",
        "Cotiza credenza, dos unidades para el tablero.",
    ],
)
def test_no_initial_quantity_does_not_infer_component_amount(text):
    assert extract(text).item_proposal.quantity is None


@pytest.mark.parametrize(
    ("text", "amount"),
    [
        ("Cuatro veladores, precio unitario 690 bolivianos", "690.00"),
        ("Cuatro veladores, presionitario, 690 bolivianos", "690.00"),
        ("Cuatro veladores, 690 bolivianos cada uno", "690.00"),
        ("Dos escritorios, precio unitario 1.150 bolivianos", "1150.00"),
    ],
)
def test_explicit_unit_amount_wins_over_repetition(text, amount):
    r = extract(text)
    assert r.item_proposal.price.mode == "PRECIO_UNITARIO"
    assert r.item_proposal.price.stated_amount == amount


def test_dangling_punctuation_cannot_be_valid_price():
    match, mode = find_price("Cotiza velador, cada uno mide 0.45 metros de ancho.")
    assert match is None
    assert mode is None
