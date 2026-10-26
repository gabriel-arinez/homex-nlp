"""Independent fixtures and destructive-in-memory mutation checks for the candidate."""

import hashlib
import json
from pathlib import Path

import pytest

from training.corpus_v2.semantic import audit_literal
from training.corpus_v2.validate import validate, validate_record

ROOT = Path(__file__).resolve().parents[2]
CANDIDATE = ROOT / "data/candidates/corpus_v2_rc1"
LABELS = set(json.loads((ROOT / "data/manifests/prf04_labels.json").read_text())["labels"])


def fixture():
    text = "Mesa. Cantidad: 2 piezas; total 6000, sin descuento."
    row = {
        "id": "independent-fixture",
        "text": text,
        "text_sha256": hashlib.sha256(text.encode()).hexdigest(),
        "category": "muebles_pedido",
        "origin": "SINTETICO_ORAL",
        "human_reviewed": False,
        "source_ref": {"kind": "INDEPENDENT_TEST"},
        "leakage_group": "test-fixture",
        "split": "dev",
        "entities": [
            [0, 4, "PRODUCTO"],
            [16, 17, "CANTIDAD"],
            [18, 24, "UNIDAD_MEDIDA"],
            [32, 36, "PRECIO_TOTAL"],
        ],
        "status": "REQUIRES_REVIEW",
    }
    ref = {
        "id": row["id"],
        "text_sha256": row["text_sha256"],
        "status": "REQUIRES_REVIEW",
        "human_reviewed": False,
        "comercial": {
            "nombre": "Mesa",
            "cantidad": "2",
            "unidad_codigo": "PIEZA",
            "precio_total_explicito": "6000",
            "precio_unitario": None,
            "descuento_linea": "0",
            "moneda_codigo": None,
        },
        "especificacion": {
            "datos_tecnicos": {"descripcion_original": text, "componentes": [], "conjuntos": []}
        },
        "facts": [
            {
                "path": p,
                "value": v,
                "evidence": {"start": a, "end": b, "text": text[a:b]},
                "rule": "MANUAL_TEST",
            }
            for p, v, a, b in [
                ("comercial.nombre", "Mesa", 0, 4),
                ("comercial.cantidad", "2", 16, 17),
                ("comercial.unidad_codigo", "PIEZA", 18, 24),
                ("comercial.precio_total_explicito", "6000", 32, 36),
                ("comercial.descuento_linea", "0", 38, 51),
            ]
        ],
    }
    # Explicit literal evidence; do not call any reference generator.
    ref["facts"][-1]["evidence"] = {"start": 38, "end": 51, "text": text[38:51]}
    return row, ref


def codes(row, ref):
    return {e["code"] for e in validate_record(row, ref, LABELS)}


def test_independent_fixture_is_valid():
    row, ref = fixture()
    assert not codes(row, ref)


@pytest.mark.parametrize(
    "mutation,expected",
    [
        ("offset", "SPAN_BOUNDS"),
        ("overlap", "SPAN_OVERLAP"),
        ("label", "LABEL"),
        ("family", "FAMILY"),
        ("hash", "TEXT_HASH"),
        ("human", "HUMAN_ATTRIBUTION"),
        ("reference_id", "REFERENCE_ID"),
        ("quantity", "FACT_VALUE"),
        ("facts", "COMMERCIAL_WITHOUT_EVIDENCE:cantidad"),
        ("evidence", "FACT_EVIDENCE"),
        ("invented_price", "COMMERCIAL_WITHOUT_EVIDENCE:precio_unitario"),
        ("currency", "COMMERCIAL_WITHOUT_EVIDENCE:moneda_codigo"),
        ("schema", "COMMERCIAL_SCHEMA_VERSION"),
        ("abstain", "ABSTAIN_PROPOSAL"),
        ("unit", "FACT_VALUE"),
        ("components", "PRF03_LIMIT"),
        ("bad_derivation", "UNIT_PRICE_DERIVATION"),
        ("split", "SPLIT"),
        ("provenance", "PROVENANCE"),
    ],
)
def test_rejects_independent_corruption(mutation, expected):
    row, ref = fixture()
    if mutation == "offset":
        row["entities"][0][1] = 999
    elif mutation == "overlap":
        row["entities"].append([33, 36, "PRECIO_TOTAL"])
    elif mutation == "label":
        row["entities"][0][2] = "CANTIDAD_INTERNA"
    elif mutation == "family":
        row["category"] = "MUEBLE_CATALOGO"
    elif mutation == "hash":
        row["text_sha256"] = "0" * 64
    elif mutation == "human":
        ref["human_reviewed"] = True
    elif mutation == "reference_id":
        ref["id"] = "different"
    elif mutation == "quantity":
        ref["comercial"]["cantidad"] = "10"
    elif mutation == "facts":
        ref["facts"] = [f for f in ref["facts"] if f["path"] != "comercial.cantidad"]
    elif mutation == "evidence":
        ref["facts"][0]["evidence"]["text"] = "Silla"
    elif mutation == "invented_price":
        ref["comercial"]["precio_unitario"] = "3000"
    elif mutation == "currency":
        ref["comercial"]["moneda_codigo"] = "BOB"
    elif mutation == "schema":
        ref["especificacion"]["datos_tecnicos"]["schema_version"] = "1.0"
    elif mutation == "abstain":
        row["status"] = ref["status"] = "ABSTAIN"
    elif mutation == "unit":
        ref["comercial"]["unidad_codigo"] = "BARRA"
    elif mutation == "components":
        ref["especificacion"]["datos_tecnicos"]["componentes"] = [
            {"uid": str(i), "nombre": "Falso"} for i in range(41)
        ]
    elif mutation == "bad_derivation":
        ref["derived_unit_price"] = "2999.99"
    elif mutation == "split":
        row["split"] = "unknown"
    elif mutation == "provenance":
        row["source_ref"] = None
    assert expected in codes(row, ref)


def test_exact_unit_requires_explicit_discount_and_cent_precision():
    row, ref = fixture()
    ref["derived_unit_price"] = "3000.00"
    assert not codes(row, ref)
    ref["comercial"]["descuento_linea"] = None
    ref["facts"] = [f for f in ref["facts"] if f["path"] != "comercial.descuento_linea"]
    assert "UNIT_PRICE_DERIVATION" in codes(row, ref)
    ref["comercial"]["descuento_linea"] = "0"
    ref["comercial"]["cantidad"] = "3"
    ref["comercial"]["precio_total_explicito"] = "1000"
    ref["derived_unit_price"] = "333.33"
    assert "UNIT_PRICE_DERIVATION" in codes(row, ref)


def test_literal_auditor_does_not_accept_ner_or_runtime_expected():
    # Independent full expected values, not predictions transformed into references.
    text = "ESCRITORIO. Medidas generales: alto 0.75 m; ancho 120 cm; profundidad 60 cm; Tablero: melamina, espesor 18 mm, color Blanco. Mesón: melamina, espesor 27 mm, color Cedro. Incorpora tres repisas interiores; Cantidad: 2 piezas. precio unitario Bs 1.200,00; descuento de línea Bs 100,00; total por este producto Bs 2.300,00."
    result = audit_literal(text, "muebles_pedido")
    assert not result["errors"]
    assert result["comercial"] == {
        "nombre": "ESCRITORIO",
        "cantidad": "2",
        "unidad_codigo": "PIEZA",
        "precio_unitario": "1200.00",
        "precio_total_explicito": "2300.00",
        "moneda_codigo": "BOB",
        "descuento_linea": "100.00",
    }
    comps = result["especificacion"]["datos_tecnicos"]["componentes"]
    assert [(c["nombre"], c["espesor"], c["color"]) for c in comps] == [
        ("Tablero", "18 mm", "Blanco"),
        ("Mesón", "27 mm", "Cedro"),
    ]
    assert result["cantidades_internas"][0]["cantidad_interna"] == 3


def test_all_records_and_manifests_pass_independent_validation():
    report = validate(CANDIDATE, ROOT)
    assert report["valid"], report["errors"][:10]
    assert report["records"] == 727


def test_no_historical_test_record_in_training():
    for path in (CANDIDATE / "04_CORPUS_DOCUMENTAL_V2").glob("*.jsonl"):
        old = {
            r["id"]: r
            for r in map(json.loads, (ROOT / "data/corpus" / path.name).read_text().splitlines())
        }
        for r in map(json.loads, path.read_text().splitlines()):
            if r.get("v1_id") and old[r["v1_id"]]["split"] == "test":
                assert r["split"] == "test"


def test_challenge_references_do_not_invent_ambiguous_fields():
    refs = {
        r["id"]: r
        for p in (CANDIDATE / "06_EXPECTED_ESTRUCTURADOS_V2").glob("*.jsonl")
        for r in map(json.loads, p.read_text().splitlines())
    }
    assert refs["V2-REC-A21"]["comercial"]["cantidad"] is None
    assert refs["V2-REC-A23"]["comercial"]["precio_unitario"] is None
    assert refs["V2-REC-A23"]["comercial"]["precio_total_explicito"] is None
    assert refs["V2-REC-A24"]["status"] == "ABSTAIN"
    assert (
        refs["V2-REC-A30"]["especificacion"]["datos_tecnicos"]["caracteristicas_generales"]["color"]
        == "blanco"
    )
    assert refs["V2-REC-A36"]["comercial"]["moneda_codigo"] == "USD"
    assert refs["V2-REC-A46"]["comercial"]["cantidad"] is None


def test_component_attributes_cannot_borrow_other_component_evidence():
    row, ref = fixture()
    text = "Mesa. Tablero de melamina. Patas de acero."
    row.update(text=text, text_sha256=hashlib.sha256(text.encode()).hexdigest(), entities=[])
    ref.update(text_sha256=row["text_sha256"], comercial={k: None for k in ref["comercial"]})
    tech = {
        "descripcion_original": text,
        "componentes": [
            {"uid": "c1", "nombre": "Tablero", "material": "melamina"},
            {"uid": "c2", "nombre": "Patas", "material": "acero"},
        ],
        "conjuntos": [],
    }
    ref["especificacion"]["datos_tecnicos"] = tech
    literals = [
        ("componentes.c1.nombre", "Tablero", 6, 13),
        ("componentes.c1.material", "melamina", 17, 25),
        ("componentes.c2.nombre", "Patas", 27, 32),
        ("componentes.c2.material", "acero", 36, 41),
    ]
    # Calculate evidence positions from these explicit, unique fixture words.
    ref["facts"] = [
        {
            "path": p,
            "value": value,
            "evidence": {
                "start": text.index(value),
                "end": text.index(value) + len(value),
                "text": value,
            },
            "rule": "INDEPENDENT_FIXTURE",
        }
        for p, value, _, _ in literals
    ]
    assert not codes(row, ref)
    tech["componentes"][0]["material"] = "acero"
    ref["facts"][1].update(value="acero", evidence=ref["facts"][3]["evidence"])
    assert "ATTRIBUTE_SCOPE" in codes(row, ref)
