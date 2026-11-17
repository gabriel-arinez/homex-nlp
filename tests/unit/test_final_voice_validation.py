"""Commercial evidence, not forbidden words or voice length, controls catalog output."""

import pytest
from pydantic import ValidationError

from homex_nlp.catalog import CatalogRequest, extract_catalog


def extract(text, category="OTRO"):
    result = extract_catalog(CatalogRequest(category=category, text=text))
    assert all(
        candidate.text == text[candidate.start : candidate.end] for candidate in result.evidence
    )
    return result


@pytest.mark.parametrize(
    "name",
    [
        "Silla Hola",
        "Silla Buenas",
        "Silla Buenos",
        "Silla Probando",
        "Silla Micrófono",
        "prueba",
        "prueba de audio",
        "uno dos tres",
        "Mueble",
    ],
)
def test_explicit_names_use_open_vocabulary(name):
    result = extract(f"nombre comercial: {name}")
    assert result.fields == {"nombre": name}


@pytest.mark.parametrize(
    "name", ["Silla Hola", "Silla Buenas", "Silla Probando", "Silla Micrófono"]
)
def test_implicit_product_names_are_not_filtered_by_unrelated_words(name):
    assert extract(name).fields == {"nombre": name}


@pytest.mark.parametrize("words", [30, 50])
def test_long_noncommercial_text_abstains_without_invented_attributes(words):
    result = extract(" ".join(["nubarrones"] * words))
    assert not result.fields
    assert result.unrecognized


def test_partial_commercial_evidence_survives_without_identity():
    result = extract("nubarrones " * 30 + "precio unitario 350 bolivianos")
    assert result.fields == {"precio_lista": "350.00"}
    assert any(c.label == "precio_lista" and c.decision == "ACCEPTED" for c in result.evidence)


@pytest.mark.parametrize(
    "category,text", [("SILLA", "Silla plegable"), ("PISO_FLOTANTE", "espesor 8 mm")]
)
def test_general_nlp_preserves_short_valid_descriptions(category, text):
    assert extract(text, category).fields


@pytest.mark.parametrize("category", ["SILLA", "PISO_FLOTANTE", "OTRO"])
def test_catalog_never_uses_transcript_as_observations(category):
    result = extract(
        "Silla plegable con asiento de espuma. Precio unitario 350 bolivianos.", category
    )
    assert "observaciones" not in result.fields
    assert not [c for c in result.evidence if c.label == "observaciones"]


def test_explicit_complementary_observations_preserve_source_evidence():
    text = (
        "Piso flotante de HDF, espesor 8 mm, largo 120 cm, ancho 20 cm. "
        "Precio unitario 350 bolivianos. Observaciones: entregar con embalaje reforzado"
    )
    result = extract(text, "PISO_FLOTANTE")
    assert result.fields["nombre"] == "Piso flotante"
    assert result.fields["espesor_mm"] == "8"
    assert result.fields["largo_mm"] == "1200"
    assert result.fields["ancho_mm"] == "200"
    assert result.fields["precio_lista"] == "350.00"
    assert result.fields["observaciones"] == "entregar con embalaje reforzado"
    observation = next(c for c in result.evidence if c.label == "observaciones")
    assert observation.decision == "ACCEPTED"
    assert observation.text == "entregar con embalaje reforzado"


def test_description_is_not_an_observation_storage_fallback():
    result = extract("Producto: Panel Aurora. Descripción: panel de madera con soporte")
    assert result.fields == {"nombre": "Panel Aurora"}


def test_general_catalog_length_contract_is_unchanged():
    CatalogRequest(category="OTRO", text="x" * 20000)
    with pytest.raises(ValidationError):
        CatalogRequest(category="OTRO", text="x" * 20001)
