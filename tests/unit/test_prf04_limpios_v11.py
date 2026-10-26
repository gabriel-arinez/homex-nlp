"""Regresiones de dictados limpios: referencia sintética de la validación 06.

No contiene grabaciones ni transcripciones privadas del vendedor.
"""

from decimal import Decimal

import pytest

from homex_nlp.contracts import ExtractionRequest
from homex_nlp.engine import RulesEngine

# Dictados predefinidos; expectativas independientes de la salida del NLP.
CASOS = [
    (
        "Un escritorio con dos cajones y tres puertas.",
        "escritorio",
        1,
        [("cajones", 2), ("puertas", 3)],
        {},
        None,
    ),
    (
        "Una credenza con cuatro puertas y dos estantes.",
        "credenza",
        1,
        [("puertas", 4), ("estantes", 2)],
        {},
        None,
    ),
    ("Una cajonera con seis cajones.", "cajonera", 1, [("cajones", 6)], {}, None),
    (
        "Una vitrina con dos puertas y tres cajones.",
        "vitrina",
        1,
        [("puertas", 2), ("cajones", 3)],
        {},
        None,
    ),
    (
        "Un escritorio de 120 centímetros de ancho y 75 centímetros de alto.",
        "escritorio",
        1,
        [],
        {"ancho": "1200", "alto": "750"},
        None,
    ),
    (
        "Un ropero de 2 metros de alto y 90 centímetros de ancho.",
        "ropero",
        1,
        [],
        {"alto": "2000", "ancho": "900"},
        None,
    ),
    (
        "Una mesa de 150 centímetros de largo y 60 centímetros de profundidad.",
        "mesa",
        1,
        [],
        {"largo": "1500", "profundidad": "600"},
        None,
    ),
    (
        "Un librero de 35 centímetros de profundidad y 180 centímetros de alto.",
        "librero",
        1,
        [],
        {"profundidad": "350", "alto": "1800"},
        None,
    ),
    ("Un escritorio de ancho total 180 centímetros.", "escritorio", 1, [], {"ancho": "1800"}, None),
    ("Una mesa con altura total 75 centímetros.", "mesa", 1, [], {"alto": "750"}, None),
    (
        "Una credenza con dos puertas, precio total 3500 bolivianos.",
        "credenza",
        1,
        [("puertas", 2)],
        {},
        ("TOTAL_NEGOCIADO", "3500.00"),
    ),
    (
        "Una mesa de 120 centímetros de largo, precio total 2000 bolivianos.",
        "mesa",
        1,
        [],
        {"largo": "1200"},
        ("TOTAL_NEGOCIADO", "2000.00"),
    ),
    (
        "Un escritorio con tres cajones a 800 bolivianos por unidad.",
        "escritorio",
        1,
        [("cajones", 3)],
        {},
        ("PRECIO_UNITARIO", "800.00"),
    ),
    (
        "Dos escritorios a 1200 bolivianos cada uno.",
        "escritorio",
        2,
        [],
        {},
        ("PRECIO_UNITARIO", "1200.00"),
    ),
    (
        "Un ropero con dos puertas y cuatro cajones, total 3500 bolivianos.",
        "ropero",
        1,
        [("puertas", 2), ("cajones", 4)],
        {},
        ("TOTAL_NEGOCIADO", "3500.00"),
    ),
    (
        "Un librero de 30 centímetros de profundidad y 200 centímetros de alto, "
        "precio total 1500 bolivianos.",
        "librero",
        1,
        [],
        {"profundidad": "300", "alto": "2000"},
        ("TOTAL_NEGOCIADO", "1500.00"),
    ),
]


def extraer(texto):
    return RulesEngine().extract(
        ExtractionRequest(request_id="v11-limpios", text=texto, currency_context="BOB")
    )


def numero(c):
    return c.normalized_value if isinstance(c.normalized_value, int) else None


@pytest.mark.parametrize(
    ("texto", "producto", "cantidad", "componentes", "dimensiones", "precio"),
    CASOS,
)
def test_dieciseis_guiones_comerciales(texto, producto, cantidad, componentes, dimensiones, precio):
    resultado = extraer(texto)
    ficha = resultado.item_proposal
    assert ficha is not None
    assert resultado.engine.rules_version == "prf04-rules-v13"
    assert ficha.name.casefold().rstrip("s") == producto.rstrip("s")
    assert ficha.quantity == cantidad
    cantidades = {}
    for c in resultado.candidates:
        if c.label == "CANTIDAD_INTERNA" and c.decision == "ACCEPTED" and c.component_ref:
            cantidades.setdefault(c.component_ref, []).append(numero(c))
    actual = [
        (c.name.casefold(), cantidades.get(c.component_id, [None])[0]) for c in ficha.components
    ]
    assert actual == componentes
    medidas = {d.axis: d.value_mm for d in ficha.dimensions if d.component_ref is None}
    assert medidas == dimensiones
    actual_precio = (
        None
        if ficha.price is None
        else (ficha.price.mode, f"{Decimal(ficha.price.stated_amount):.2f}")
    )
    assert actual_precio == precio
    assert all(texto[c.start : c.end] == c.text for c in resultado.candidates)


@pytest.mark.parametrize(
    "texto",
    [
        "Dos mesas y tres estantes",
        "Una credenza con dos estantes y otro escritorio",
        "Una credenza con dos estantes y tres mesas",
    ],
)
def test_pedidos_distintos_no_se_fusionan(texto):
    r = extraer(texto)
    assert r.status == "NO_PROPOSAL"
    assert r.item_proposal is None
    assert any(w.code == "MULTIPLE_MAIN_PRODUCTS" for w in r.warnings)


@pytest.mark.parametrize(
    "texto,producto",
    [
        ("Dos estantes con tres cajones", "estantes"),
        ("Una credenza con cajonera", "credenza"),
        ("Una cajonera sin cajones", "cajonera"),
    ],
)
def test_conserva_producto_legitimo_y_subcomponentes(texto, producto):
    r = extraer(texto)
    assert r.item_proposal is not None
    assert r.item_proposal.name.casefold() == producto
    assert all(texto[c.start : c.end] == c.text for c in r.candidates)


@pytest.mark.parametrize(
    "texto,precio",
    [
        ("Un escritorio ancho total 180 centímetros", None),
        ("Un escritorio con altura total 75 cm y precio total 2000 bolivianos", "2000.00"),
        ("Una mesa ancho total 180 cm, total 7000 bolivianos", "7000.00"),
    ],
)
def test_medida_total_no_inventa_precio(texto, precio):
    r = extraer(texto)
    actual = r.item_proposal.price
    assert (None if actual is None else f"{Decimal(actual.stated_amount):.2f}") == precio
    assert all(texto[c.start : c.end] == c.text for c in r.candidates)
