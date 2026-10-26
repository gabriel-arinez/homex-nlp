"""Independent rc2 mutations and training-isolation tests. No real human decisions."""

import copy
import json
from pathlib import Path

import pytest

from tools.ci_corpus_scope import corpus_only
from training.corpus_v2_rc2.grouping import normalized, pair_risks
from training.corpus_v2_rc2.no_training import check_command
from training.corpus_v2_rc2.review import import_decisions
from training.corpus_v2_rc2.validate import privacy, validate, validate_rows

CANDIDATE = Path("data/candidates/corpus_v2_rc2")
LABELS = set(json.loads(Path("data/manifests/prf04_labels.json").read_text())["labels"])


def data():
    rows = [
        r
        for p in sorted((CANDIDATE / "development_v2").rglob("*.jsonl"))
        for r in map(json.loads, p.read_text().splitlines())
    ]
    refs = {
        r["id"]: r
        for p in (CANDIDATE / "expected").rglob("*.jsonl")
        for r in map(json.loads, p.read_text().splitlines())
    }
    return rows, refs


def errors(rows, refs):
    return {e["code"] for e in validate_rows(rows, refs, LABELS)}


def test_rc2_coverage_independence_and_manifest():
    result = validate(CANDIDATE)
    assert result["valid"], result["errors"][:10]
    assert result["GATE_TRAINING"] == "EXPERIMENTAL_READY"
    assert result["HUMAN_GOLD"] == "NO"
    assert result["development_records"] == sum(
        len(p.read_text().splitlines()) for p in (CANDIDATE / "development_v2").rglob("*.jsonl")
    )


@pytest.mark.parametrize(
    "mutation,code",
    [
        ("exact", "EXACT_LEAK"),
        ("numbers", "NUMBER_TEMPLATE_LEAK"),
        ("case", "CASE_LEAK"),
        ("paraphrase", "CASE_LEAK"),
        ("template", "CASE_LEAK"),
        ("gold", "FALSE_GOLD"),
        ("offset", "SPAN_BOUNDS"),
        ("evidence", "FACT_EVIDENCE"),
        ("total", "ARITHMETIC"),
        ("capacity_quantity", "COMMERCIAL_VS_INTERNAL_CAPACITY"),
        ("missing_family", "FAMILY_COVERAGE"),
        ("missing_label", "LABEL_SCENARIO_COVERAGE"),
    ],
)
def test_mutation_guards(mutation, code):
    rows, refs = data()
    row = next(r for r in rows if r["id"] == "RC2-recepcion-cableado")
    dev = next(r for r in rows if r["id"] == "RC2-laboratorio-rincon")
    if mutation in {"exact", "numbers"}:
        extra = copy.deepcopy(row)
        extra["id"] = "MUTATION-ONLY"
        extra["split"] = "dev"
        extra["collection"] = "development_dev"
        extra["source_case_id"] = "fixture-extra"
        extra["leakage_group"] = "fixture-extra"
        extra["paraphrase_group_id"] = "fixture-extra"
        extra["template_id"] = "fixture-extra"
        ref = copy.deepcopy(refs[row["id"]])
        ref["id"] = extra["id"]
        if mutation == "numbers":
            extra["text"] = extra["text"].replace("2380", "2470")
        rows.append(extra)
        refs[extra["id"]] = ref
    elif mutation in {"case", "paraphrase", "template"}:
        key = {
            "case": "source_case_id",
            "paraphrase": "paraphrase_group_id",
            "template": "template_id",
        }[mutation]
        dev[key] = row[key]
    elif mutation == "gold":
        row["human_gold"] = True
    elif mutation == "offset":
        row["entities"][0][1] = 99999
    elif mutation == "evidence":
        refs[row["id"]]["facts"][0]["evidence"]["start"] += 1
    elif mutation == "total":
        refs[row["id"]]["comercial"]["precio_total_explicito"] = "1"
    elif mutation == "capacity_quantity":
        ref = refs[row["id"]]
        f = next(f for f in ref["facts"] if f["path"] == "comercial.cantidad")
        loc = row["text"].index("25 mm")
        f["value"] = "25"
        ref["comercial"]["cantidad"] = "25"
        f["evidence"] = {"start": loc, "end": loc + 2, "text": "25"}
    elif mutation == "missing_family":
        rows = [r for r in rows if not (r["split"] == "train" and r["category"] == "sillas")]
        refs = {r["id"]: refs[r["id"]] for r in rows}
    elif mutation == "missing_label":
        for r in rows:
            if r["split"] == "dev":
                r["entities"] = [e for e in r["entities"] if e[2] != "CABECERA"]
    assert code in errors(rows, refs)


def test_generic_family_does_not_define_case_identity():
    rows, refs = data()
    a = next(r for r in rows if r["id"] == "RC2-recepcion-cableado")
    b = next(r for r in rows if r["id"] == "RC2-laboratorio-rincon")
    assert a["category"] == b["category"]
    assert not any(r["severity"] == "HIGH" for r in pair_risks([a, b], refs))
    assert normalized("Mesa 2,40 metros 18 mm") == normalized("mesa 9,20 metros 27 mm")
    assert normalized("DIÁMETRO 80 centímetros") == normalized("diametro 92 cm")


@pytest.mark.parametrize(
    "text",
    [
        "cliente_nombre: Persona de prueba",
        "celular: 77777777",
        "/home/fixture/private.wav",
        "x@example.invalid",
    ],
)
def test_privacy_patterns(text):
    assert privacy(text)


def human_fixture():
    # Deliberately fictional test identities; never imported into candidate data.
    kit = [{"review_id": "test-field", "record_id": "test-record", "text_sha256": "a" * 64}]
    votes = [
        {
            "review_id": "test-field",
            "text_sha256": "a" * 64,
            "reviewer": "FIXTURE_ONLY_A",
            "attestation_id": "TEST-A",
            "reviewed_at": "2026-10-25T12:00:00-04:00",
            "decision": "ACCEPT",
            "comment": "Synthetic unit-test decision, not a real human review.",
        }
    ]
    registry = [{"reviewer": "FIXTURE_ONLY_A", "attestation_id": "TEST-A", "authorized": True}]
    from training.corpus_v2_rc2.review import field_digest

    kit[0]["field_sha256"] = field_digest(kit[0])
    votes[0]["field_sha256"] = kit[0]["field_sha256"]
    return kit, votes, registry


def test_no_gold_from_one_person_or_missing_authorization():
    kit, votes, registry = human_fixture()
    with pytest.raises(ValueError):
        import_decisions(kit, votes, [])
    result = import_decisions(kit, votes, registry)
    assert not result["human_gold"]
    assert result["fields"][0]["status"] == "HUMAN_REVIEWED"
    assert result["dataset_modified"] is False
    votes.append(votes[0].copy())
    with pytest.raises(ValueError):
        import_decisions(kit, votes, registry)


def test_stale_missing_and_disputed_reviews_stay_out_of_gold():
    kit, votes, registry = human_fixture()
    stale = copy.deepcopy(votes)
    stale[0]["text_sha256"] = "b" * 64
    with pytest.raises(ValueError):
        import_decisions(kit, stale, registry)
    assert not import_decisions(kit, [], registry)["human_gold"]
    votes[0]["decision"] = "DISPUTE"
    assert import_decisions(kit, votes, registry)["fields"][0]["status"] == "DISPUTED"


def test_two_real_external_decisions_protocol_is_supported_without_claiming_them():
    kit, votes, registry = human_fixture()
    second = votes[0] | {"reviewer": "FIXTURE_ONLY_B", "attestation_id": "TEST-B"}
    result = import_decisions(
        kit,
        votes + [second],
        registry + [{"reviewer": "FIXTURE_ONLY_B", "attestation_id": "TEST-B", "authorized": True}],
    )
    assert result["records"][0]["status"] == "GOLD_ELIGIBLE"
    assert result["external_identity_verification_required"] is True
    progress = json.loads((CANDIDATE / "review/progress.json").read_text())
    assert progress["human_reviewed"] == 0 and progress["human_gold"] == "NO"


def test_corpus_only_guard_preserves_mixed_and_production_ci():
    assert corpus_only(
        [
            "training/corpus_v2_rc2/build.py",
            "data/candidates/corpus_v2_rc2/manifest.json",
            ".github/workflows/ci.yml",
        ]
    )
    assert not corpus_only(["training/corpus_v2_rc2/build.py", "src/homex_nlp/rules.py"])
    assert not corpus_only(["src/homex_nlp/contracts/models.py"])
    assert not corpus_only([])
    assert not corpus_only([".github/workflows/other-security.yml"])
    workflow = Path(".github/workflows/ci.yml").read_text()
    assert workflow.count("if: needs.scope.outputs.corpus_only != 'true'") == 2
    assert "training.train_prf04 --epochs 10" in workflow
    assert "  secrets:" in workflow and "  dependency-audit:" in workflow


@pytest.mark.parametrize(
    "command",
    [
        ["python", "-m", "training.train_prf04"],
        ["python", "-m", "spacy", "train", "x.cfg"],
        ["python", "training/train_prf04.py"],
    ],
)
def test_data_gate_rejects_training_command(command):
    with pytest.raises(RuntimeError):
        check_command(command)


def test_ci_gate_command_allowlist_and_no_weights_api(monkeypatch):
    from training.corpus_v2_rc2.ci_gate import commands

    for command in commands(Path("/tmp/fixture-data-gate")):
        check_command(command)
    # Patch is scoped to this test to preserve existing test behavior afterwards.
    import importlib

    import spacy

    from training.corpus_v2_rc2.no_training import install

    train_module = importlib.import_module("spacy.cli.train")
    originals = (
        spacy.load,
        spacy.language.Language.initialize,
        spacy.language.Language.update,
        spacy.cli.train,
        train_module.train,
    )
    try:
        install()
        with pytest.raises(RuntimeError):
            spacy.load("FIXTURE_NO_SUCH_MODEL")
        with pytest.raises(RuntimeError):
            spacy.blank("es").initialize()
        with pytest.raises(RuntimeError):
            train_module.train("FIXTURE_NO_FILE")
    finally:
        (
            spacy.load,
            spacy.language.Language.initialize,
            spacy.language.Language.update,
            spacy.cli.train,
            train_module.train,
        ) = originals


def test_high_risks_without_adjudication_block_training():
    from training.corpus_v2_rc2.validate import check_risks

    assert check_risks(
        [{"severity": "HIGH", "decision": "PENDING", "a": "fixture-a", "b": "fixture-b"}]
    )
    assert check_risks(
        [{"severity": "HIGH", "decision": "SAME_CASE_GROUP", "cross_partition": True}]
    )
    assert not check_risks([{"severity": "LOW", "decision": "GENERIC_LANGUAGE_FALSE_POSITIVE"}])


def test_protected_source_mutation_is_detected(tmp_path):
    import hashlib

    from training.corpus_v2_rc2.validate import check_protected

    source = tmp_path / "source.jsonl"
    source.write_text("immutable fixture\n")
    baseline = {"source.jsonl": hashlib.sha256(source.read_bytes()).hexdigest()}
    assert not check_protected(baseline, tmp_path)
    source.write_text("corrupted fixture\n")
    assert check_protected(baseline, tmp_path)[0]["code"] == "PROTECTED_CHANGED"


def test_reworded_equivalent_claims_cannot_cross_partitions():
    rows, refs = data()
    source = next(r for r in rows if r["id"] == "RC2-recepcion-cableado")
    extra = copy.deepcopy(source)
    extra.update(
        id="FIXTURE-PARAPHRASE",
        split="dev",
        collection="development_dev",
        text="Bueno, " + source["text"],
    )
    for key in ("source_case_id", "paraphrase_group_id", "template_id", "leakage_group"):
        extra[key] = "fixture-unrelated-claim"
    ref = copy.deepcopy(refs[source["id"]])
    ref["id"] = extra["id"]
    refs[extra["id"]] = ref
    rows.append(extra)
    assert "SEMANTIC_CLAIMS_LEAK" in errors(rows, refs)


def test_new_branch_range_is_not_assumed_safe(monkeypatch):
    from tools import ci_corpus_scope

    monkeypatch.setattr(
        ci_corpus_scope.subprocess, "check_output", lambda *a, **kw: "unverified-parent\n"
    )
    paths = ci_corpus_scope.changed_paths({"before": "0" * 40})
    assert not ci_corpus_scope.corpus_only(paths)


def test_human_decision_binds_reference_value_not_only_text():
    kit, votes, registry = human_fixture()
    kit[0]["after"] = "changed reference with same source text"
    with pytest.raises(ValueError):
        import_decisions(kit, votes, registry)
