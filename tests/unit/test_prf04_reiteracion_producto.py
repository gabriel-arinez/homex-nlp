"""Caso real detectado al validar el adaptador NLP 0.1.4 de PRF-04."""

from homex_nlp.contracts import ExtractionRequest
from homex_nlp.engine import RulesEngine


def extraer(texto):
    return RulesEngine().extract(
        ExtractionRequest(request_id="reiteracion-producto", text=texto, currency_context="BOB")
    )


def test_nombre_compuesto_y_total_reiterado_no_crean_segundo_producto():
    texto = "Dos mesas de reunión para diez personas, precio total de las dos mesas 7300 bolivianos"
    resultado = extraer(texto)
    assert resultado.status == "REQUIRES_REVIEW"
    item = resultado.item_proposal
    assert item is not None
    assert item.name == "mesas de reunión para diez personas"
    assert item.quantity == 2
    assert item.price is not None
    assert item.price.mode == "TOTAL_NEGOCIADO"
    assert item.price.line_total == "7300.00"
    assert item.price.unit_price_reference == "3650"
    assert not any(w.code == "MULTIPLE_MAIN_PRODUCTS" for w in resultado.warnings)


def test_total_reiterado_con_verbo_y_separadores():
    resultado = extraer(
        "Dos mesas de reunión para diez personas, "
        "el precio total de las dos mesas es de 7.300 bolivianos"
    )
    assert resultado.item_proposal is not None
    assert resultado.item_proposal.quantity == 2
    assert resultado.item_proposal.price.line_total == "7300.00"


def test_cantidades_distintas_no_se_unifican_silenciosamente():
    resultado = extraer(
        "Dos mesas de reunión para diez personas, precio total de las tres mesas 7300 bolivianos"
    )
    assert resultado.status == "NO_PROPOSAL"
    assert any(w.code == "MULTIPLE_MAIN_PRODUCTS" for w in resultado.warnings)


def test_otro_producto_real_sigue_rechazado():
    resultado = extraer(
        "Dos mesas de reunión y un escritorio, precio total de las dos mesas 7300 bolivianos"
    )
    assert resultado.status == "NO_PROPOSAL"
    assert any(w.code == "MULTIPLE_MAIN_PRODUCTS" for w in resultado.warnings)


def test_se_mantiene_la_extraccion_anterior():
    resultado = extraer("Dos mesas, el precio total de las dos mesas es de 7.300 bolivianos")
    assert resultado.item_proposal is not None
    assert resultado.item_proposal.quantity == 2
    assert resultado.item_proposal.price.line_total == "7300.00"
