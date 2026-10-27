"""Rectificaciones internas: nunca proyectar la cantidad/pieza sustituida."""

import pytest

from homex_nlp.contracts import ExtractionRequest
from homex_nlp.engine import RulesEngine


def extraer(texto):
    return RulesEngine().extract(
        ExtractionRequest(request_id="componentes-v8", text=texto, currency_context="BOB")
    )


def cantidades(resultado, decision):
    return [
        (c.text.casefold(), c.normalized_value)
        for c in resultado.candidates
        if c.label == "CANTIDAD_INTERNA" and c.decision == decision
    ]


@pytest.mark.parametrize(
    ("texto", "nombres", "afirmadas", "descartadas"),
    [
        (
            "Un escritorio con tres cajones, no, mejor dos cajones",
            ["cajones"],
            [("dos", 2)],
            [("tres", 3)],
        ),
        (
            "Un escritorio con tres cajones, no, mejor dos",
            ["cajones"],
            [("dos", 2)],
            [("tres", 3)],
        ),
        (
            "Un escritorio con tres cajones, no, mejor dos puertas",
            ["puertas"],
            [("dos", 2)],
            [("tres", 3)],
        ),
        (
            "Un escritorio con tres cajones, no, mejor dos cajones y una puerta",
            ["cajones", "puerta"],
            [("dos", 2), ("una", 1)],
            [("tres", 3)],
        ),
        (
            "Una mesa con tres cajones, mejor dos cajones, total 7300 bolivianos",
            ["cajones"],
            [("dos", 2)],
            [("tres", 3)],
        ),
    ],
)
def test_rectificacion_no_deja_cantidad_ni_componente_antiguos(
    texto, nombres, afirmadas, descartadas
):
    r = extraer(texto)
    assert r.status == "REQUIRES_REVIEW"
    assert [c.name.lower() for c in r.item_proposal.components] == nombres
    assert cantidades(r, "ACCEPTED") == afirmadas
    assert cantidades(r, "REJECTED") == descartadas
    assert any(w.code == "CONFLICTING_VALUES" for w in r.warnings)
    for c in r.candidates:
        assert texto[c.start : c.end] == c.text


def test_sin_rectificacion_conserva_componentes_comerciales():
    r = extraer("Un escritorio con tres cajones y dos puertas")
    assert [c.name for c in r.item_proposal.components] == ["cajones", "puertas"]
    assert cantidades(r, "ACCEPTED") == [("tres", 3), ("dos", 2)]
    assert cantidades(r, "REJECTED") == []


def test_no_dos_cajones_no_se_convierte_en_orden_positiva():
    r = extraer("Un escritorio con tres cajones, no dos cajones")
    assert [c.name for c in r.item_proposal.components] == ["cajones"]
    assert cantidades(r, "ACCEPTED") == [("tres", 3)]
    assert not [
        c
        for c in r.candidates
        if c.label == "CANTIDAD_INTERNA" and c.normalized_value == 2 and c.decision == "ACCEPTED"
    ]


def test_negaciones_continuan_excluyendo_piezas():
    r = extraer("Un escritorio con dos cajones sin puertas")
    assert [c.name for c in r.item_proposal.components] == ["cajones"]
    assert cantidades(r, "ACCEPTED") == [("dos", 2)]
    assert any(
        c.label == "COMPONENTE" and c.text == "puertas" and c.decision == "REJECTED"
        for c in r.candidates
    )


def test_precios_negociados_no_se_transforman_en_unitarios():
    r = extraer("Una mesa con tres cajones, no, mejor dos, total 7300 bolivianos")
    assert r.item_proposal.price.mode == "TOTAL_NEGOCIADO"
    assert r.item_proposal.price.line_total == "7300.00"
    assert r.item_proposal.price.unit_price_reference == "7300"
    assert cantidades(r, "ACCEPTED") == [("dos", 2)]


def test_no_inventa_cantidad_comercial_a_partir_de_cajones():
    r = extraer("Escritorio con tres cajones, no, mejor dos")
    assert r.item_proposal.quantity is None
    assert cantidades(r, "ACCEPTED") == [("dos", 2)]


@pytest.mark.parametrize(
    "texto",
    [
        "Un escritorio con tres cajones, no, dos cajones",
        "Un escritorio con tres cajones, no, dos",
        "Un escritorio con tres cajones, no, mejor dos, no, mejor cuatro",
    ],
)
def test_ambiguedad_no_afirma_cantidades_internas(texto):
    resultado = extraer(texto)
    assert resultado.item_proposal is not None
    assert cantidades(resultado, "ACCEPTED") == []
    assert any(w.code == "CONFLICTING_VALUES" for w in resultado.warnings)
    assert resultado.item_proposal.unresolved
    assert all(texto[c.start : c.end] == c.text for c in resultado.candidates)


def test_rectificacion_encadenada_conserva_todos_los_numeros_no_resueltos():
    r = extraer("Un escritorio con tres cajones, no, mejor dos, no, mejor cuatro")
    assert cantidades(r, "UNRESOLVED") == [("tres", 3), ("dos", 2), ("cuatro", 4)]


def test_motor_sigue_sin_ner_y_exige_revision_humana():
    r = extraer("Un escritorio con tres cajones, no, mejor dos")
    assert r.engine.mode == "RULES_ONLY"
    assert r.status == "REQUIRES_REVIEW"
    assert r.proposed_item_count == 1
