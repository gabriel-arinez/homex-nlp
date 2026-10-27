"""Mutation/regression checks; no private documents or model fitting in CI."""

from copy import deepcopy

import pytest

from training.canonical_v2.build import documentary
from training.canonical_v2.experiment import ner_metrics
from training.canonical_v2.io import digest, private_path, read
from training.canonical_v2.patches_v1 import patches
from training.canonical_v2.validate import ROOT, validate


@pytest.fixture
def corpus():
    return read(ROOT / "data/canonical_v2/synthetic.jsonl"), read(
        ROOT / "data/canonical_v2/synthetic_expected.jsonl"
    )


def test_canonical_synthetic_and_docbin_roundtrip(corpus, tmp_path):
    rows, refs = corpus
    result = validate(rows, refs, docbin=tmp_path)
    assert result["valid"], result["errors"]
    assert result["records"] == 66
    assert result["splits"] == {"train": 39, "dev": 27}
    assert len(result["labels"]) == 24
    assert (tmp_path / "train.spacy").exists()


@pytest.mark.parametrize(
    "mutation,code",
    [
        ("hash", "TEXT_HASH"),
        ("label", "UNKNOWN_LABEL"),
        ("overlap", "BOUNDS_OVERLAP"),
        ("out_of_range", "BOUNDS_OVERLAP"),
        ("alignment", "TOKEN_ALIGNMENT"),
        ("negative", "NEGATIVE_OR_ZERO_VALUE"),
        ("precision", "PRICE_PRECISION"),
        ("arithmetic", "PRICE_ARITHMETIC"),
        ("evidence", "FACT_EVIDENCE"),
        ("group", "CROSS_SPLIT_GROUP_OR_DUPLICATE"),
        ("human", "FALSE_HUMAN_REVIEW"),
        ("missing", "REFERENCE_HASH_OR_MISSING"),
    ],
)
def test_mutations_fail_closed(corpus, mutation, code):
    rows, refs = deepcopy(corpus)
    by = {r["id"]: r for r in refs}
    r = next(r for r in rows if r["id"] == "RC2-recepcion-cableado")
    ref = by[r["id"]]
    if mutation == "hash":
        r["text_sha256"] = "bad"
    elif mutation == "label":
        r["entities"][0][2] = "UNKNOWN"
    elif mutation == "overlap":
        r["entities"].insert(1, deepcopy(r["entities"][0]))
    elif mutation == "out_of_range":
        r["entities"][0][1] = len(r["text"]) + 1
    elif mutation == "alignment":
        r["entities"][0][0] += 1
    elif mutation == "negative":
        ref["comercial"]["cantidad"] = "-1"
    elif mutation == "precision":
        ref["comercial"]["precio_unitario"] = "2380.001"
    elif mutation == "arithmetic":
        ref["comercial"]["precio_total_explicito"] = "99"
    elif mutation == "evidence":
        ref["facts"][0]["evidence"]["text"] = "wrong"
    elif mutation == "group":
        r["leakage_group"] = next(x["leakage_group"] for x in rows if x["split"] == "dev")
    elif mutation == "human":
        r["human_reviewed"] = True
    elif mutation == "missing":
        refs.remove(ref)
    report = validate(rows, refs)
    assert not report["valid"]
    assert code in {e["code"] for e in report["errors"]}


def test_frozen_test_never_receives_overlay():
    assert patches({"split": "test"}) is None


def test_49_reversible_extensions_without_changing_v1():
    changes = []
    for path in (ROOT / "data/corpus").glob("*.jsonl"):
        for row in read(path):
            original = deepcopy(row)
            overlay = patches(row)
            assert row == original
            if overlay and overlay["operations"]:
                changes.append(overlay)
                assert all(
                    op["rule"] == "MEMBRANA_INCLUDE_EXPLICIT_NOUN" for op in overlay["operations"]
                )
    assert len(changes) == 49


def item(text, **extra):
    return dict(
        id="fixture",
        item_text=text,
        source_file="PROFORMAS.txt",
        source_sha256=digest(text),
        document_level="COTIZACION_SIN_ID_PROFORMA",
        proforma_id=None,
        line_start=1,
        line_end=2,
        char_start=0,
        **extra,
    )


def test_authentic_literal_excerpts_keep_offset_and_component_scope():
    source = item(
        "MESA CIRCULAR\n1,00 Pza. Mesón de melamina de 25mm. Patas de melamina de 18mm. precio unitario 1500,00. total 1500,00."
    )
    rows, refs, _ = documentary([source], set())
    for row in rows:
        a, b = row["source_ref"]["item_offset"]
        assert row["text"] == source["item_text"][a:b]
        assert row["origin"] == "DOCUMENTO_HOMEX_LITERAL"
        assert row["source_ref"]["certainty"] == "CONFIRMADA"
    components = [c for ref in refs for c in ref["especificacion"]["datos_tecnicos"]["componentes"]]
    assert [(c["nombre"], c["espesor"]) for c in components] == [
        ("Mesón", "25mm"),
        ("Patas", "18mm"),
    ]
    assert validate(rows, refs)["valid"]


def test_quarantined_document_never_trains():
    rows, refs, _ = documentary(
        [item("GAVETERO\nprecio unitario 1800,00. total 1700,00.")], {"fixture"}
    )
    assert not rows and not refs


def test_catalog_price_is_not_negotiated_price():
    source = item("SILLA COD: EXAMPLE\tFicha de prueba\tBs1.500,00")
    source.update(source_file="inventario de sillas.txt", document_level="CATALOGO")
    rows, refs, _ = documentary([source], set())
    prices = [r for r in refs if "catalog_price" in r]
    assert prices[0]["catalog_price"] == "1500.00"
    assert prices[0]["comercial"]["precio_unitario"] is None
    assert validate(rows, refs)["valid"]


def test_private_output_rejected_inside_checkout():
    with pytest.raises(ValueError, match="PRIVATE_ARTIFACT_INSIDE_GIT"):
        private_path(ROOT / "data/private-forbidden")


def test_metric_counts_label_substitution_as_fp_and_fn():
    rows = [dict(entities=[[0, 4, "PRODUCTO"]])]
    scores = ner_metrics(rows, [[(0, 4, "MATERIAL")]])
    assert scores["micro"]["tp"] == 0
    assert scores["micro"]["fp"] == scores["micro"]["fn"] == 1
    assert scores["error_matrix"] == {"PRODUCTO -> MATERIAL": 1}


def test_second_literal_material_is_annotated(corpus):
    rows, _ = corpus
    r = next(r for r in rows if r["id"] == "V2-REC-A33")
    assert sum(label == "MATERIAL" for _, _, label in r["entities"]) == 2


@pytest.mark.parametrize("field", ["quantity", "price", "dimensions"])
def test_ablation_preserves_v15_contract_and_original(field):
    from homex_nlp.contracts import ExtractionRequest, ExtractionResult
    from homex_nlp.engine import RulesEngine
    from training.canonical_v2.experiment import ablate

    original = RulesEngine().extract(
        ExtractionRequest(
            request_id="ablation-test", text="Mesa, dos piezas, total 6000.", currency_context="BOB"
        )
    )
    before = original.model_dump()
    result = ablate(original, field)
    ExtractionResult.model_validate(result.model_dump())
    assert original.model_dump() == before
    if field == "quantity":
        assert result.item_proposal.quantity is None
        assert any(w.code == "NO_QUANTITY" for w in result.warnings)


def test_080_meters_does_not_trigger_literal_80_meter_quarantine(tmp_path):
    from training.canonical_v2.private_ingest import ingest

    source = tmp_path / "PROFORMAS.txt"
    source.write_text(
        "ESCRITORIO\nTamaño: 0,80mts de ancho.\n\nESCRITORIO\nTamaño: 80mts de alto.\n"
    )
    output = tmp_path / "private"
    ingest([source], output)
    issues = read(output / "document_quarantine.jsonl")
    assert len(issues) == 1
    assert "Tamaño: 80mts de alto." in issues[0]["text"]


@pytest.mark.parametrize(
    "mutation,code",
    [
        ("orphan", "ORPHAN_COMPONENT_GROUP"),
        ("dimension", "DIMENSION_NON_POSITIVE"),
        ("unit", "DIMENSION_AXIS_OR_UNIT"),
        ("ner_semantic", "NER_EXPECTED_NUMBER_CONFLICT"),
        ("relation", "FACT_EXPECTED_VALUE_CONFLICT"),
        ("fraction", "FRACTIONAL_PIECE_QUANTITY"),
    ],
)
def test_semantic_and_parent_mutations(corpus, mutation, code):
    rows, refs = deepcopy(corpus)
    ref = next(r for r in refs if r["id"] == "RC2-recepcion-cableado")
    tech = ref["especificacion"]["datos_tecnicos"]
    if mutation == "orphan":
        tech["componentes"][0]["conjunto_uid"] = "absent"
    elif mutation == "dimension":
        tech["caracteristicas_generales"]["dimensiones"]["largo"]["valor"] = "-1"
    elif mutation == "unit":
        tech["caracteristicas_generales"]["dimensiones"]["largo"]["unidad"] = "kg"
    elif mutation == "ner_semantic":
        ref["comercial"]["cantidad"] = "999"
    elif mutation == "fraction":
        ref["comercial"]["cantidad"] = "1.5"
    elif mutation == "relation":
        ref["facts"][0]["value"] = "false-value"
    report = validate(rows, refs)
    assert code in {e["code"] for e in report["errors"]}


def test_secret_scanner_exemptions_are_exact_public_artifact_digests():
    import re
    import subprocess

    fingerprints = [
        line
        for line in (ROOT / ".gitleaksignore").read_text().splitlines()
        if ":docs/canonical_v2/RESULTS.json:" in line
    ]
    assert len(fingerprints) == 20
    for entry in fingerprints:
        commit, path, rule, line = entry.split(":")
        assert re.fullmatch("[0-9a-f]{40}", commit)
        assert rule == "generic-api-key"
        content = subprocess.check_output(["git", "show", commit + ":" + path], cwd=ROOT, text=True)
        source_line = content.splitlines()[int(line) - 1]
        assert re.fullmatch(r'\s*"(?:tokenizer|vocab/key2row)": "[0-9a-f]{64}",?\s*', source_line)
