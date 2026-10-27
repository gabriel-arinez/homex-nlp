from homex_nlp.contracts import ExtractionRequest
from homex_nlp.engine import RulesEngine


def run(texto):
    return RulesEngine().extract(
        ExtractionRequest(request_id="comercial-v5", text=texto, currency_context="BOB")
    )


def test_cantidad_de_mesas_no_es_capacidad():
    result = run("Dos mesas de reunión para diez personas y dos tomacorrientes")
    assert result.item_proposal.quantity == 2
    assert not any(w.code == "NO_QUANTITY" for w in result.warnings)
    sin_cantidad = run("Mesa de reunión para diez personas con dos tomacorrientes")
    assert sin_cantidad.item_proposal.quantity is None


def test_unitario_explicito_y_total_declarado():
    item = run("Una mesa, precio unitario de 7300 bolivianos").item_proposal
    assert item.quantity == 1
    assert item.price.mode == "PRECIO_UNITARIO"
    assert item.price.unit_price_input == "7300.00"
    total = run("Dos mesas, el precio total de las dos mesas es de 7.300 bolivianos")
    assert total.item_proposal.quantity == 2
    assert total.item_proposal.price.mode == "TOTAL_NEGOCIADO"
    assert total.item_proposal.price.line_total == "7300.00"
    assert total.item_proposal.price.unit_price_reference == "3650"


def test_importe_ambiguo_no_inventa_modalidad():
    result = run("Una mesa, precio 7300")
    assert result.item_proposal.price is None
    assert any(
        c.label == "PRECIO_AMBIGUO" and c.decision == "UNRESOLVED" for c in result.candidates
    )
    assert any(w.code == "REQUIRED_FIELD_MISSING" for w in result.warnings)


def test_cantidad_comercial_oral():
    result = run("Mesa, cantidad de dos unidades, total 7300")
    assert result.item_proposal.quantity == 2
    assert result.item_proposal.price.line_total == "7300.00"
