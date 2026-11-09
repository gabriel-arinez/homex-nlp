"""Invented evidence examples; no documentary commercial text."""

from homex_nlp.contracts import ExtractionRequest, ExtractionResult
from training.integral_v2.assembler import IntegralNerEngine


def assemble(text, annotations):
    engine = IntegralNerEngine.__new__(IntegralNerEngine)
    engine.model_version = "invented-test"
    spans = []
    start = 0
    for literal, label in annotations:
        a = text.index(literal, start)
        spans.append((a, a + len(literal), label))
        start = a + len(literal)
    result = engine.assemble(
        ExtractionRequest(request_id="invented", text=text, currency_context="BOB"), spans
    )
    return ExtractionResult.model_validate(result.model_dump())


def test_distinct_component_thicknesses_and_internal_count():
    text = "Tres mesas inventadas, tapa MDP 29 mm y patas metal 17 mm; dos cajones."
    r = assemble(
        text,
        [
            ("Tres", "CANTIDAD"),
            ("mesas inventadas", "PRODUCTO"),
            ("tapa", "COMPONENTE"),
            ("MDP", "MATERIAL"),
            ("29 mm", "ESPESOR"),
            ("patas", "COMPONENTE"),
            ("metal", "MATERIAL"),
            ("17 mm", "ESPESOR"),
            ("cajones", "COMPONENTE"),
        ],
    )
    assert r.item_proposal.quantity == 3
    assert len({m.component_ref for m in r.item_proposal.thicknesses}) == 2
    internal = [c for c in r.candidates if c.label == "CANTIDAD_INTERNA"]
    assert internal[-1].normalized_value == 2
    assert internal[-1].component_ref == r.item_proposal.components[-1].component_id


def test_negation_does_not_fabricate_accessory():
    r = assemble(
        "Una mesa inventada sin jaladores.",
        [("Una", "CANTIDAD"), ("mesa inventada", "PRODUCTO"), ("jaladores", "ACCESORIO")],
    )
    assert r.item_proposal.accessories == []


def test_quantity_rectification():
    r = assemble(
        "Dos, no, cuatro mesas inventadas.",
        [("Dos", "CANTIDAD"), ("cuatro", "CANTIDAD"), ("mesas inventadas", "PRODUCTO")],
    )
    assert r.item_proposal.quantity == 4


def test_repeated_product_not_two_sales():
    r = assemble(
        "Una mesa inventada. La mesa inventada lleva madera.",
        [
            ("Una", "CANTIDAD"),
            ("mesa inventada", "PRODUCTO"),
            ("mesa inventada", "PRODUCTO"),
            ("madera", "MATERIAL"),
        ],
    )
    assert r.item_proposal is not None


def test_two_distinct_products_abstain():
    r = assemble(
        "Una mesa y un armario.",
        [("Una", "CANTIDAD"), ("mesa", "PRODUCTO"), ("armario", "PRODUCTO")],
    )
    assert r.item_proposal is None


def test_unit_absent_is_not_inferred():
    r = assemble(
        "Una mesa inventada ancho uno veinte.",
        [("Una", "CANTIDAD"), ("mesa inventada", "PRODUCTO"), ("uno veinte", "ANCHO")],
    )
    assert r.item_proposal.dimensions == []


def test_axis_absent_is_not_inferred_from_label():
    r = assemble(
        "Una mesa inventada de 139 cm.",
        [("Una", "CANTIDAD"), ("mesa inventada", "PRODUCTO"), ("139 cm", "ANCHO")],
    )
    assert r.item_proposal.dimensions == []


def test_negotiated_exact_reference_only_when_discount_explicit_zero():
    text = "Tres mesas inventadas, total novecientos, descuento cero."
    r = assemble(
        text,
        [
            ("Tres", "CANTIDAD"),
            ("mesas inventadas", "PRODUCTO"),
            ("novecientos", "PRECIO_TOTAL"),
            ("cero", "DESCUENTO"),
        ],
    )
    assert r.item_proposal.price.mode == "TOTAL_NEGOCIADO"
    assert r.item_proposal.price.unit_price_reference == "300.00"
    r = assemble(
        "Tres mesas inventadas, total novecientos.",
        [("Tres", "CANTIDAD"), ("mesas inventadas", "PRODUCTO"), ("novecientos", "PRECIO_TOTAL")],
    )
    assert r.item_proposal.price.unit_price_reference is None


def test_non_exact_cent_division_abstains_reference():
    r = assemble(
        "Tres mesas inventadas total mil, descuento cero.",
        [
            ("Tres", "CANTIDAD"),
            ("mesas inventadas", "PRODUCTO"),
            ("mil", "PRECIO_TOTAL"),
            ("cero", "DESCUENTO"),
        ],
    )
    assert r.item_proposal.price.unit_price_reference is None


def test_late_pending_color_cancels_earlier_choice():
    r = assemble(
        "Una mesa inventada color verde, no, dejá a elección.",
        [("Una", "CANTIDAD"), ("mesa inventada", "PRODUCTO"), ("verde", "COLOR")],
    )
    assert not any(c.label == "COLOR" and c.decision == "ACCEPTED" for c in r.candidates)


def test_nearby_other_axis_does_not_license_wrong_axis():
    r = assemble(
        "Una mesa inventada, alto 77 cm y ancho 139 cm.",
        [("Una", "CANTIDAD"), ("mesa inventada", "PRODUCTO"), ("139 cm", "ALTO")],
    )
    assert r.item_proposal.dimensions == []


def test_price_label_without_commercial_role_is_not_enough():
    r = assemble(
        "Una mesa inventada de 31 mm.",
        [("Una", "CANTIDAD"), ("mesa inventada", "PRODUCTO"), ("31", "PRECIO_UNITARIO")],
    )
    assert r.item_proposal.price is None


def test_each_piece_is_explicit_unit_price():
    r = assemble(
        "Tres mesas inventadas, cuatrocientos diez cada pieza.",
        [
            ("Tres", "CANTIDAD"),
            ("mesas inventadas", "PRODUCTO"),
            ("cuatrocientos diez", "PRECIO_UNITARIO"),
        ],
    )
    assert r.item_proposal.price.mode == "PRECIO_UNITARIO"
    assert r.item_proposal.price.line_total == "1230.00"


def test_whole_lot_is_explicit_total_and_abstention_version_is_current():
    r = assemble(
        "Dos mesas inventadas, novecientos por todo el lote.",
        [("Dos", "CANTIDAD"), ("mesas inventadas", "PRODUCTO"), ("novecientos", "PRECIO_TOTAL")],
    )
    assert r.item_proposal.price.mode == "TOTAL_NEGOCIADO"
    r = assemble("No generes una propuesta.", [])
    assert r.engine.rules_version == "integral-offline-assembler-2"
