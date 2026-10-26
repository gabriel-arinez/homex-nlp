"""Synthetic/stub-only experiment tests; no training or weight loading in CI."""

import copy
import json

import pytest

from training.benchmark_campo.pipeline import canonical, digest
from training.offline_rc2_v13.protocol import (
    BASE,
    ROOT,
    V13,
    WHEEL,
    check_files,
    check_runtime,
    config,
    disjoint,
    load_split,
    require_manual,
)
from training.offline_rc2_v13.scoring import (
    compare_fields,
    component_scope,
    measurement,
    numeric,
    summarize,
)
from training.offline_rc2_v13.worker import evidence, reconcile


def v13_info():
    return {
        "commit": V13,
        "wheel_sha256": WHEEL,
        "package_version": "0.1.12",
        "rules_version": "prf04-rules-v13",
    }


def result(quantity=1, price=None):
    return {
        "schema_version": "1.0",
        "request_id": "SYN-1",
        "text_original": "mesa",
        "status": "REQUIRES_REVIEW",
        "proposed_item_count": 1,
        "item_proposal": {
            "name": "mesa",
            "quantity": quantity,
            "components": [],
            "dimensions": [],
            "thicknesses": [],
            "accessories": [],
            "price": price,
            "unresolved": [],
        },
        "candidates": [
            {
                "candidate_id": "r1",
                "label": "PRODUCTO",
                "start": 0,
                "end": 4,
                "text": "mesa",
                "source": "RULE",
                "normalized_value": None,
                "component_ref": None,
                "decision": "ACCEPTED",
                "reason": None,
            }
        ],
        "warnings": [],
        "engine": {
            "mode": "RULES_ONLY",
            "rules_version": "prf04-rules-v13",
            "normalization_version": "1.0",
            "model_version": None,
        },
        "error": None,
    }


def test_rc2_exact_membership_disjoint_groups_and_no_archive():
    train, dev = load_split("train"), load_split("dev")
    disjoint(train, dev)
    assert len(train) == 39 and len(dev) == 27
    assert sum(r["category"] == "muebles_pedido" for r in train) == 22
    assert sum(r["category"] == "muebles_pedido" for r in dev) == 16
    assert len({r["leakage_group"] for r in train + dev}) == 46
    assert all(r["human_gold"] is False for r in train + dev)
    with pytest.raises(ValueError):
        load_split("archive_v1")
    check_files()


@pytest.mark.parametrize(
    "key",
    ["id", "source_case_id", "paraphrase_group_id", "template_id", "leakage_group", "text_sha256"],
)
def test_split_leak_mutations(key):
    a = {
        k: "train-" + k
        for k in (
            "id",
            "source_case_id",
            "paraphrase_group_id",
            "template_id",
            "leakage_group",
            "text_sha256",
        )
    }
    b = {k: "dev-" + k for k in a}
    b[key] = a[key]
    with pytest.raises(ValueError):
        disjoint([a], [b])


@pytest.mark.parametrize(
    "field,bad",
    [
        ("commit", BASE),
        ("wheel_sha256", "0" * 64),
        ("package_version", "0.1.11"),
        ("rules_version", "prf04-rules-v12"),
    ],
)
def test_authentic_v13_metadata_guard(field, bad):
    info = v13_info()
    info[field] = bad
    with pytest.raises(ValueError):
        check_runtime(info)
    check_runtime(v13_info())


@pytest.mark.parametrize("name", ["CI", "HOMEX_DATA_GATE_NO_TRAINING"])
def test_training_always_rejected_by_ci(name, monkeypatch, tmp_path):
    from training.offline_rc2_v13.train import train

    monkeypatch.setenv(name, "1")
    with pytest.raises(RuntimeError):
        train(tmp_path / "not-read.whl", tmp_path / "not-created", True)
    assert not (tmp_path / "not-created").exists()


def test_explicit_training_flag_required(monkeypatch):
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.delenv("HOMEX_DATA_GATE_NO_TRAINING", raising=False)
    with pytest.raises(RuntimeError):
        require_manual(False)


def test_stub_training_only_receives_examples_not_dev():
    from training.offline_rc2_v13.train import fit

    class Stub:
        def __init__(self):
            self.seen = []

        def initialize(self, callback):
            assert callback() == ["TRAIN-1", "TRAIN-2"]
            return "optimizer"

        def update(self, batch, **kwargs):
            self.seen.extend(batch)
            kwargs["losses"]["ner"] = 1.0

    a, b = Stub(), Stub()
    one = fit(a, ["TRAIN-1", "TRAIN-2"], 2, lambda rows: [rows])
    two = fit(b, ["TRAIN-1", "TRAIN-2"], 2, lambda rows: [rows])
    assert one == two and a.seen == b.seen
    assert len(a.seen) == 4 and not any("DEV" in x for x in a.seen)


def test_c_never_resurrects_baseline_rejection():
    a = result()
    a.update(item_proposal=None, status="NO_PROPOSAL", proposed_item_count=0)
    a["warnings"] = [
        {
            "code": "MULTIPLE_MAIN_PRODUCTS",
            "path": "",
            "severity": "REVIEW",
            "message": "Synthetic negative",
        }
    ]
    c, _ = reconcile(a, result(), "model-stub")
    assert c["item_proposal"] is None
    assert c["engine"]["model_version"] == "model-stub"
    assert len(c["candidates"]) == 2 and c["candidates"][-1]["decision"] == "REJECTED"


def test_c_quantity_conflict_clears_derived_price_and_preserves_input():
    a = result(
        1,
        {
            "mode": "PRECIO_UNITARIO",
            "stated_amount": "10.00",
            "unit_price_input": "10.00",
            "line_total": "10.00",
            "currency": "BOB",
        },
    )
    original = copy.deepcopy(a)
    c, conflicts = reconcile(a, result(2), "stub-model")
    assert a == original and c["item_proposal"]["quantity"] is None
    assert c["item_proposal"]["price"] is None and "QUANTITY_DISAGREEMENT" in conflicts
    assert any(w["code"] == "NO_QUANTITY" for w in c["warnings"])


@pytest.mark.parametrize(
    "field,value", [("mode", "TOTAL_NEGOCIADO"), ("currency", "USD"), ("stated_amount", "11.00")]
)
def test_price_currency_conflicts_cannot_convert_or_merge(field, value):
    a = result(price={"mode": "PRECIO_UNITARIO", "currency": "BOB", "stated_amount": "10.00"})
    b = copy.deepcopy(a)
    b["item_proposal"]["price"][field] = value
    c, conflicts = reconcile(a, b, "model-stub")
    assert c["item_proposal"]["price"] is None and "PRICE_DISAGREEMENT" in conflicts


def test_c_does_not_fill_rules_abstention_from_ner():
    a = result(quantity=None)
    c, _ = reconcile(
        a,
        result(5, {"currency": "BOB", "mode": "TOTAL_NEGOCIADO", "stated_amount": "10.00"}),
        "stub-model",
    )
    assert c["item_proposal"]["quantity"] is None and c["item_proposal"]["price"] is None


def test_c_actual_contract_with_stub_candidates():
    from homex_nlp.contracts import ExtractionResult

    a = result()
    c, _ = reconcile(a, result(), "stub-model")
    assert ExtractionResult.model_validate(c).schema_version == "1.0"
    b = result()
    b["item_proposal"]["name"] = "silla"
    c, _ = reconcile(a, b, "stub-model")
    assert ExtractionResult.model_validate(c).status == "NO_PROPOSAL"


def test_exact_decimal_axis_units_component_and_missing_reference():
    assert numeric("2,00") == numeric("2.000")
    assert measurement("18 mm") == ("18", "mm")
    assert measurement("1 m") != measurement("100 cm")
    with pytest.raises(ValueError):
        numeric("3.650,00")
    a, b = component_scope("Tablero"), component_scope("Mesón")
    assert a != b
    cs = compare_fields({(a, "espesor"): ("18", "mm")}, {(b, "espesor"): ("18", "mm")}, set())
    assert cs["espesor"]["omission"] == 1 and cs["espesor"]["false_assertion"] == 1
    negative = compare_fields({}, {}, {("ITEM", "sold_quantity")})
    assert negative["sold_quantity"]["safe_abstention"] == 1
    assert negative["sold_quantity"]["correct"] == 0


def stub_report():
    rows = [
        {
            "id": "SYN-1",
            "text_sha256": "0" * 64,
            "category": "muebles_pedido",
            "entities": [(0, 4, "PRODUCTO")],
            "leakage_group": "SYN-GROUP",
        }
    ]
    ref = {
        "SYN-1": {
            "comercial": {
                "nombre": "mesa",
                "cantidad": "1",
                "unidad_codigo": None,
                "precio_unitario": None,
                "precio_total_explicito": None,
            },
            "especificacion": {},
            "status": "REQUIRES_REVIEW",
        }
    }
    predictions = {
        "protocol_digest": digest(config()),
        "v13": v13_info(),
        "rows": [
            {
                "id": "SYN-1",
                "text_sha256": "0" * 64,
                "results": {e: result() for e in "ABC"},
                "ner": {e: [(0, 4, "PRODUCTO")] for e in "ABC"},
                "errors": {},
                "hybrid_conflicts": [],
                "currency_context": "BOB",
            }
        ],
    }
    return rows, ref, predictions


def test_fixed_aggregate_determinism_and_honest_flags():
    rows, refs, p = stub_report()
    one = summarize(rows, refs, p)
    assert canonical(one) == canonical(summarize(rows, refs, copy.deepcopy(p)))
    assert one["HUMAN_GOLD"] == "NO" and one["TEST_VOZ_REAL"] == "NO" and one["PROMOCION"] == "NO"
    assert one["engines"]["B"]["muebles_pedido"]["ner"]["micro"]["f1"] == 1
    assert one["engines"]["A"]["sillas"]["ner"]["micro"] is None
    public = canonical(one)
    assert "SYN-1" not in public and "mesa" not in public and str(ROOT) not in public


def test_prediction_wrong_engine_or_text_cannot_be_scored():
    rows, refs, p = stub_report()
    p["v13"]["rules_version"] = "prf04-rules-v12"
    with pytest.raises(ValueError):
        summarize(rows, refs, p)
    rows, refs, p = stub_report()
    p["rows"][0]["text_sha256"] = "1" * 64
    with pytest.raises(ValueError):
        summarize(rows, refs, p)


def test_c_missing_dependency_reported_not_evaluable():
    rows, refs, p = stub_report()
    p["rows"][0]["results"]["C"] = None
    p["rows"][0]["errors"]["C"] = "NOT_EVALUABLE_B_DEPENDENCY"
    report = summarize(rows, refs, p)["engines"]["C"]["muebles_pedido"]
    assert report["commercial"]["status"] == "NOT_EVALUABLE"
    assert report["ner"]["micro"] is None


def test_b_raw_negatives_do_not_hide_false_positive_entities():
    r = result()
    r["candidates"][0]["decision"] = "UNRESOLVED"
    assert evidence(r, ["PRODUCTO"], raw=True)[0] == [(0, 4, "PRODUCTO")]
    assert evidence(r, ["PRODUCTO"], raw=False)[0] == []


def test_training_requires_successful_preflight_before_model_loading(monkeypatch, tmp_path):
    from training.offline_rc2_v13.train import train

    monkeypatch.delenv("CI", raising=False)
    monkeypatch.delenv("HOMEX_DATA_GATE_NO_TRAINING", raising=False)
    monkeypatch.setenv("OMP_NUM_THREADS", "1")
    monkeypatch.setenv("OPENBLAS_NUM_THREADS", "1")
    with pytest.raises(ValueError, match="VERIFIED_PREFLIGHT_REQUIRED"):
        train(tmp_path / "not-read.whl", tmp_path / "not-created", True)


def test_loss_history_has_json_native_floats():
    import numpy as np

    from training.offline_rc2_v13.train import fit

    class Stub:
        def initialize(self, callback):
            return None

        def update(self, batch, **kwargs):
            kwargs["losses"]["ner"] = np.float32(1.25)

    history = fit(Stub(), ["TRAIN-ONLY"], 1, lambda x: [x])
    assert json.loads(json.dumps(history))[0]["losses"]["ner"] == 1.25


def test_scope_new_branch_and_exact_allowlist_no_production(monkeypatch):
    from tools import ci_corpus_scope

    responses = iter([BASE + "\n", "training/offline_rc2_v13/train.py\n"])
    monkeypatch.setattr(
        ci_corpus_scope.subprocess, "check_output", lambda *a, **kw: next(responses)
    )
    assert ci_corpus_scope.corpus_only(ci_corpus_scope.changed_paths({"before": "0" * 40}))
    assert not ci_corpus_scope.corpus_only(
        ["training/offline_rc2_v13/train.py", "src/homex_nlp/rules.py"]
    )
    assert not ci_corpus_scope.corpus_only(["training/offline_rc2_v13/model.bin"])
    assert not ci_corpus_scope.corpus_only(["training/offline_rc2_v13/private.json"])


def test_real_worker_forbidden_in_ci_before_loading(monkeypatch, tmp_path):
    from training.offline_rc2_v13.worker import evaluate

    monkeypatch.setenv("CI", "true")
    with pytest.raises(RuntimeError):
        evaluate(tmp_path / "missing", tmp_path / "missing", tmp_path / "out")


def test_wheel_hash_checked_before_any_import(tmp_path):
    from training.offline_rc2_v13.protocol import runtime

    wheel = tmp_path / "fake.whl"
    wheel.write_bytes(b"SYNTHETIC_TEST_NOT_A_WHEEL")
    with pytest.raises(ValueError, match="APPROVED_V13_WHEEL"):
        runtime(wheel)


def test_private_weights_cannot_be_written_inside_git(monkeypatch):
    from training.offline_rc2_v13.train import train

    monkeypatch.delenv("CI", raising=False)
    monkeypatch.delenv("HOMEX_DATA_GATE_NO_TRAINING", raising=False)
    monkeypatch.setenv("OMP_NUM_THREADS", "1")
    monkeypatch.setenv("OPENBLAS_NUM_THREADS", "1")
    with pytest.raises(ValueError, match="PRIVATE_PATH"):
        train(ROOT / "unused.whl", ROOT / "model-should-not-exist", True)
    assert not (ROOT / "model-should-not-exist").exists()


def test_changed_or_symlinked_dataset_rejected(monkeypatch, tmp_path):
    from training.offline_rc2_v13 import protocol

    p = tmp_path / "data.txt"
    p.write_text("synthetic-changed")
    monkeypatch.setattr(protocol, "ROOT", tmp_path)
    monkeypatch.setattr(protocol, "config", lambda: {"protected_files": {"data.txt": "0" * 64}})
    with pytest.raises(ValueError):
        protocol.check_files()


def test_label_denominators_and_private_differences_separate():
    from training.offline_rc2_v13.scoring import private_differences

    rows, refs, p = stub_report()
    rows[0]["text"] = "mesa"
    report = summarize(rows, refs, p)
    metric = report["engines"]["B"]["muebles_pedido"]["ner"]["by_label"]["PRODUCTO"]
    assert metric["reference_entities"] == metric["tp"] + metric["fn"] == 1
    assert metric["reference_groups"] == 1 and metric["reference_documents"] == 1
    assert private_differences(rows, refs, p)[0]["text"] == "mesa"
    assert '"text"' not in canonical(report)


def test_cli_private_detail_explicit_and_public_aggregate_redacted(tmp_path, monkeypatch):
    import sys

    from training.offline_rc2_v13 import cli

    rows, refs, p = stub_report()
    rows[0]["text"] = "mesa"
    source = tmp_path / "predictions.json"
    source.write_text(json.dumps(p))
    tmp_path.chmod(0o700)
    monkeypatch.setattr(cli, "load_split", lambda split: rows)
    monkeypatch.setattr(cli, "references", lambda split: refs)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "cli",
            "summarize",
            "--predictions",
            str(source),
            "--output",
            str(tmp_path / "public.json"),
            "--private-detail",
            str(tmp_path / "private.json"),
        ],
    )
    cli.main()
    assert '"text"' not in (tmp_path / "public.json").read_text()
    assert json.loads((tmp_path / "private.json").read_text())[0]["text"] == "mesa"
    assert (tmp_path / "private.json").stat().st_mode & 0o777 == 0o600


def test_comparison_requires_two_runs():
    from training.offline_rc2_v13.scoring import comparison

    with pytest.raises(ValueError, match="TWO_INDEPENDENT"):
        comparison([], None)


def test_multiple_product_false_proposal_has_explicit_denominator():
    rows, refs, p = stub_report()
    rows[0]["phenomena"] = ["multiproducto"]
    refs["SYN-1"]["comercial"]["nombre"] = None
    refs["SYN-1"]["status"] = "NO_PROPOSAL"
    c = summarize(rows, refs, p)["engines"]["B"]["muebles_pedido"]["commercial"]
    assert c["multiple_product_negatives"] == 1 and c["multiple_product_false_proposals"] == 1


def test_same_view_accepted_excludes_unresolved_b_entities():
    rows, refs, predictions = stub_report()
    predictions["rows"][0]["results"]["B"]["candidates"][0]["decision"] = "UNRESOLVED"
    # Historical cached B ner spans remain raw. Comparable views must be derived
    # from the sealed DTO through the real evidence adapter, not from this cache.
    accepted = summarize(rows, refs, predictions, ner_view="accepted")
    raw = summarize(rows, refs, predictions, ner_view="all_candidates")
    assert accepted["engines"]["A"]["muebles_pedido"]["ner"]["micro"]["tp"] == 1
    assert accepted["engines"]["B"]["muebles_pedido"]["ner"]["micro"]["fn"] == 1
    assert raw["engines"]["B"]["muebles_pedido"]["ner"]["micro"]["tp"] == 1


def comparison_fixture(tmp_path, monkeypatch):
    from training.offline_rc2_v13 import protocol

    rows, refs, p = stub_report()
    p["model_files_digest"] = "SYNTHETIC_MODEL_TREE"
    monkeypatch.setattr(protocol, "load_split", lambda split: rows)
    monkeypatch.setattr(protocol, "references", lambda split: refs)
    plan = tmp_path / "preflight.json"
    plan.write_text(json.dumps({"protocol_digest": digest(config()), "machine": {}}))
    perf = {
        "load_seconds": {},
        "process_peak_rss_kib": 1,
        "model_bytes": 1,
        "method": "SYNTHETIC_STUB",
        "latencies": [
            {"id": "SYN-1", "phase": "first_dev_call", "milliseconds": dict.fromkeys("ABC", 1)}
        ],
    }
    dirs = [tmp_path / "eval-1", tmp_path / "eval-2"]
    for d in dirs:
        d.mkdir()
        (d / "predictions.json").write_text(json.dumps(p))
        (d / "performance.json").write_text(json.dumps(perf))
    return dirs, plan


@pytest.mark.parametrize("alias", ["same", "symlink", "dotdot"])
def test_duplicate_evaluation_directory_rejected(tmp_path, monkeypatch, alias):
    from training.offline_rc2_v13.scoring import comparison

    dirs, plan = comparison_fixture(tmp_path, monkeypatch)
    if alias == "symlink":
        second = tmp_path / "alias"
        second.symlink_to(dirs[0], target_is_directory=True)
    elif alias == "dotdot":
        second = dirs[1] / ".." / "eval-1"
    else:
        second = dirs[0]
    with pytest.raises(ValueError, match="DUPLICATE_EVALUATION_DIRECTORY"):
        comparison([dirs[0], second], plan)


def test_copied_evaluation_is_not_verified_independence(tmp_path, monkeypatch):
    from training.offline_rc2_v13.scoring import comparison

    dirs, plan = comparison_fixture(tmp_path, monkeypatch)
    rep = comparison(dirs, plan)["reproducibility"]
    assert rep["evaluations_supplied"] == 2
    assert rep["distinct_artifacts"] == 1
    assert rep["independent_runs_verified"] == 0
    assert rep["independence_status"] == "UNVERIFIED"
    assert rep["independent_evaluation_processes"] is None


def test_distinct_documented_measurements_remain_honestly_unverified(tmp_path, monkeypatch):
    from training.offline_rc2_v13.scoring import comparison

    dirs, plan = comparison_fixture(tmp_path, monkeypatch)
    # A different elapsed time and a self-declared run ID do not authenticate
    # separate OS processes or linkage to different fits. Historical files read.
    source = dirs[1] / "performance.json"
    perf = json.loads(source.read_text())
    perf["latencies"][0]["milliseconds"]["A"] = 2
    perf["run_id"] = "SELF_DECLARED_NOT_TRUSTED"
    source.write_text(json.dumps(perf))
    report = comparison(dirs, plan)
    rep = report["reproducibility"]
    assert rep["distinct_artifacts"] == 2 and rep["evaluations_supplied"] == 2
    assert rep["independence_status"] == "UNVERIFIED" and rep["independent_runs_verified"] == 0
    assert rep["predictions_identical"] and rep["model_files_identical"]


@pytest.mark.parametrize("field", ["protocol_digest", "model_files_digest"])
def test_comparison_rejects_protocol_or_model_mismatch(tmp_path, monkeypatch, field):
    from training.offline_rc2_v13.scoring import comparison

    dirs, plan = comparison_fixture(tmp_path, monkeypatch)
    source = dirs[1] / "predictions.json"
    p = json.loads(source.read_text())
    p[field] = "CHANGED"
    source.write_text(json.dumps(p))
    with pytest.raises(ValueError):
        comparison(dirs, plan)


def test_post_hoc_views_support_hashes_c_policy_and_determinism(tmp_path, monkeypatch):
    from training.offline_rc2_v13.scoring import supplementary_comparison

    dirs, plan = comparison_fixture(tmp_path, monkeypatch)
    one = supplementary_comparison(dirs, plan)
    assert canonical(one) == canonical(supplementary_comparison(dirs, plan))
    assert one["analysis_type"] == "SUPPLEMENTARY_POST_HOC" and not one["protocol_changed"]
    assert one["original_predictions_sha256"][0] == one["original_predictions_sha256"][1]
    assert set(one["views"]["accepted"]) == set("ABC")
    assert set(one["views"]["all_candidates"]) == set("AB")
    for view in one["views"].values():
        for families in view.values():
            m = families["muebles_pedido"]
            assert (m["documents"], m["entities"], m["groups"]) == (1, 1, 1)
            label = m["ner"]["by_label"]["PRODUCTO"]
            assert label["reference_entities"] == label["tp"] + label["fn"] == 1
            absent = m["ner"]["by_label"]["ACABADO"]
            assert absent["f1"] is None and absent["reference_entities"] == 0
    public = canonical(one)
    assert '"text"' not in public and "SYN-1" not in public and str(tmp_path) not in public


def test_unknown_view_cannot_silently_fall_back_to_legacy():
    with pytest.raises(ValueError, match="UNKNOWN_NER_VIEW"):
        summarize(*stub_report(), ner_view="accidental-mixed")


def test_cli_supplement_is_postprocessing_only(tmp_path, monkeypatch):
    import sys

    from training.offline_rc2_v13 import cli

    dirs, plan = comparison_fixture(tmp_path, monkeypatch)
    tmp_path.chmod(0o700)
    target = tmp_path / "supplement.json"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "cli",
            "supplement",
            "--evaluation-dirs",
            *map(str, dirs),
            "--preflight",
            str(plan),
            "--output",
            str(target),
        ],
    )
    cli.main()
    assert json.loads(target.read_text())["analysis_type"] == "SUPPLEMENTARY_POST_HOC"
    assert target.stat().st_mode & 0o777 == 0o600
