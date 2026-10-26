"""Regresiones críticas del motor RULES_ONLY v7; ejemplos sintéticos de diagnóstico."""

import pytest

from homex_nlp.contracts import ExtractionRequest
from homex_nlp.engine import RulesEngine


def extraer(texto: str):
    return RulesEngine().extract(
        ExtractionRequest(request_id="negacion-v7", text=texto, currency_context="BOB")
    )


@pytest.mark.parametrize(
    ("texto", "producto", "cantidad"),
    [
        ("Una mesa, no un escritorio", "mesa", 1),
        ("Una mesa, no, mejor un escritorio", "escritorio", 1),
        ("Mesa no, quiero escritorio", "escritorio", None),
        ("No quiero mesas, quiero un escritorio", "escritorio", 1),
        ("No quiero dos mesas, quiero un escritorio", "escritorio", 1),
        ("No quiero dos mesas, necesito escritorio", "escritorio", None),
        ("Un escritorio, no hay dudas, con cajones", "escritorio", 1),
    ],
)
def test_producto_y_cantidad_con_negaciones_locales(texto, producto, cantidad):
    resultado = extraer(texto)
    assert resultado.status == "REQUIRES_REVIEW"
    assert resultado.item_proposal.name.lower() == producto
    assert resultado.item_proposal.quantity == cantidad
    for candidato in resultado.candidates:
        assert texto[candidato.start : candidato.end] == candidato.text


@pytest.mark.parametrize(
    ("texto", "componentes"),
    [
        ("Un escritorio sin cajones ni puertas", []),
        ("Un escritorio sin cajones y puertas", []),
        ("Un escritorio que no lleva cajones", []),
        ("Un escritorio con dos cajones, sin puertas", ["cajones"]),
        ("Un escritorio con puertas y sin cajones", ["puertas"]),
        ("Una mesa sin cajones, con puertas", ["puertas"]),
    ],
)
def test_piezas_negadas_no_entran_en_configurador(texto, componentes):
    resultado = extraer(texto)
    assert resultado.item_proposal is not None
    assert [p.name.lower() for p in resultado.item_proposal.components] == componentes
    assert any(c.decision == "REJECTED" for c in resultado.candidates)
    assert all(texto[c.start : c.end] == c.text for c in resultado.candidates)


def test_rechaza_dos_productos_verdaderamente_comerciales():
    resultado = extraer("Dos mesas y tres escritorios")
    assert resultado.status == "NO_PROPOSAL"
    assert any(w.code == "MULTIPLE_MAIN_PRODUCTS" for w in resultado.warnings)


def test_reiteracion_del_mismo_producto_en_el_total_no_es_otro_item():
    resultado = extraer(
        "Dos mesas de reunión para diez personas, precio total de las dos mesas 7300 bolivianos"
    )
    assert resultado.status == "REQUIRES_REVIEW"
    assert resultado.item_proposal.quantity == 2
    assert resultado.item_proposal.price.mode == "TOTAL_NEGOCIADO"
    assert resultado.item_proposal.price.line_total == "7300.00"


def test_componente_positivo_con_cantidad_interna_sigue_operativo():
    resultado = extraer("Seis veladores con dos cajones, a 750 bolivianos por unidad")
    assert resultado.item_proposal.quantity == 6
    assert any(
        c.label == "CANTIDAD_INTERNA" and c.normalized_value == 2 for c in resultado.candidates
    )


def test_sin_producto_afirmado_no_inventa_propuesta():
    resultado = extraer("No quiero una mesa ni un escritorio")
    assert resultado.status == "NO_PROPOSAL"
    assert resultado.item_proposal is None
    assert any(c.label == "PRODUCTO" and c.decision == "REJECTED" for c in resultado.candidates)


def test_version_de_reglas_identifica_este_correctivo():
    assert extraer("Un escritorio").engine.rules_version == "prf04-rules-v13"


def test_conjuncion_en_negacion_no_se_interpreta_como_orden_positiva():
    resultado = extraer("No quiero dos mesas y un escritorio")
    assert resultado.status == "NO_PROPOSAL"
    assert resultado.item_proposal is None
