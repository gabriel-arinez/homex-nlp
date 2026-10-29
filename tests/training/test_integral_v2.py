"""All literals in these tests are invented, never documentary HOMEX text."""

from copy import deepcopy

import pytest

from training.canonical_v2.io import digest
from training.integral_v2.build import partition
from training.integral_v2.review import CHECKS, leaves, payload, seal, validate_review
from training.integral_v2.tokenizer import create_nlp


def fixture():
    text = "Mesa inventada; mesón de 29 mm, patas de 17 mm. 3 piezas."
    item = {
        "id": "invented-1",
        "item_text": text,
        "source_sha256": digest("invented"),
        "char_start": 70,
        "document_level": "COTIZACION_SIN_ID_PROFORMA",
    }
    expected = {
        "comercial": {
            "nombre": "Mesa inventada",
            "cantidad": "3",
            "precio_unitario": None,
            "precio_total_explicito": None,
        },
        "especificacion": {
            "datos_tecnicos": {
                "descripcion_original": text,
                "componentes": [],
                "conjuntos": [],
                "accesorios": [],
                "caracteristicas_generales": {},
                "advertencias": [],
            }
        },
    }
    evidence = {
        "start": 0,
        "end": len(text),
        "text": text,
        "source_start": 70,
        "source_end": 70 + len(text),
    }
    review = {
        "item_id": item["id"],
        "source_sha256": item["source_sha256"],
        "text_sha256": digest(text),
        "human_reviewed": False,
        "review_kind": "REVISION_TECNICA_ASISTIDA",
        "decision": "APTO",
        "reason": "Invented fixture, no domain validation claim",
        "supervised": True,
        "checklist": dict.fromkeys(CHECKS, True),
        "annotation_scope": "FULL_ITEM",
        "entities": [[0, 14, "PRODUCTO"], [46, 47, "CANTIDAD"]],
        "expected": expected,
        "coverage": [{"start": 0, "end": len(text), "text": text, "role": "REVIEWED_CONTEXT"}],
        "facts": [
            {
                "path": p,
                "value": v,
                "state": "AUSENTE" if v is None else "EXPLICITO",
                "rule": "INVENTED_FIXTURE",
                "evidence": [] if v is None else [evidence],
            }
            for p, v in leaves(expected)
        ],
    }
    start = text.index("3 piezas")
    review["entities"][1][:2] = [start, start + 1]
    for fact in review["facts"]:
        fact["entity_refs"] = [0, 1]
    coverage = []
    cursor = 0
    for a, b, _ in review["entities"]:
        if a > cursor:
            coverage.append(
                {"start": cursor, "end": a, "text": text[cursor:a], "role": "REVIEWED_CONTEXT"}
            )
        coverage.append({"start": a, "end": b, "text": text[a:b], "role": "ENTITY"})
        cursor = b
    if cursor < len(text):
        coverage.append(
            {"start": cursor, "end": len(text), "text": text[cursor:], "role": "REVIEWED_CONTEXT"}
        )
    review["coverage"] = coverage
    return item, review, seal(payload(review))


def test_invented_review():
    validate_review(*fixture())


@pytest.mark.parametrize(
    "mutator",
    [
        lambda r: r["entities"].clear(),
        lambda r: r["entities"][0].__setitem__(0, 1),
        lambda r: r.__setitem__("human_reviewed", True),
        lambda r: r.__setitem__("annotation_scope", "INCOMPLETE_FULL_ITEM"),
        lambda r: r["checklist"].pop("component_scope"),
        lambda r: r["expected"]["comercial"].__setitem__("cantidad", "8"),
        lambda r: r["facts"][0].__setitem__("value", "false"),
        lambda r: r["coverage"][0].__setitem__("end", 12),
        lambda r: r["facts"][0]["evidence"][0].__setitem__("source_start", 71),
        lambda r: r["facts"].pop(),
    ],
)
def test_mutation_cannot_reuse_certificate(mutator):
    item, review, certificate = fixture()
    changed = deepcopy(review)
    mutator(changed)
    with pytest.raises(ValueError, match="ADJUDICATION_CHANGED|FALSE_HUMAN_REVIEW"):
        validate_review(item, changed, certificate)


def test_semantic_validation_even_with_new_certificate():
    item, review, _ = fixture()
    review["facts"][0]["evidence"][0]["start"] = 1
    with pytest.raises(ValueError, match="FACT_OFFSET"):
        validate_review(item, review, seal(payload(review)))


def test_partial_cannot_be_certified_complete():
    item, review, _ = fixture()
    review["annotation_scope"] = "INCOMPLETE_FULL_ITEM"
    with pytest.raises(ValueError, match="PARTIAL_AS_COMPLETE"):
        validate_review(item, review, seal(payload(review)))


def test_unreviewed_field_rejected_even_with_new_certificate():
    item, review, _ = fixture()
    review["expected"]["comercial"]["descuento"] = "7"
    with pytest.raises(ValueError, match="UNREVIEWED_EXPECTED_FIELD"):
        validate_review(item, review, seal(payload(review)))


def test_exclusion_needs_reason_and_no_training():
    item, review, _ = fixture()
    review.update(decision="CUARENTENA", supervised=False, conflicts=["Invented ambiguity"])
    validate_review(item, review, seal(payload(review)))
    review["supervised"] = True
    with pytest.raises(ValueError, match="EXCLUDED_SUPERVISION"):
        validate_review(item, review, seal(payload(review)))


def test_numeric_template_variants_stay_together_across_sources():
    records = [
        {"id": "a", "item_text": "Mesa inventada de 100 cm, 3 piezas"},
        {"id": "b", "item_text": "Mesa inventada de 140 cm, 5 piezas"},
        {"id": "c", "item_text": "Solicitud sin una línea comercial identificable"},
    ]
    assignment, edges = partition(records)
    assert assignment["a"] == assignment["b"]
    assert edges[0]["similarity"] == 1
    assert partition(records) == (assignment, edges)


def test_offline_glued_punctuation_alignment():
    nlp = create_nlp()
    text = "Altura=0.85m, mts.de, Bs17,50"
    doc = nlp.make_doc(text)
    for literal in ("0.85m", "mts", "de", "17,50"):
        start = text.index(literal)
        assert doc.char_span(start, start + len(literal), alignment_mode="strict") is not None


def test_internal_quantity_cannot_become_sold_quantity_with_new_certificate():
    item, review, _ = fixture()
    review["entities"][1][2] = "OBSERVACION"
    with pytest.raises(ValueError, match="COMMERCIAL_INTERNAL_QUANTITY_OR_PRICE_CONFUSION"):
        validate_review(item, review, seal(payload(review)))


def test_total_cannot_become_arbitrary_unit_price_with_new_certificate():
    item, review, _ = fixture()
    review["expected"]["comercial"]["precio_unitario"] = "19"
    fact = next(f for f in review["facts"] if f["path"] == "/comercial/precio_unitario")
    fact.update(value="19", state="DERIVADO_EXACTO", evidence=[review["facts"][0]["evidence"][0]])
    with pytest.raises(ValueError, match="UNAUTHORIZED_COMMERCIAL_DERIVATION"):
        validate_review(item, review, seal(payload(review)))


def test_wrong_group_reference_fails_with_new_certificate():
    item, review, _ = fixture()
    tech = review["expected"]["especificacion"]["datos_tecnicos"]
    tech["componentes"] = [{"uid": "c1", "nombre": "pata", "conjunto_uid": "unknown"}]
    with pytest.raises(ValueError, match="ORPHAN_COMPONENT"):
        validate_review(item, review, seal(payload(review)))


def test_named_axis_without_unit_cannot_be_supervised_as_o():
    item, review, _ = fixture()
    item["item_text"] += " 1.73 de ancho."
    review["text_sha256"] = digest(item["item_text"])
    with pytest.raises(ValueError, match="UNANNOTATED_NAMED_AXIS"):
        validate_review(item, review, seal(payload(review)))


def test_multisegment_named_axis_cannot_be_reduced_to_last_scalar():
    item, review, _ = fixture()
    item["item_text"] += " 1.73 x 1.81m de ancho."
    review["text_sha256"] = digest(item["item_text"])
    with pytest.raises(ValueError, match="UNANNOTATED_COMPLEX_AXIS"):
        validate_review(item, review, seal(payload(review)))
