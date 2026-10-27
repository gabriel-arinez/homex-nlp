"""Regresiones sintéticas del ASR: puntuación omitida, negación y evidencia."""

import pytest

from homex_nlp.contracts import ExtractionRequest
from homex_nlp.engine import RulesEngine


def extraer(texto):
    return RulesEngine().extract(
        ExtractionRequest(request_id="nlp-v9-puntuacion", text=texto, currency_context="BOB")
    )


def internas(resultado, decision):
    return [
        (c.text.casefold(), c.normalized_value)
        for c in resultado.candidates
        if c.label == "CANTIDAD_INTERNA" and c.decision == decision
    ]


@pytest.mark.parametrize(
    "texto",
    [
        "Un escritorio con tres cajones, no, mejor dos cajones",
        "Un escritorio con tres cajones no mejor dos cajones",
        "Un escritorio con tres cajones no, mejor dos cajones",
        "Un escritorio con tres cajones. No, mejor dos cajones",
        "Un escritorio con tres cajones; no, mejor dos cajones",
    ],
)
def test_rectificacion_de_pieza_sin_signos_obligatorios(texto):
    r = extraer(texto)
    assert [c.name.casefold() for c in r.item_proposal.components] == ["cajones"]
    assert internas(r, "ACCEPTED") == [("dos", 2)]
    assert internas(r, "REJECTED") == [("tres", 3)]
    assert r.status == "REQUIRES_REVIEW"
    assert all(texto[c.start : c.end] == c.text for c in r.candidates)


@pytest.mark.parametrize(
    "texto",
    [
        "Un escritorio con tres cajones, no, mejor dos",
        "Un escritorio con tres cajones no mejor dos",
        "Un escritorio con tres cajones no, mejor dos",
        "Un escritorio con tres cajones. No mejor dos",
    ],
)
def test_rectificacion_de_cantidad_sin_signos_obligatorios(texto):
    r = extraer(texto)
    assert [c.name.casefold() for c in r.item_proposal.components] == ["cajones"]
    assert internas(r, "ACCEPTED") == [("dos", 2)]
    assert internas(r, "REJECTED") == [("tres", 3)]
    assert all(texto[c.start : c.end] == c.text for c in r.candidates)


def test_no_inventa_correccion_desde_no_incompleto():
    r = extraer("Un escritorio con tres cajones no, dos")
    assert internas(r, "ACCEPTED") == []
    assert internas(r, "UNRESOLVED") == [("tres", 3), ("dos", 2)]
    assert r.item_proposal.unresolved


@pytest.mark.parametrize(
    "texto",
    [
        "Un escritorio con tres cajones, no, mejor dos, no, mejor cuatro",
        "Un escritorio con tres cajones no mejor dos no mejor cuatro",
    ],
)
def test_rectificaciones_sucesivas_no_se_confirman_silenciosamente(texto):
    r = extraer(texto)
    assert internas(r, "ACCEPTED") == []
    assert internas(r, "UNRESOLVED") == [("tres", 3), ("dos", 2), ("cuatro", 4)]
    assert r.item_proposal.unresolved


def test_dos_componentes_validos_no_se_fusionan():
    r = extraer("Un escritorio con tres cajones y dos puertas")
    assert [c.name.casefold() for c in r.item_proposal.components] == ["cajones", "puertas"]
    assert internas(r, "ACCEPTED") == [("tres", 3), ("dos", 2)]


def test_negaciones_sin_correccion_siguen_excluyendo():
    r = extraer("Un escritorio con dos cajones sin puertas")
    assert [c.name.casefold() for c in r.item_proposal.components] == ["cajones"]


def test_no_cambia_precio_total():
    r = extraer("Un escritorio con tres cajones no mejor dos, total 7300 bolivianos")
    assert r.item_proposal.price.mode == "TOTAL_NEGOCIADO"
    assert r.item_proposal.price.line_total == "7300.00"
    assert internas(r, "ACCEPTED") == [("dos", 2)]


def test_version_identifica_nueva_regla():
    assert extraer("Un escritorio").engine.rules_version == "prf04-rules-v15"
