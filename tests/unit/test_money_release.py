"""Synthetic monetary scale regressions, unrelated to private recordings."""

from decimal import Decimal

import pytest

from homex_nlp.contracts import ExtractionRequest, ExtractionResult
from homex_nlp.engine import RulesEngine
from homex_nlp.rules import price_mentions


@pytest.mark.parametrize("amount", ["10 mil", "diez mil", "10.000", "10000"])
@pytest.mark.parametrize("mode", ["unitario", "total negociado"])
def test_equivalent_monetary_scales(amount, mode):
    text = f"Tres mesas de taller. Precio {mode} {amount} bolivianos por las tres unidades."
    result = RulesEngine().extract(
        ExtractionRequest(request_id="money-synthetic", text=text, currency_context="BOB")
    )
    assert result.item_proposal.quantity == 3
    price = result.item_proposal.price
    assert price is not None
    assert price.stated_amount == "10000.00"
    assert price.mode == ("PRECIO_UNITARIO" if mode == "unitario" else "TOTAL_NEGOCIADO")
    assert price.currency == "BOB" and price.component_ref is None
    assert result.text_original == text
    for c in result.candidates:
        assert text[c.start : c.end] == c.text
    ExtractionResult.model_validate_json(result.model_dump_json())


@pytest.mark.parametrize(
    "amount,expected", [("10", "10"), ("mil ochocientos cincuenta", "1850"), ("7.280", "7280")]
)
def test_other_safe_amounts(amount, expected):
    mentions, _ = price_mentions("Precio unitario " + amount + " bolivianos")
    assert len(mentions) == 1 and mentions[0][0].value == Decimal(expected)


@pytest.mark.parametrize(
    "text",
    ["Melamina de 10 milímetros", "Dos cajones de 10 milímetros", "10 mil", "0.20 metros de ancho"],
)
def test_no_monetary_false_positives(text):
    assert price_mentions(text)[0] == []


@pytest.mark.parametrize(
    "amount",
    [
        "-10 mil",
        "−10 mil",
        "diez mil mil",
        "10 mil millones",
        "un millon",
        "mil y dos",
        "ciento y veinte",
        "0 mil",
    ],
)
def test_unsafe_scales_never_become_smaller_effective_prices(amount):
    mentions, _ = price_mentions("Precio unitario " + amount + " bolivianos")
    assert not any(m.value is not None for m, _ in mentions)


@pytest.mark.parametrize(
    "text",
    [
        "Tres mesas, precio unitario 12 mil bolivianos, sin puertas y sin cajones.",
        "Tres mesas de 0.20 metros de ancho con tablero de 10 milímetros, precio total negociado 12 mil bolivianos, sin descuento.",
    ],
)
def test_dimensions_negation_serialization_and_repeatability(text):
    engine = RulesEngine()
    req = ExtractionRequest(request_id="adversarial", text=text, currency_context="BOB")
    a = engine.extract(req)
    b = engine.extract(req)
    da = a.model_dump(mode="json")
    db = b.model_dump(mode="json")
    da.pop("latency_nlp_ms")
    db.pop("latency_nlp_ms")
    assert da == db
    assert a.item_proposal.price.stated_amount == "12000.00"
    assert "sin" in a.text_original
    if "0.20" in text:
        assert a.item_proposal.dimensions[0].value == "0.20"
        assert any(
            c.label == "ESPESOR" and c.normalized_value == ["10", "mm"] for c in a.candidates
        )
    assert all(c.text == text[c.start : c.end] for c in a.candidates)


def test_multiple_products_remain_review_not_mixed():
    t = "Dos mesas precio unitario 12 mil bolivianos y tres escritorios precio unitario 900 bolivianos"
    r = RulesEngine().extract(ExtractionRequest(request_id="multi", text=t, currency_context="BOB"))
    assert r.item_proposal is None


@pytest.mark.parametrize(
    "phrase",
    [
        "-12 mil bolivianos cada uno",
        "−12 mil bolivianos cada uno",
        "a -12 mil bolivianos cada uno",
        "precio unitario -12 mil bolivianos",
    ],
)
def test_negative_prefix_never_lost(phrase):
    mentions, _ = price_mentions(phrase)
    assert not any(m.value is not None for m, _ in mentions)


@pytest.mark.parametrize("separator", [": ", ", ", " es de "])
@pytest.mark.parametrize(
    "words,amount", [("ocho mil seiscientos", "8600.00"), ("mil setecientos", "1700.00")]
)
@pytest.mark.parametrize("mode", ["unitario", "total negociado"])
def test_spoken_money_with_explicit_marker_and_punctuation(separator, words, amount, mode):
    text = f"Tres mesas de taller. Precio {mode}{separator}{words} bolivianos."
    r = RulesEngine().extract(
        ExtractionRequest(request_id="spoken-punctuation", text=text, currency_context="BOB")
    )
    assert r.item_proposal.price.stated_amount == amount
    assert r.item_proposal.price.mode == (
        "PRECIO_UNITARIO" if mode == "unitario" else "TOTAL_NEGOCIADO"
    )
    assert all(text[c.start : c.end] == c.text for c in r.candidates)
