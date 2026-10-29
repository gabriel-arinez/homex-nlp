"""Regresiones focalizadas v13; casos sintéticos, no transcripciones privadas."""

import pytest

from homex_nlp import __version__
from homex_nlp.contracts import ExtractionRequest
from homex_nlp.engine import RulesEngine
from homex_nlp.rules import find_accessories


def extraer(texto):
    return RulesEngine().extract(
        ExtractionRequest(request_id="prf04-v13-cantidad-acc", text=texto, currency_context="BOB")
    )


@pytest.mark.parametrize(
    ("texto", "cantidad", "fragmento"),
    [
        ("Mesa de reunión para 10 personas, una pieza tamaño 2.4 metros de largo", 1, "una"),
        ("Escritorio, dos piezas. Material melamina de 18 milímetros", 2, "dos"),
        ("Ropero 3 unidades, alto 2 metros", 3, "3"),
        ("Vitrina una pieza precio unitario 750", 1, "una"),
        ("Mesa, dos pzas., color a elección", 2, "dos"),
        ("Un escritorio", 1, "Un"),
        ("Dos escritorios para oficina", 2, "Dos"),
        ("Escritorio, cantidad comercial: tres piezas", 3, "tres"),
        ("Se cotizan dos piezas de escritorio", 2, "dos"),
    ],
)
def test_cantidad_comercial_segura_y_offset(texto, cantidad, fragmento):
    resultado = extraer(texto)
    assert resultado.status == "REQUIRES_REVIEW"
    assert resultado.engine.mode == "RULES_ONLY"
    assert resultado.engine.rules_version == "prf04-rules-final"
    assert resultado.item_proposal.quantity == cantidad
    spans = [c for c in resultado.candidates if c.label == "CANTIDAD" and c.decision == "ACCEPTED"]
    assert len(spans) == 1
    assert spans[0].text.casefold() == fragmento.casefold()
    assert texto[spans[0].start : spans[0].end] == spans[0].text


@pytest.mark.parametrize(
    "texto",
    [
        "Mesa para 10 personas, color gris",
        "Mesa de reunión para 10 personas",
        "Mesa, dos puertas y tres cajones",
        "Mesa, una pieza de vidrio en la parte superior",
        "Mesa dos piezas de madera",
        "Mesa, dos piezas para fabricar un tablero",
        "Mesa, dos piezas, no mejor tres piezas",
        "Mesa sin una pieza adicional",
        "Mesa con dos piezas de vidrio",
        "Mesa, una pieza de MDF de 18 mm",
    ],
)
def test_no_inferir_cantidad_de_capacidad_componentes_ni_ambiguos(texto):
    r = extraer(texto)
    assert r.item_proposal.quantity is None
    assert not [c for c in r.candidates if c.label == "CANTIDAD" and c.decision == "ACCEPTED"]
    assert any(w.code == "NO_QUANTITY" for w in r.warnings)


def test_cantidad_pospuesta_habilita_total_unitario_sin_inventar_precio():
    r = extraer(
        "Mesa de reunión para 10 personas, una pieza tamaño 2.4 metros, precio unitario 7300"
    )
    assert r.item_proposal.quantity == 1
    assert r.item_proposal.price.mode == "PRECIO_UNITARIO"
    assert r.item_proposal.price.line_total == "7300.00"
    assert r.item_proposal.price.unit_price_input == "7300.00"


def test_cantidad_pospuesta_y_total_negociado_no_convierten_precio_a_unitario():
    r = extraer("Mesa, dos unidades, alto 75 centímetros, precio total 7600 bolivianos")
    assert r.item_proposal.quantity == 2
    assert r.item_proposal.price.mode == "TOTAL_NEGOCIADO"
    assert r.item_proposal.price.line_total == "7600.00"
    assert r.item_proposal.price.unit_price_reference == "3800"


@pytest.mark.parametrize(
    ("texto", "nombre", "cantidad"),
    [
        (
            "dos tomacorrientes al centro estructura en tablero melamínico",
            "tomacorrientes al centro",
            2,
        ),
        ("dos tomacorrientes al centro de estructura en melamina", "tomacorrientes al centro", 2),
        ("dos tomacorrientes al centro precio total 7300", "tomacorrientes al centro", 2),
        ("dos tomacorrientes al centro dimensiones por definir", "tomacorrientes al centro", 2),
        ("dos tomacorrientes al centro, estructura de MDF", "tomacorrientes al centro", 2),
        ("tapacanto en PVC y dos tomacorrientes al centro", "tapacanto en PVC", None),
        ("dos bisagras de acero inoxidable", "bisagras de acero inoxidable", 2),
        ("una bandeja de estructura metálica", "bandeja de estructura metálica", 1),
        ("dos jaladores en estructura madera", "jaladores en estructura madera", 2),
    ],
)
def test_accesorios_sin_sangrar_clausulas_y_sin_recortar_atributos(texto, nombre, cantidad):
    found = find_accessories(texto)
    match = found[0]
    assert match.text == nombre
    assert match.value == cantidad
    assert texto[match.start : match.end] == match.text


def test_tomas_corrientes_con_ruido_asr_en_captura_mesa():
    texto = (
        "Mesa de reunión para 10 personas, una pieza tamaño 2.4 metros de largo y dos "
        "tomacorrientes al centro estructura en tablero melamínico precio unitario 7300"
    )
    r = extraer(texto)
    assert r.item_proposal.quantity == 1
    assert r.item_proposal.price.mode == "PRECIO_UNITARIO"
    assert r.item_proposal.accessories[0].name == "tomacorrientes al centro"
    assert r.item_proposal.accessories[0].quantity == 2
    assert all(texto[c.start : c.end] == c.text for c in r.candidates)


def test_version_paquete_y_modo_invariables():
    assert __version__ == "0.1.17"
    r = extraer("Una mesa alto dos metros")
    assert r.engine.mode == "RULES_ONLY"
    assert r.engine.model_version is None
    assert r.schema_version == "1.0"
    assert r.item_proposal.price is None
