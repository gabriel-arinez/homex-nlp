"""Pruebas sintéticas: medidas no monetarias, precios y componentes limpios."""

import pytest

from homex_nlp.contracts import ExtractionRequest
from homex_nlp.engine import RulesEngine
from homex_nlp.rules import find_price


def extraer(texto):
    return RulesEngine().extract(
        ExtractionRequest(request_id="precio-v10", text=texto, currency_context="BOB")
    )


@pytest.mark.parametrize(
    "texto",
    [
        "Un escritorio de ancho total 180 centímetros",
        "Un escritorio de altura total 180 centímetros",
        "Un escritorio de longitud total 180 centímetros",
        "Un escritorio de ancho total 180",
        "Un escritorio con ancho total 180 cm y alto 75 cm",
        "Escritorio precio total 180 centímetros",
        "Escritorio monto total de 200 mm",
    ],
)
def test_medida_no_es_precio(texto):
    assert find_price(texto) == (None, None)
    resultado = extraer(texto)
    assert resultado.item_proposal is not None
    assert resultado.item_proposal.price is None
    assert all(texto[c.start : c.end] == c.text for c in resultado.candidates)


@pytest.mark.parametrize(
    ("texto", "importe", "modo"),
    [
        (
            "Escritorio con ancho total 180 centímetros, total 7600 bolivianos",
            "7600.00",
            "TOTAL_NEGOCIADO",
        ),
        (
            "Escritorio con ancho total 180 centímetros, precio total 7600",
            "7600.00",
            "TOTAL_NEGOCIADO",
        ),
        (
            "Escritorio con alto total 75 cm. Precio total de 2000 Bs",
            "2000.00",
            "TOTAL_NEGOCIADO",
        ),
        ("Escritorio total 7300 bolivianos", "7300.00", "TOTAL_NEGOCIADO"),
        ("Escritorio total 7300", "7300.00", "TOTAL_NEGOCIADO"),
        ("Escritorio a 500 Bs por unidad", "500.00", "PRECIO_UNITARIO"),
        ("Escritorio precio unitario 550", "550.00", "PRECIO_UNITARIO"),
        ("Dos escritorios total 1000 bolivianos", "1000.00", "TOTAL_NEGOCIADO"),
    ],
)
def test_precios_comerciales_siguieron_funcionando(texto, importe, modo):
    resultado = extraer(texto)
    assert resultado.item_proposal is not None
    assert resultado.item_proposal.price is not None
    assert resultado.item_proposal.price.mode == modo
    assert resultado.item_proposal.price.stated_amount == importe
    assert all(texto[c.start : c.end] == c.text for c in resultado.candidates)


@pytest.mark.parametrize(
    "texto",
    [
        "Un escritorio con dos cajones y tres puertas",
        "Un escritorio con dos cajones, y tres puertas",
        "Un escritorio con dos cajones. Y tres puertas",
    ],
)
def test_componentes_limpios_invariantes(texto):
    resultado = extraer(texto)
    assert resultado.item_proposal is not None
    assert [c.name.lower() for c in resultado.item_proposal.components] == ["cajones", "puertas"]
    assert resultado.item_proposal.price is None
    assert all(texto[c.start : c.end] == c.text for c in resultado.candidates)
