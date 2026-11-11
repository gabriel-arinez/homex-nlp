"""Public-interface regressions derived from linguistic rules, not product IDs."""

import pytest

from homex_nlp.catalog import CatalogRequest, extract_catalog
from homex_nlp.contracts import ExtractionRequest
from homex_nlp.engine import RulesEngine


def catalog(category, text):
    result = extract_catalog(CatalogRequest(category=category, text=text))
    for candidate in result.evidence:
        assert candidate.text == text[candidate.start : candidate.end]
    return result


@pytest.mark.parametrize("unit", ["juego", "pieza", "barra", "metro cuadrado"])
def test_explicit_commercial_unit_price_is_not_lost(unit):
    text = f"Producto: Revestimiento; precio por {unit} de doscientos treinta bolivianos."
    result = catalog("OTRO", text)
    assert result.fields["precio_lista"] == "230.00"
    assert "stock" not in result.fields
    assert "cantidad" not in result.fields


def test_existing_unit_price_and_negotiated_total_keep_their_meaning():
    result = catalog("OTRO", "precio unitario 250 bolivianos, cantidad 3, total 750 bolivianos")
    assert result.fields["precio_lista"] == "250.00"
    result = RulesEngine().extract(
        ExtractionRequest(
            request_id="previous-behavior",
            text="Dos mesas. Precio unitario 250 bolivianos.",
            currency_context="BOB",
        )
    )
    assert result.item_proposal.price.stated_amount == "250.00"
    assert result.item_proposal.price.mode == "PRECIO_UNITARIO"


@pytest.mark.parametrize(
    "amount,expected", [("ocho", "8"), ("treinta y dos", "32"), ("8,5", "8.5")]
)
def test_conjunction_before_measurement_does_not_become_part_of_number(amount, expected):
    result = catalog(
        "PISO_FLOTANTE", f"Piso laminado de aglomerado y {amount} milímetros de espesor."
    )
    assert result.fields["espesor_mm"] == expected


def test_existing_prefixed_measure_and_alternative_are_preserved():
    assert catalog("PISO_FLOTANTE", "espesor de ocho milímetros").fields["espesor_mm"] == "8"
    assert "espesor_mm" not in catalog("PISO_FLOTANTE", "espesor de ocho o diez milímetros").fields


def test_explicit_backrest_is_not_assigned_to_preceding_seat():
    result = catalog("SILLA", "Silla con asiento de espuma inyectada y respaldo de malla.")
    assert result.fields["especificaciones"]["material_respaldo"] == "respaldo de malla"
    assert result.fields["especificaciones"]["asiento"] == "espuma inyectada"


def test_seat_mesh_and_negated_backrest_do_not_invent_backrest_material():
    result = catalog("SILLA", "Silla con asiento de malla, sin respaldo de malla.")
    assert "material_respaldo" not in result.fields.get("especificaciones", {})


@pytest.mark.parametrize(
    "product", ["armario", "armarios", "clóset", "clósets", "casillero", "casilleros"]
)
def test_storage_furniture_nouns_retain_quantity_and_source_evidence(product):
    text = f"Dos {product} de melamina. Precio unitario de tres mil bolivianos."
    result = RulesEngine().extract(
        ExtractionRequest(request_id="storage", text=text, currency_context="BOB")
    )
    assert result.item_proposal is not None
    assert result.item_proposal.name == product
    assert result.item_proposal.quantity == 2
    assert result.item_proposal.price.stated_amount == "3000.00"
    for candidate in result.candidates:
        assert candidate.text == text[candidate.start : candidate.end]


@pytest.mark.parametrize("phrase", ["HDF de doce milímetros", "HDF de 9,5 mm"])
def test_explicit_hdf_board_thickness_without_repeated_label(phrase):
    expected = "12" if "doce" in phrase else "9.5"
    assert (
        catalog("PISO_FLOTANTE", f"Piso de aglomerado {phrase}.").fields["espesor_mm"] == expected
    )


def test_labeled_length_and_invalid_hdf_amount_do_not_become_thickness():
    for text in [
        "HDF de doce milímetros de ancho",
        "HDF de ocho o doce milímetros",
        "sin HDF de doce milímetros",
    ]:
        assert "espesor_mm" not in catalog("PISO_FLOTANTE", text).fields


def test_storage_product_negation_and_multiple_products_keep_abstention():
    for text in ["No quiero dos armarios.", "Dos armarios y una mesa."]:
        result = RulesEngine().extract(
            ExtractionRequest(request_id="abstain", text=text, currency_context="BOB")
        )
        assert result.item_proposal is None


@pytest.mark.parametrize("category", ["OTRO", "SILLA", "PISO_FLOTANTE"])
def test_numeric_count_prefix_keeps_literal_name_and_description(category):
    text = "3 paneles modulares con soporte. Precio unitario de setecientos bolivianos."
    result = catalog(category, text)
    assert result.fields["nombre"] == "3 paneles modulares"
    assert result.fields["observaciones"] == text
    assert result.fields["precio_lista"] == "700.00"
    assert "cantidad" not in result.fields
    assert "stock" not in result.fields


@pytest.mark.parametrize(
    "text",
    [
        "8 milímetros de espesor",
        "5500 bolivianos",
        "2 sin respaldo",
        "2 modelos",
        "0 paneles",
        "2,5 metros",
    ],
)
def test_numeric_fragments_do_not_invent_catalog_names(text):
    result = catalog("OTRO", text)
    assert "nombre" not in result.fields
    assert "observaciones" not in result.fields
