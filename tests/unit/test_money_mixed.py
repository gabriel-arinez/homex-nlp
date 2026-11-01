"""Synthetic full-token monetary capture regressions."""

from decimal import Decimal

import pytest

from homex_nlp.rules import price_mentions


@pytest.mark.parametrize(
    "amount", ["10 mil 500", "diez mil 500", "10 mil quinientos", "diez mil quinientos"]
)
@pytest.mark.parametrize(
    "template,mode",
    [
        ("precio unitario {} bolivianos", "PRECIO_UNITARIO"),
        ("precio unitario {}", "PRECIO_UNITARIO"),
        ("{} bolivianos cada uno", "PRECIO_UNITARIO"),
        ("precio total negociado {} bolivianos", "TOTAL_NEGOCIADO"),
        ("precio unitario 900, corrijo {} bolivianos", "PRECIO_UNITARIO"),
    ],
)
def test_complete_mixed_capture(amount, template, mode):
    text = template.format(amount)
    matches, _ = price_mentions(text)
    m, actual_mode = matches[-1]
    assert m.value == Decimal("10500")
    assert m.text == amount
    assert text[m.start : m.end] == amount
    assert actual_mode == mode


@pytest.mark.parametrize(
    "amount",
    [
        "10 mil 500 20",
        "10 mil500",
        "diez mil500",
        "10 mil 500foo",
        "diez mil 500 20",
        "10 mil mil",
        "10 mil -500",
        "10 mil −500",
        "10 mil - 500",
        "10 mil − 500",
        "10 mil 1000",
        "10 mil 0.5",
        "10 500",
        "diez diez",
        "10 mil millones",
        "diez mil quinientos veinte treinta cuarenta cincuenta sesenta setenta ochenta noventa",
    ],
)
@pytest.mark.parametrize(
    "template",
    [
        "precio unitario {} bolivianos",
        "{} bolivianos cada uno",
        "precio unitario 900, corrijo {} bolivianos",
    ],
)
def test_no_valid_fragment_of_malformed_amount(amount, template):
    matches, _ = price_mentions(template.format(amount))
    # A preceding corrected value may remain as evidence, but no effective replacement.
    assert not matches or matches[-1][0].value is None


@pytest.mark.parametrize(
    "suffix", [" bolivianos, 3 mesas", " bolivianos ancho 20 cm", " bolivianos y 3 cajones"]
)
def test_other_specification_does_not_extend_price(suffix):
    matches, _ = price_mentions("precio unitario 10 mil 500" + suffix)
    assert matches[0][0].value == Decimal("10500")


@pytest.mark.parametrize("amount", ["10 mil 500", "diez mil 500", "10 mil 500 20", "10 mil - 500"])
@pytest.mark.parametrize("mode", ["unitario", "total negociado"])
def test_engine_mixed_amount_preserves_contract(amount, mode):
    from homex_nlp.contracts import ExtractionRequest, ExtractionResult
    from homex_nlp.engine import RulesEngine

    text = f"Tres mesas de 0.20 metros de ancho. Precio {mode} {amount} bolivianos."
    result = RulesEngine().extract(
        ExtractionRequest(request_id="mixed", text=text, currency_context="BOB")
    )
    assert result.text_original == text
    assert result.item_proposal.quantity == 3
    assert result.item_proposal.dimensions[0].value == "0.20"
    assert all(text[c.start : c.end] == c.text for c in result.candidates)
    ExtractionResult.model_validate_json(result.model_dump_json())
    if amount in {"10 mil 500", "diez mil 500"}:
        assert result.item_proposal.price.stated_amount == "10500.00"
        assert result.item_proposal.price.mode == (
            "PRECIO_UNITARIO" if mode == "unitario" else "TOTAL_NEGOCIADO"
        )
    else:
        assert result.item_proposal.price is None
