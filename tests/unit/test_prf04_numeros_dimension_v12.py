"""Regresiones de número en palabras tras ASR; escenarios sintéticos, no voz privada."""

from decimal import Decimal

import pytest

from homex_nlp.contracts import ExtractionRequest
from homex_nlp.engine import RulesEngine
from homex_nlp.rules import _dimension_numero_palabras, find_measurements


@pytest.mark.parametrize(
    ("texto", "eje", "valor_mm"),
    [
        ("Un ropero de dos metros de alto", "alto", "2000"),
        ("Un ropero de noventa centímetros de ancho", "ancho", "900"),
        ("Una mesa de setenta y cinco centímetros de altura", "alto", "750"),
        ("Un escritorio con alto de dos metros", "alto", "2000"),
        ("Un escritorio con alto total dos metros", "alto", "2000"),
        ("Un escritorio con altura total noventa centímetros", "alto", "900"),
        ("Un escritorio con ancho ciento ochenta centímetros", "ancho", "1800"),
        ("Una mesa de ciento veinte centímetros de largo", "largo", "1200"),
        ("Una mesa de treinta y cinco centímetros de profundidad", "profundidad", "350"),
        ("Una mesa de veintidós centímetros de fondo", "profundidad", "220"),
        ("Un escritorio de veintitrés centímetros de ancho", "ancho", "230"),
        ("Un escritorio de dieciséis centímetros de alto", "alto", "160"),
        ("Un mueble con ancho mil doscientos milímetros", "ancho", "1200"),
        ("Un ropero de dos mil milímetros de alto", "alto", "2000"),
        ("Un ropero de mil ochocientos milímetros de alto", "alto", "1800"),
        ("Un ropero de cien centímetros de ancho", "ancho", "1000"),
        ("Un ropero de trescientos centímetros de largo", "largo", "3000"),
        ("Un ropero de treinta y uno centímetros de ancho", "ancho", "310"),
        ("Un ropero con diámetro cuarenta centímetros", "diametro", "400"),
    ],
)
def test_dimension_escrita_en_palabras(texto, eje, valor_mm):
    res = RulesEngine().extract(
        ExtractionRequest(request_id="v12-positivo", text=texto, currency_context="BOB")
    )
    assert res.item_proposal is not None
    medidas = [d for d in res.item_proposal.dimensions if d.axis == eje]
    assert len(medidas) == 1
    assert medidas[0].value_mm == valor_mm
    assert res.item_proposal.price is None
    assert res.engine.rules_version == "prf04-rules-v13"
    for c in res.candidates:
        assert texto[c.start : c.end] == c.text


def test_l06_variantes_equivalentes_y_orden_de_ejes():
    casos = (
        "Un ropero de 2 metros de alto y 90 centímetros de ancho",
        "Un ropero de dos metros de alto y 90 centímetros de ancho",
        "Un ropero de 2 metros de alto y noventa centímetros de ancho",
        "Un ropero de dos metros de alto y noventa centímetros de ancho",
        "Un ropero de alto dos metros y ancho noventa centímetros",
    )
    for texto in casos:
        r = RulesEngine().extract(
            ExtractionRequest(request_id="l06-sintetico", text=texto, currency_context="BOB")
        )
        assert r.item_proposal is not None
        assert {d.axis: d.value_mm for d in r.item_proposal.dimensions} == {
            "alto": "2000",
            "ancho": "900",
        }
        assert r.item_proposal.price is None


@pytest.mark.parametrize(
    "texto",
    [
        "Una mesa de dos puertas",  # no es una dimensión
        "Un ropero de alto dos",  # sin unidad: abstenerse
        "Un ropero de alto veinti centímetros",  # token desconocido
        "Un ropero de alto ciento y veinte centímetros",  # gramática inválida
        "Un ropero de dos y tres metros de alto",  # valores contradictorios
        "Un ropero de ciento cinco y dos metros de alto",  # secuencia inválida
        "Un ropero de dos coma cinco metros de alto",  # decimal oral no soportado
        "Un ropero de dos punto cinco metros de alto",  # decimal oral no soportado
        "Un ropero de un metro y veinte centímetros de alto",  # medida oral compuesta no soportada
        "Un ropero de dos centímetros y veinte milímetros de alto",  # múltiples unidades
        "Un ropero de alto diez mil metros",  # fuera de rango
        "Un ropero de cero metros de alto",  # cero inválido
        "Una mesa de dos metros",  # sin eje explícito
    ],
)
def test_abstencion_para_expresiones_incompletas_o_ambiguas(texto):
    r = RulesEngine().extract(
        ExtractionRequest(request_id="v12-negativo", text=texto, currency_context="BOB")
    )
    assert r.item_proposal is not None
    assert r.item_proposal.dimensions == []
    assert r.item_proposal.price is None


@pytest.mark.parametrize(
    ("texto", "precio", "mm"),
    [
        ("Un escritorio de dos metros de alto, precio total 3500 bolivianos", "3500.00", "2000"),
        ("Una mesa con ancho ciento ochenta centímetros, total 7600 bolivianos", "7600.00", "1800"),
        ("Una mesa con altura noventa centímetros, sin precio indicado", None, "900"),
    ],
)
def test_medida_no_se_confunde_con_precio(texto, precio, mm):
    r = RulesEngine().extract(
        ExtractionRequest(request_id="v12-precios", text=texto, currency_context="BOB")
    )
    assert r.item_proposal is not None
    assert (r.item_proposal.price.stated_amount if r.item_proposal.price else None) == precio
    assert [d.value_mm for d in r.item_proposal.dimensions] == [mm]


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("NOVENTA", 90),
        ("setenta y cinco", 75),
        ("ciento ochenta", 180),
        ("veintidós", 22),
        ("doscientos cincuenta", 250),
        ("mil doscientos", 1200),
        ("dos mil novecientos", 2900),
        ("mil novecientos ochenta y cinco", 1985),
        ("ciento y veinte", None),
        ("diez mil", None),
        ("veinte y treinta", None),
        ("un mil", 1000),
    ],
)
def test_parser_completo_o_abstencion(raw, expected):
    result = _dimension_numero_palabras(raw)
    assert result == (None if expected is None else Decimal(expected))


def test_evidencia_offsets_y_tipos_de_todas_las_medidas():
    texto = "Un escritorio de ancho ciento ochenta centímetros y alto setenta y cinco centímetros"
    ancho = find_measurements(texto, "ancho")
    alto = find_measurements(texto, "alto")
    for m in ancho + alto:
        assert texto[m.start : m.end] == m.text
        assert isinstance(m.value[0], Decimal)
        assert m.value[1] == "cm"
    assert [a.value[0] for a in ancho] == [Decimal(180)]
    assert [a.value[0] for a in alto] == [Decimal(75)]


def test_milimetros_con_tilde_en_numero_escrito_en_digitos():
    texto = "Un ropero de 1800 milímetros de alto"
    resultado = RulesEngine().extract(
        ExtractionRequest(request_id="v12-mm", text=texto, currency_context="BOB")
    )
    assert resultado.item_proposal is not None
    assert len(resultado.item_proposal.dimensions) == 1
    d = resultado.item_proposal.dimensions[0]
    assert d.unit == "mm"
    assert d.value_mm == "1800"
    assert (
        texto[resultado.candidates[0].start : resultado.candidates[0].end]
        == resultado.candidates[0].text
    )
