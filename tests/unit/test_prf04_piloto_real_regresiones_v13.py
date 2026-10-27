"""Regresiones focalizadas del piloto v13. Frases de prueba; no son GOLD ni WER."""

import pytest

from homex_nlp.contracts import ExtractionRequest
from homex_nlp.engine import RulesEngine


def extraer(texto):
    return RulesEngine().extract(
        ExtractionRequest(request_id="piloto-v13-replay", text=texto, currency_context="BOB")
    )


@pytest.mark.parametrize(
    ("texto", "producto", "cantidad", "importe"),
    [
        (
            "Solicito tres gabeteros móviles de 0.49 metros de ancho, presionitario, 1.150 bolivianos",
            "gabeteros",
            3,
            "1150.00",
        ),
        (
            "Solicito tres gaveteros móviles de 0.49 metros de ancho, precio unitario 1150 bolivianos",
            "gaveteros",
            3,
            "1150.00",
        ),
        (
            "Necesito un escritor ejecutivo, una unidad de 1.70 metros de ancho, precio unitario, 4.850 bolivianos",
            "escritor ejecutivo",
            1,
            "4850.00",
        ),
        (
            "Necesito un atril, una unidad de 0.48 metros de ancho, presunitario 920 bolivianos",
            "atril",
            1,
            "920.00",
        ),
    ],
)
def test_productos_asr_acotados(texto, producto, cantidad, importe):
    r = extraer(texto)
    assert r.status == "REQUIRES_REVIEW"
    assert r.item_proposal is not None
    assert producto in r.item_proposal.name.casefold()
    assert r.item_proposal.quantity == cantidad
    assert r.item_proposal.price.mode == "PRECIO_UNITARIO"
    assert r.item_proposal.price.stated_amount == importe
    assert all(texto[c.start : c.end] == c.text for c in r.candidates)


def test_escritorio_en_l_y_cajonera_integrada_son_una_linea():
    texto = (
        "Solicito dos escritorios en L con cajonería rodante integrada, "
        "cada escritorio tiene dos lados de 1.40 metros, "
        "cajonera con 3 cajones y precio unitario 4.150 bolivianos"
    )
    r = extraer(texto)
    assert r.item_proposal is not None
    assert r.item_proposal.quantity == 2
    assert not any(w.code == "MULTIPLE_MAIN_PRODUCTS" for w in r.warnings)


def test_mesa_reunion_una_sola_unidad_al_final():
    texto = (
        "Mesa de reunión para 12 personas, de 3 metros de largo, "
        "presionitario 8.50 bolivianos, se cotiza una sola mesa"
    )
    r = extraer(texto)
    assert r.item_proposal is not None
    assert r.item_proposal.quantity == 1
    assert not any(w.code == "MULTIPLE_MAIN_PRODUCTS" for w in r.warnings)
    # Nunca convertir 8.50 en 8050 a partir de la intención supuesta.
    assert r.item_proposal.price is None
    assert any(w.code == "INVALID_PRICE" for w in r.warnings)

    asr = extraer(texto.replace("se cotiza", "secotiza"))
    assert asr.item_proposal is not None
    assert asr.item_proposal.quantity == 1


def test_cantidad_contradictoria_no_se_silencia():
    r = extraer("Dos mesas de reunión, se cotiza una sola mesa")
    assert r.item_proposal is None
    assert any(w.code == "MULTIPLE_MAIN_PRODUCTS" for w in r.warnings)


@pytest.mark.parametrize(
    "texto",
    [
        "Un escritor de novelas que habla de una ciudad",
        "Se necesitan un escritorio y una mesa",
        "Cotiza mesa y cajonera independientes",
        "Dos escritorios y una cajonera adicional",
    ],
)
def test_sin_inferencias_inseguras(texto):
    r = extraer(texto)
    if "escritor de novelas" in texto:
        assert r.item_proposal is None
    else:
        assert r.item_proposal is None
        assert any(w.code == "MULTIPLE_MAIN_PRODUCTS" for w in r.warnings)


@pytest.mark.parametrize(
    ("texto", "mode", "amount"),
    [
        ("Un escritorio, precio total negociado, 5.400 bolivianos", "TOTAL_NEGOCIADO", "5400.00"),
        ("Una credenza, precio total negociado 5400 bolivianos", "TOTAL_NEGOCIADO", "5400.00"),
        ("Un escritorio, el precio unitario es de 2.450 bolivianos", "PRECIO_UNITARIO", "2450.00"),
        ("Una mesa, prese unitario 7.280 bolivianos", "PRECIO_UNITARIO", "7280.00"),
    ],
)
def test_precios_comerciales_con_separadores(texto, mode, amount):
    r = extraer(texto)
    assert r.item_proposal is not None
    assert r.item_proposal.price is not None
    assert r.item_proposal.price.mode == mode
    assert r.item_proposal.price.stated_amount == amount


def test_la_medida_nunca_se_reutiliza_como_importe():
    r = extraer("Un escritorio de ancho total 180 centímetros, precio unitario 1850 bolivianos")
    assert r.item_proposal.price.stated_amount == "1850.00"
