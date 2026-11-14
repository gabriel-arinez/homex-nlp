"""Independent language probes for explicit counts, price labels and clause limits."""

from decimal import Decimal

import pytest

from homex_nlp.contracts import ExtractionRequest
from homex_nlp.engine import RulesEngine


def extract(text):
    result = RulesEngine().extract(
        ExtractionRequest(request_id="commercial-value-probe", text=text, currency_context="BOB")
    )
    assert result.text_original == text
    assert all(c.text == text[c.start : c.end] for c in result.candidates)
    assert result.item_proposal is not None
    return result


@pytest.mark.parametrize(
    "words,expected",
    [
        ("Once", 11),
        ("Veintiún", 21),
        ("Veinticinco", 25),
        ("Treinta y dos", 32),
        ("Ciento veinticinco", 125),
        ("Doscientos cincuenta", 250),
        ("Mil cien", 1100),
    ],
)
def test_explicit_commercial_word_counts_reuse_the_strict_integer_grammar(words, expected):
    result = extract(f"{words} escritorios de 95 cm de ancho. Precio unitario 700 bolivianos.")
    assert result.item_proposal.quantity == expected
    assert result.item_proposal.price.mode == "PRECIO_UNITARIO"
    assert result.item_proposal.price.line_total == f"{expected * 700}.00"
    assert not any(w.code == "NO_QUANTITY" for w in result.warnings)


@pytest.mark.parametrize(
    "text",
    [
        "Escritorios; cantidad comercial veinticinco piezas.",
        "Escritorios, se cotizan veinticinco unidades.",
        "Escritorios, veinticinco piezas tamaño 95 cm de ancho.",
    ],
)
def test_same_word_count_is_supported_in_explicit_and_postposed_forms(text):
    assert extract(text).item_proposal.quantity == 25


@pytest.mark.parametrize(
    "number",
    ["Treinta y dos y tres", "Treinta con cinco", "Veinticinco o treinta", "-25", "1.5"],
)
def test_invalid_or_alternative_counts_never_become_a_valid_suffix(number):
    result = extract(f"{number} escritorios de 95 cm de ancho.")
    assert result.item_proposal.quantity is None
    assert any(w.code == "NO_QUANTITY" for w in result.warnings)


def test_component_counts_do_not_become_commercial_quantity():
    result = extract("Una mesa con veinticinco conectores HDMI.")
    assert result.item_proposal.quantity == 1
    assert next(a for a in result.item_proposal.accessories if "HDMI" in a.name).quantity == 25


@pytest.mark.parametrize("quantity", ["Tres", "3", "25"])
def test_previous_word_and_digit_commercial_counts_keep_their_values(quantity):
    expected = 3 if quantity in {"Tres", "3"} else 25
    assert extract(f"{quantity} escritorios de 95 cm de ancho.").item_proposal.quantity == expected


@pytest.mark.parametrize("label", ["Preciunitario", "Presiunitario", "Precio unitario"])
def test_fused_explicit_unit_price_label_retains_original_evidence(label):
    result = extract(f"Dos estantes. {label} de 625,50 bolivianos.")
    price = result.item_proposal.price
    assert price.mode == "PRECIO_UNITARIO"
    assert price.stated_amount == "625.50"
    assert price.line_total == "1251.00"
    assert any(
        c.text == "625,50" for c in result.candidates if c.candidate_id in price.evidence_ids
    )


@pytest.mark.parametrize(
    "phrase",
    [
        "Parece unitario de 625 bolivianos",
        "Precio de 625 bolivianos",
        "Preciunitario de 85 centímetros",
        "mueblepreciunitario de 625 bolivianos",
    ],
)
def test_ambiguous_or_geometric_phrases_never_acquire_unit_price_mode(phrase):
    assert extract(f"Dos estantes. {phrase}.").item_proposal.price is None


def test_explicit_total_is_not_changed_by_the_unit_price_label_extension():
    price = extract("Dos escritorios. Total negociado 1250 bolivianos.").item_proposal.price
    assert price.mode == "TOTAL_NEGOCIADO"
    assert price.stated_amount == "1250.00"
    assert price.unit_price_input is None


@pytest.mark.parametrize("boundary", [",", ";", "."])
def test_explicit_height_after_a_separate_compound_clause_is_not_discarded(boundary):
    result = extract(
        f"Un escritorio de un metro treinta por un metro treinta{boundary} "
        "ochenta centímetros de alto y cincuenta y cinco de profundidad."
    )
    dimensions = result.item_proposal.dimensions
    assert [(d.value_mm, d.unit) for d in dimensions if d.axis == "alto"] == [("800", "cm")]
    depth = next(d for d in dimensions if d.axis == "profundidad")
    assert Decimal(depth.value) == 55 and depth.unit is None and depth.value_mm is None
    assert not any(d.axis in {"ancho", "largo"} for d in dimensions)
    assert any(w.code == "MISSING_UNIT" for w in result.warnings)


@pytest.mark.parametrize("phrase", ["un metro 5", "dos metros cinco", "setenta y cinco y sesenta"])
def test_same_clause_ambiguous_dimension_fragments_remain_unresolved(phrase):
    dimensions = extract(f"Una mesa de {phrase} de ancho.").item_proposal.dimensions
    assert not any(d.axis == "ancho" for d in dimensions)


@pytest.mark.parametrize(
    "count,expected,width,mm",
    [("Veinticinco", 25, "ochenta", "800"), ("Tres", 3, "noventa", "900")],
)
def test_contextual_furniture_uses_the_same_complete_cardinal_grammar(count, expected, width, mm):
    result = extract(f"{count} credencias de {width} centímetros de ancho, cuerpo de melamina.")
    assert result.item_proposal.quantity == expected
    assert result.item_proposal.name == "credencias"
    assert any(d.axis == "ancho" and d.value_mm == mm for d in result.item_proposal.dimensions)


@pytest.mark.parametrize(
    "count,width", [("Veinticinco y dos", "ochenta"), ("Tres", "setenta y cinco y sesenta")]
)
def test_invalid_cardinal_context_does_not_qualify_a_new_furniture_alias(count, width):
    result = RulesEngine().extract(
        ExtractionRequest(
            request_id="context-negative",
            text=f"{count} credencias de {width} centímetros de ancho, cuerpo de melamina.",
            currency_context="BOB",
        )
    )
    assert result.status == "NO_PROPOSAL"
    assert result.item_proposal is None
