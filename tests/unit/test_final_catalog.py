"""Catalog boundary regressions, exercised through the public extraction API."""

import pytest

from homex_nlp.catalog import CatalogRequest, extract_catalog


def extract(category, text):
    result = extract_catalog(CatalogRequest(category=category, text=text))
    assert all(item.text == text[item.start : item.end] for item in result.evidence)
    return result


@pytest.mark.parametrize(
    ("category", "text", "expected"),
    [
        ("SILLA", "12 sillas ejecutivas con apoyo lumbar", "sillas ejecutivas"),
        ("SILLA", "doce sillas ejecutivas con apoyo lumbar", "sillas ejecutivas"),
        (
            "PISO_FLOTANTE",
            "52 metros cuadrados de piso flotante laminado, espesor 8 mm",
            "piso flotante laminado",
        ),
        (
            "PISO_FLOTANTE",
            "cincuenta y dos metros cuadrados de piso flotante laminado, espesor 8 mm",
            "piso flotante laminado",
        ),
        ("OTRO", "7 zócalos decorativos con acabado resistente", "zócalos decorativos"),
    ],
)
def test_quoted_quantity_is_not_product_identity(category, text, expected):
    result = extract(category, text)
    assert result.fields["nombre"] == expected
    assert not {"cantidad", "stock", "existencias"} & result.fields.keys()


def test_full_punctuated_model_code_or_abstention():
    result = extract("SILLA", "Silla ejecutiva modelo NF Guión 7,782; color negro")
    assert result.fields.get("modelo") in (None, "NF-7782")
    assert any(item.label == "modelo" and "7,782" in item.text for item in result.evidence)


@pytest.mark.parametrize(
    "technical",
    [
        "capacidad de carga de ciento veinte kilogramos",
        "capacidad de carga de 120 kg",
        "reclinación de ciento treinta y cinco grados",
        "reclinación de 135 grados",
        "giro de trescientos sesenta grados",
    ],
)
def test_chair_technical_numbers_preserved(technical):
    result = extract("SILLA", "Silla ejecutiva con " + technical)
    specs = result.fields.get("especificaciones", {})
    assert any(technical in value for value in specs.values())


def test_atypical_explicit_thickness_is_preserved_with_review():
    result = extract("PISO_FLOTANTE", "Piso flotante laminado, espesor 80 mm")
    assert result.fields["espesor_mm"] == "80"
    assert any(
        item.field == "espesor_mm" and item.severity == "REVIEW" for item in result.field_reviews
    )


def test_zocalo_description_is_not_lost_or_entire_transcript():
    technical = "resistente al agua y acabado texturizado"
    result = extract("OTRO", "7 zócalos decorativos con " + technical)
    assert technical in result.fields.get("observaciones", "")
    assert "7 zócalos" not in result.fields["observaciones"]


@pytest.mark.parametrize("raw", ["de ochenta y uno", "ene noventa y uno setenta y cuatro"])
def test_unknown_letters_are_not_reconstructed(raw):
    result = extract("SILLA", "Silla ejecutiva modelo " + raw)
    assert result.fields.get("modelo") not in {"D81A", "NA9174"}
    assert any(item.field == "modelo" for item in result.field_reviews)


def test_category_and_literal_model_remain_unchanged():
    assert extract("SILLA", "Silla ejecutiva modelo B15b").fields["modelo"] == "B15b"
    assert "nombre" not in extract("SILLA", "Piso flotante laminado").fields


@pytest.mark.parametrize(
    "text",
    [
        "quiero registrar doce sillas ejecutivas con apoyo lumbar",
        "nombre: doce sillas ejecutivas, cantidad 12",
    ],
)
def test_counted_introductions_keep_only_name(text):
    assert extract("SILLA", text).fields["nombre"] == "sillas ejecutivas"


def test_model_written_prefix_cannot_hide_numeric_continuation():
    result = extract("SILLA", "Silla ejecutiva modelo NF Guión 7 782")
    assert result.fields.get("modelo") != "NF-7"
    assert any(item.field == "modelo" for item in result.field_reviews)
