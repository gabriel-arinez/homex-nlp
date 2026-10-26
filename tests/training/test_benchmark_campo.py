"""All fixtures and mutations in this module are artificial, never field evidence."""

import copy
import json

import pytest
from pydantic import ValidationError

from tools.ci_corpus_scope import changed_paths, corpus_only
from training.benchmark_campo.cli import main
from training.benchmark_campo.metrics import (
    alignment,
    commercial_counts,
    ner_counts,
    ner_report,
    productivity,
    stats,
)
from training.benchmark_campo.models import Batch, Commercial, Span
from training.benchmark_campo.pipeline import (
    ROOT,
    baseline_rows,
    canonical,
    leakage,
    load,
    review_kit,
    score,
    verified,
    write_private,
)
from training.evaluar_campo_prf04 import distancia, palabras

FIXTURE = ROOT / "tests/fixtures/benchmark_campo/synthetic.json"


def raw():
    return json.loads(FIXTURE.read_text())


def batch(data=None):
    return Batch.model_validate_json(json.dumps(raw() if data is None else data))


def synthetic_real_mutation():
    # Unpublished transport mutation to exercise declaration gates; not a real recording.
    d = raw()
    s = d["sessions"][0]
    s.update(source_type="ASR_REAL", capture_mode="imported_asr")
    s["consent"] = {
        "human_declared": True,
        "act_id": "SYN-ACT",
        "use_policy_id": "SYN-USE",
        "retention_policy_id": "SYN-RETENTION",
    }
    s["reference"]["origin"] = "independent_human"
    return d


@pytest.mark.parametrize(
    "r,h,wanted",
    [
        ("a b", "a c", (1, 0, 0, 2)),
        ("a b", "a", (0, 1, 0, 2)),
        ("a", "a b", (0, 0, 1, 1)),
        ("", "a b", (0, 0, 2, 0)),
        ("", "", (0, 0, 0, 0)),
        ("ÁRBOL dos 1,20", "árbol dos 1.20", (0, 0, 0, 4)),
        ("two chairs", "two chair", (1, 0, 0, 2)),
        ("dos", "2", (1, 0, 0, 1)),
    ],
)
def test_wer_independent_expected_counts(r, h, wanted):
    result = alignment(r, h)
    assert tuple(result[k] for k in ("S", "D", "I", "N")) == wanted
    assert result["wer"] == (sum(wanted[:3]) / wanted[3] if wanted[3] else None)
    assert sum(result[k] for k in ("S", "D", "I")) == distancia(palabras(r), palabras(h))


def test_ner_negative_and_independent_formula():
    a = Span(start=0, end=2, label="PRODUCTO")
    b = Span(start=3, end=5, label="COLOR")
    c = ner_counts([a], [a, b])
    r = ner_report(c, 1)
    assert r["micro"] == {"tp": 1, "fp": 1, "fn": 0, "precision": 0.5, "recall": 1, "f1": 2 / 3}
    assert r["macro_f1"] == 0.5
    assert ner_report(ner_counts([], [b]), 1)["micro"]["fp"] == 1
    assert ner_report({}, 0)["micro"] is None
    assert ner_report({}, 1)["micro"]["f1"] is None


def test_real_without_registry_never_scores_reference():
    r = score(batch(synthetic_real_mutation()))["groups"]["ASR_REAL"]
    assert r["wer_micro"]["wer"] is None
    assert r["excluded_unverified_consent"] == 1
    assert all(v["status"] == "NOT_EVALUABLE" for v in r["ner"].values())


def test_no_gold_partial_and_coordinate_are_not_evaluable():
    d = raw()
    del d["sessions"][0]["reference"]
    r = score(batch(d))
    assert r["groups"]["SINTETICO_PRUEBA"]["wer_micro"]["wer"] is None
    assert r["groups"]["ASR_REAL"]["status"] == "NO_DISPONIBLE"
    d = raw()
    d["sessions"][0]["reference"]["ner"]["coverage"] = "partial"
    assert (
        next(iter(score(batch(d))["groups"]["SINTETICO_PRUEBA"]["ner"].values()))["status"]
        == "NOT_EVALUABLE"
    )
    d = raw()
    s = d["sessions"][0]
    s["reference"]["ner"].update(
        coordinate="faithful", text_sha256=s["reference"]["faithful"]["sha256"]
    )
    assert (
        next(iter(score(batch(d))["groups"]["SINTETICO_PRUEBA"]["ner"].values()))["status"]
        == "NOT_EVALUABLE"
    )


@pytest.mark.parametrize(
    "mutation",
    [
        lambda s: s.update(extra="forbidden"),
        lambda s: s["asr"].update(sha256="0" * 64),
        lambda s: s["reference"]["ner"]["spans"][0].update(end=999),
        lambda s: s["reference"]["ner"]["spans"][1].update(start=5),
        lambda s: s["reference"].update(origin="model_prediction"),
        lambda s: s["engines"][0].update(text_sha256="0" * 64),
        lambda s: s["engines"][0]["commercial"]["facts"][0].update(scope="ABSENT"),
        lambda s: s["engines"][0]["commercial"]["facts"][4].update(evidence="inferred"),
        lambda s: s["engines"][0]["commercial"]["facts"][4].update(value="NaN"),
        lambda s: s["engines"][0]["commercial"]["facts"][4].update(value="3.650,00"),
        lambda s: s["timings"][0].update(unit="minutes"),
        lambda s: s["timings"][0].update(end=-1.0),
        lambda s: s["timings"][0].update(end=float("inf")),
        lambda s: s["timings"][0].update(end_boundary="nlp_done"),
        lambda s: s["consent"].update(human_verified=True),
        lambda s: s.update(diagnosis={"cause": "ASR"}),
        lambda s: s["productivity"].update(case_id="OTHER-CASE"),
        lambda s: s["reference"]["commercial"].update(coverage="partial"),
        lambda s: s["provenance"].update(speaker_id="name@example.com"),
        lambda s: s.update(audio={"private_ref": "/private/audio.wav", "sha256": "0" * 64}),
    ],
)
def test_strict_mutations(mutation):
    d = raw()
    mutation(d["sessions"][0])
    with pytest.raises((ValueError, ValidationError)):
        batch(d)


def test_duplicates_and_real_declaration_rejected():
    d = raw()
    d["sessions"].append(copy.deepcopy(d["sessions"][0]))
    with pytest.raises(ValidationError):
        batch(d)
    d = synthetic_real_mutation()
    d["sessions"][0]["consent"]["human_declared"] = False
    with pytest.raises(ValidationError):
        batch(d)


@pytest.mark.parametrize(
    "field,value,unit,expected",
    [
        ("sold_quantity", "10", None, "sold_quantity"),
        ("unit_price", "3650.01", None, "unit_price"),
        ("currency", "USD", None, "currency"),
        ("length", "2", None, "length"),
        ("length", "200", "cm", "length"),
        ("thickness", "27", "mm", "thickness"),
    ],
)
def test_business_mutations(field, value, unit, expected):
    g = batch().sessions[0].reference.commercial
    p = g.model_copy(deep=True)
    next(f for f in p.facts if f.field == field).value = value
    next(f for f in p.facts if f.field == field).unit = unit
    rows, e, n = commercial_counts(g, p)
    assert rows[expected]["omission"] == 1
    assert rows[expected]["false_assertion"] == 1
    assert e == 1 and n > 0


def test_decimal_relations_internal_and_missing_are_not_success():
    g = batch().sessions[0].reference.commercial
    p = g.model_copy(deep=True)
    next(f for f in p.facts if f.field == "length").value = "2.000"
    assert commercial_counts(g, p)[1] == 0
    p.facts = [f for f in p.facts if f.field != "sold_quantity"]
    assert commercial_counts(g, p)[0]["sold_quantity"]["correct"] == 0
    p = g.model_copy(deep=True)
    a, b = [f for f in p.facts if f.field == "thickness"]
    a.scope, b.scope = b.scope, a.scope
    assert commercial_counts(g, p)[1] == 2
    p = g.model_copy(deep=True)
    p.facts.append(
        p.facts[1].model_copy(
            update={"field": "internal_quantity", "scope": "TABLERO", "value": "2"}
        )
    )
    assert commercial_counts(g, p)[0]["internal_quantity"]["false_assertion"] == 1


def test_partial_negatives_and_missing_units():
    g = Commercial(
        scopes={"ITEM": "item", "CONDITIONS": "conditions"},
        facts=[],
        coverage="partial",
        reviewed_keys=["ITEM:unit_price"],
    )
    p = batch().sessions[0].reference.commercial
    rows, _, _ = commercial_counts(g, p)
    assert set(rows) == {"unit_price"} and rows["unit_price"]["false_assertion"] == 1
    assert commercial_counts(g, None)[0]["unit_price"]["safe_abstention"] == 1
    g = p.model_copy(deep=True)
    next(f for f in g.facts if f.field == "length").unit = None
    assert commercial_counts(g, g)[0]["length"]["correct"] == 0


def test_stats_pairing_exclusions_and_negative_saving():
    assert stats([1, 2, 3, 4, 100]) == {"n": 5, "p50": 3, "p95": 100, "max": 100}
    assert stats([1, 3])["p50"] == 2
    assert stats([])["p95"] is None
    p = batch().sessions[0].productivity
    p.assisted_seconds = 130
    assert productivity([p])["paired_saving_seconds"]["p50"] == -10
    p.commercial_validated = False
    assert productivity([p, None])["n"] == 0


def test_rc2_review_binding_and_external_decisions_only():
    b = batch()
    kit = review_kit(b)
    assert not verified(b, [], [])
    votes = []
    registry = []
    for r in kit:
        for reviewer in ("SYN-REVIEW-01", "SYN-REVIEW-02"):
            registry.append({"reviewer": reviewer, "attestation_id": "SYN-ACT", "authorized": True})
            votes.append(
                {
                    **r,
                    "decision": "ACCEPT",
                    "reviewer": reviewer,
                    "attestation_id": "SYN-ACT",
                    "reviewed_at": "2026-10-26T00:00:00+00:00",
                    "comment": "Synthetic unit-test vote; no actual review",
                }
            )
    assert len(verified(b, votes, registry)) == 3
    b.sessions[0].asr.text += " changed"
    with pytest.raises(ValueError):
        verified(b, votes, registry)


def test_leakage_development_previous_open_and_cross_partition():
    b = batch()
    previous = [
        {"text": b.sessions[0].asr.text, "partition": "TRAIN", "case_id": b.sessions[0].case_id}
    ]
    finding = leakage(b, previous)["findings"]
    assert finding["duplicate_text"] == 1 and finding["cross_partition_overlap"] == 1
    baseline = list(baseline_rows())
    assert len(baseline) >= 675 + 66
    s = b.sessions[0]
    s.asr.text = baseline[-1]["text"]
    assert leakage(b)["findings"]["duplicate_text"] >= 1
    b = batch()
    previous = [{"text": b.sessions[0].asr.text + " extra", "partition": "PREVIOUSLY_OPEN"}]
    assert leakage(b, previous)["findings"]["possible_paraphrase_jaccard_0_8"] == 1


def test_privacy_determinism_and_no_false_real_metrics():
    b = batch()
    a = canonical(score(b))
    assert a == canonical(score(batch()))
    for secret in (
        b.sessions[0].asr.text,
        b.sessions[0].session_id,
        "3650",
        "SYN-ENGINE",
        str(ROOT),
    ):
        assert secret not in a
    assert score(b)["HUMAN_GOLD"] == "NO"
    assert "PRIVATE_DETAIL_DO_NOT_PUBLISH" in score(b, private_detail=True)


def test_private_cli_no_literals_on_error(tmp_path, capsys):
    tmp_path.chmod(0o700)
    out = tmp_path / "report.json"
    assert main(["score", str(FIXTURE), "--output", str(out)]) == 0
    assert out.stat().st_mode & 0o777 == 0o600
    assert main(["score", str(FIXTURE), "--output", str(out)]) == 2
    d = raw()
    d["sessions"][0]["asr"]["sha256"] = "bad"
    src = tmp_path / "bad.json"
    src.write_text(json.dumps(d))
    assert main(["validate", str(src), "--output", str(tmp_path / "no.json")]) == 2
    assert d["sessions"][0]["asr"]["text"] not in capsys.readouterr().out
    with pytest.raises(ValueError):
        write_private(ROOT / "should-not-exist.json", {})


def test_real_private_input_policy(tmp_path, monkeypatch):
    tmp_path.chmod(0o700)
    src = tmp_path / "input.json"
    src.write_text(json.dumps(synthetic_real_mutation()))
    src.chmod(0o600)
    monkeypatch.delenv("CI", raising=False)
    assert load(src).sessions[0].source_type == "ASR_REAL"
    monkeypatch.setenv("CI", "true")
    with pytest.raises(ValueError):
        load(src)


def test_scope_direct_new_branch_and_mixed_fail_closed(monkeypatch):
    from tools import ci_corpus_scope

    responses = iter(
        ["b27edfa522f08c4621d31113b14295ece08e2109\n", "training/benchmark_campo/metrics.py\n"]
    )
    monkeypatch.setattr(
        ci_corpus_scope.subprocess, "check_output", lambda *a, **kw: next(responses)
    )
    assert corpus_only(changed_paths({"before": "0" * 40}))
    assert not corpus_only(["training/benchmark_campo/metrics.py", "src/homex_nlp/rules.py"])
    assert not corpus_only(["training/benchmark_campo/train.py"])
    assert not corpus_only(["tests/fixtures/benchmark_campo/private.json"])
    assert not corpus_only(["docs/other.md"])


def test_empty_batch_honest_real_unavailable():
    d = raw()
    d["sessions"] = []
    r = score(batch(d))
    assert r["groups"]["ASR_REAL"]["wer_micro"]["wer"] is None
    assert r["groups"]["ASR_REAL"]["productivity"]["paired_saving_seconds"]["p50"] is None


def test_multi_batch_aggregation_preserves_hash_bound_review(tmp_path):
    from training.benchmark_campo.pipeline import combine

    a = batch()
    d = raw()
    d["batch_id"] = "SYN-BATCH-02"
    d["sessions"][0].update(batch_id="SYN-BATCH-02", session_id="SYN-SESSION-02")
    b = batch(d)
    combined = combine([a, b])
    assert review_kit(combined) == review_kit(a) + review_kit(b)
    r = score(combined)
    assert r["groups"]["SINTETICO_PRUEBA"]["wer_micro"]["N"] == 12
    assert r["groups"]["SINTETICO_PRUEBA"]["sessions"] == 2
    with pytest.raises(ValueError):
        combine([a, a])
    tmp_path.chmod(0o700)
    second = tmp_path / "second.json"
    second.write_text(canonical(d))
    assert (
        main(["aggregate", str(FIXTURE), str(second), "--output", str(tmp_path / "aggregate.json")])
        == 0
    )


def test_duplicate_json_keys_rejected_privately(tmp_path):
    from training.benchmark_campo.pipeline import read_json

    p = tmp_path / "bad.json"
    p.write_text('{"a": 1, "a": 2}')
    with pytest.raises(ValueError):
        read_json(p)


def test_inconsistent_time_landmarks_and_dimension_unit_rejected():
    d = raw()
    d["sessions"][0]["timings"].append(
        {
            "metric": "frontend",
            "unit": "s",
            "start_boundary": "frontend_received",
            "end_boundary": "form_usable",
            "start": 3.0,
            "end": 5.0,
            "clock": "monotonic_common",
        }
    )
    with pytest.raises(ValidationError):
        batch(d)
    d = raw()
    d["sessions"][0]["reference"]["commercial"]["facts"][3]["unit"] = "PERCENT"
    with pytest.raises(ValidationError):
        batch(d)


def test_independent_micro_wer_denominator_not_average():
    from training.benchmark_campo.metrics import wer_counts

    a = alignment("a", "b")
    b = alignment("a b c", "a b c")
    assert wer_counts(*(a[k] + b[k] for k in ("S", "D", "I", "N")))["wer"] == 0.25


def test_schema_json_matches_validator():
    import jsonschema

    schema = json.loads((FIXTURE.parent / "schema.json").read_text())["batch"]
    jsonschema.validate(raw(), schema)


@pytest.mark.parametrize(
    "field,value",
    [
        ("total_price", "7300.01"),
        ("discount", "1"),
        ("material", "metal"),
        ("color", "rojo"),
        ("accessory_quantity", "3"),
        ("unit", "JUEGO"),
    ],
)
def test_remaining_commercial_field_mutations(field, value):
    g = batch().sessions[0].reference.commercial
    if field == "unit":
        from training.benchmark_campo.models import Fact

        g.facts.append(Fact(scope="ITEM", field="unit", value="PIEZA"))
    p = g.model_copy(deep=True)
    next(f for f in p.facts if f.field == field).value = value
    counts, errors, den = commercial_counts(g, p)
    assert counts[field]["false_assertion"] == 1
    assert counts[field]["omission"] == 1
    assert errors == (0 if field == "color" else 1)
    assert den > 0


def test_metadata_versions_are_separate_strata():
    from training.benchmark_campo.pipeline import engine_key

    e = batch().sessions[0].engines[0]
    changed = e.model_copy(update={"version": "SYN-OTHER"})
    assert engine_key(e) != engine_key(changed)


def test_private_detail_keeps_missing_session_not_evaluable():
    d = raw()
    del d["sessions"][0]["reference"]
    detail = score(batch(d), private_detail=True)["PRIVATE_DETAIL_DO_NOT_PUBLISH"]
    assert detail["per_session"][0]["wer"]["status"] == "NOT_EVALUABLE"


def test_inverted_pipeline_stages_rejected():
    d = raw()
    d["sessions"][0]["timings"] = [
        {
            "metric": "asr",
            "unit": "s",
            "start_boundary": "asr_started",
            "end_boundary": "asr_done",
            "start": 3.0,
            "end": 4.0,
            "clock": "monotonic_common",
        },
        {
            "metric": "nlp",
            "unit": "s",
            "start_boundary": "nlp_started",
            "end_boundary": "nlp_done",
            "start": 1.0,
            "end": 2.0,
            "clock": "monotonic_common",
        },
    ]
    with pytest.raises(ValidationError):
        batch(d)


def test_rc1_baseline_includes_its_actual_layout():
    rows = list(baseline_rows())
    # V1 675 + RC1 documentary/oral 727 + RC2 development 66.
    assert len(rows) == 1468


def test_audit_a_complete_adjudicated_negative_abstention():
    negative = Commercial(
        scopes={"ITEM": "item", "CONDITIONS": "conditions"},
        facts=[],
        coverage="complete",
        reviewed_keys=["ITEM:sold_quantity"],
    )
    counts, errors, denominator = commercial_counts(negative, None)
    assert counts["sold_quantity"]["safe_abstention"] == 1
    assert counts["sold_quantity"]["expected_positive"] == 0
    assert errors == 0 and denominator == 1


def audit_pair():
    """Two artificial sessions: first faithful equals second ASR; no shared IDs."""
    from training.benchmark_campo.models import sha

    d = raw()
    first = d["sessions"][0]
    first["asr"] = {"text": "orbita nube solar", "sha256": sha("orbita nube solar")}
    first["reference"]["faithful"] = {
        "text": "cuarzo azul brillante",
        "sha256": sha("cuarzo azul brillante"),
    }
    first["reference"]["ner"] = None
    first["engines"] = []
    first["provenance"]["partition"] = "TRAIN"
    second = copy.deepcopy(first)
    second.update(session_id="SYN-SESSION-02", case_id="SYN-CASE-02", productivity=None)
    second["provenance"].update(
        source_id="SYN-SOURCE-02",
        template_id="SYN-TEMPLATE-02",
        speaker_id="SYN-SPEAKER-02",
        partition="EXTERNAL_CANDIDATE",
    )
    second["asr"] = copy.deepcopy(first["reference"]["faithful"])
    second["reference"]["faithful"] = {
        "text": "motor lunar remoto",
        "sha256": sha("motor lunar remoto"),
    }
    d["sessions"].append(second)
    return d


def test_audit_b_faithful_asr_cross_session_leak():
    findings = leakage(batch(audit_pair()))["findings"]
    assert findings.get("duplicate_text", 0) == 1
    assert findings.get("cross_partition_overlap", 0) == 1


def test_audit_c_general_attribute_without_invented_component():
    from training.benchmark_campo.models import Fact

    reference = Commercial(
        scopes={"ITEM": "item", "CONDITIONS": "conditions"},
        facts=[Fact(scope="ITEM", field="color", value="roble")],
    )
    assert reference.facts[0].scope == "ITEM"


@pytest.mark.parametrize("coverage", ["complete", "partial"])
@pytest.mark.parametrize("prediction", ["none", "empty", "spurious"])
def test_adjudicated_negative_denominators_and_no_positive_inflation(coverage, prediction):
    from training.benchmark_campo.metrics import commercial_report
    from training.benchmark_campo.models import Fact

    scopes = {"ITEM": "item", "CONDITIONS": "conditions"}
    gold = Commercial(
        scopes=scopes,
        facts=[],
        coverage=coverage,
        reviewed_keys=["ITEM:sold_quantity", "ITEM:unit_price"],
    )
    actual = None if prediction == "none" else Commercial(scopes=scopes, facts=[])
    if prediction == "spurious":
        actual.facts.append(Fact(scope="ITEM", field="sold_quantity", value="2"))
    counts, errors, n = commercial_counts(gold, actual)
    report = commercial_report(counts, errors, n, 1)
    expected_safe = 1 if prediction == "spurious" else 2
    assert report["negative_opportunities"] == 2
    assert report["safe_abstentions"] == expected_safe
    assert report["safe_abstention_rate"] == expected_safe / 2
    assert errors == (1 if prediction == "spurious" else 0) and n == 2
    assert all(r["accuracy"] is None and r["correct"] == 0 for r in report["by_field"].values())
    assert counts["sold_quantity"]["false_assertion"] == (prediction == "spurious")


def test_empty_complete_without_adjudication_has_no_negative_denominator():
    from training.benchmark_campo.metrics import commercial_report

    gold = Commercial(scopes={"ITEM": "item", "CONDITIONS": "conditions"}, facts=[])
    counts, errors, n = commercial_counts(gold, None)
    assert (counts, errors, n) == ({}, 0, 0)
    report = commercial_report(counts, errors, n, 1)
    assert report["safe_abstention_rate"] is None and report["negative_opportunities"] == 0


def test_positive_accuracy_does_not_include_reviewed_negative():
    from training.benchmark_campo.metrics import commercial_report
    from training.benchmark_campo.models import Fact

    gold = Commercial(
        scopes={"ITEM": "item", "CONDITIONS": "conditions"},
        facts=[Fact(scope="ITEM", field="product", value="mesa")],
        reviewed_keys=["ITEM:sold_quantity"],
    )
    counts, errors, n = commercial_counts(gold, gold)
    report = commercial_report(counts, errors, n, 1)
    assert report["by_field"]["product"]["accuracy"] == 1
    assert report["by_field"]["sold_quantity"]["accuracy"] is None
    assert report["safe_abstentions"] == 1
    assert sum(row["correct"] for row in counts.values()) == 1


def set_synthetic_text(session, coordinate, text):
    from training.benchmark_campo.models import sha

    value = {"text": text, "sha256": sha(text)}
    if coordinate == "asr":
        session["asr"] = value
    else:
        session["reference"]["faithful"] = value


@pytest.mark.parametrize("first_coordinate", ["asr", "faithful"])
@pytest.mark.parametrize("second_coordinate", ["asr", "faithful"])
def test_all_text_coordinate_pairs_and_permutations(first_coordinate, second_coordinate):
    d = audit_pair()
    for i, session in enumerate(d["sessions"]):
        set_synthetic_text(session, "asr", ["orbita nube solar", "motor lunar remoto"][i])
        set_synthetic_text(session, "faithful", ["nieve hielo blanco", "tigre selva verde"][i])
    for session, coordinate in zip(d["sessions"], [first_coordinate, second_coordinate]):
        set_synthetic_text(session, coordinate, "cuarzo azul brillante")
    b = batch(d)
    forward = leakage(b)
    b.sessions.reverse()
    reverse = leakage(b)
    assert forward == reverse
    assert forward["findings"] == {"cross_partition_overlap": 1, "duplicate_text": 1}
    assert forward["comparisons"] == {"session_pairs": 1, "historical_evidence_pairs": 2936}
    assert forward["baseline_rows"] == 1468


def test_near_duplicate_faithful_asr_is_order_independent():
    d = audit_pair()
    set_synthetic_text(d["sessions"][0], "faithful", "cuarzo azul brillante lejano celeste")
    set_synthetic_text(d["sessions"][1], "asr", "cuarzo azul brillante lejano celeste extra")
    b = batch(d)
    a = leakage(b)
    b.sessions.reverse()
    assert a == leakage(b)
    assert a["findings"] == {"cross_partition_overlap": 1, "possible_paraphrase_jaccard_0_8": 1}


def test_multiple_matching_representations_and_audio_count_once_per_pair():
    d = audit_pair()
    for session in d["sessions"]:
        for coordinate in ("asr", "faithful"):
            set_synthetic_text(session, coordinate, "cuarzo azul brillante")
        session["audio"] = {"private_ref": "SYN-AUDIO", "sha256": "c" * 64}
    findings = leakage(batch(d))["findings"]
    assert findings == {
        "cross_partition_overlap": 1,
        "duplicate_text": 1,
        "same_dictation_audio": 1,
    }


@pytest.mark.parametrize("key", ["text", "asr", "faithful", "reference"])
@pytest.mark.parametrize("wrapped", [False, True])
def test_previously_open_equivalent_text_fields(key, wrapped):
    b = batch(audit_pair())
    b.sessions = b.sessions[:1]
    value = "orbita nube solar"
    if wrapped:
        from training.benchmark_campo.models import sha

        value = {"text": value, "sha256": sha(value)}
    row = {
        key: {"faithful": value} if key == "reference" else value,
        "partition": "PREVIOUSLY_OPEN",
    }
    result = leakage(b, [row])
    assert result["findings"] == {"cross_partition_overlap": 1, "duplicate_text": 1}
    assert result["comparisons"]["historical_evidence_pairs"] == 1469


def test_previously_open_all_representations_are_one_evidence_pair():
    b = batch(audit_pair())
    b.sessions = b.sessions[:1]
    row = {
        "text": "orbita nube solar",
        "asr": "orbita nube solar",
        "faithful": "cuarzo azul brillante",
        "partition": "DEV",
    }
    result = leakage(b, [row])
    assert result["findings"]["duplicate_text"] == 1
    assert result["findings"]["cross_partition_overlap"] == 1


def test_three_session_permutations_stable_and_no_empty_text_matches():
    from itertools import permutations

    d = audit_pair()
    third = copy.deepcopy(d["sessions"][1])
    third.update(session_id="SYN-SESSION-03", case_id="SYN-CASE-03")
    third["provenance"].update(
        source_id="SYN-SOURCE-03",
        template_id="SYN-TEMPLATE-03",
        speaker_id="SYN-SPEAKER-03",
        partition="DEV",
    )
    d["sessions"].append(third)
    expected = None
    for rows in permutations(d["sessions"]):
        d["sessions"] = list(rows)
        result = leakage(batch(d), [{"audio_sha256": "0" * 64, "partition": "DEV"}])
        assert result["comparisons"]["session_pairs"] == 3
        if expected is None:
            expected = result
        assert result == expected
    assert result["findings"]["duplicate_text"] == 3


@pytest.mark.parametrize(
    "field,value,unit",
    [("material", "melamina", None), ("color", "roble", None), ("thickness", "18", "mm")],
)
def test_general_attributes_exact_and_not_component_equivalents(field, value, unit):
    from training.benchmark_campo.models import Fact

    scopes = {
        "ITEM": "item",
        "CONDITIONS": "conditions",
        "TABLERO": "component",
        "MESON": "component",
    }
    gold = Commercial(
        scopes=scopes, facts=[Fact(scope="ITEM", field=field, value=value, unit=unit)]
    )
    counts, errors, _ = commercial_counts(gold, gold)
    assert counts[field]["correct"] == 1 and errors == 0
    wrong = Commercial(
        scopes=scopes, facts=[Fact(scope="TABLERO", field=field, value=value, unit=unit)]
    )
    counts, _, _ = commercial_counts(gold, wrong)
    assert counts[field]["correct"] == 0
    assert counts[field]["omission"] == 1 and counts[field]["false_assertion"] == 1
    meson = Commercial(
        scopes=scopes, facts=[Fact(scope="MESON", field=field, value=value, unit=unit)]
    )
    assert commercial_counts(wrong, meson)[0][field]["correct"] == 0


@pytest.mark.parametrize(
    "scope,field,value",
    [
        ("ITEM", "internal_quantity", "2"),
        ("ITEM", "currency", "BOB"),
        ("TABLERO", "unit_price", "10"),
        ("TABLERO", "sold_quantity", "2"),
        ("CONDITIONS", "color", "roble"),
        ("ITEM", "accessory_quantity", "2"),
    ],
)
@pytest.mark.parametrize("negative", [False, True])
def test_scope_restrictions_still_apply_to_facts_and_adjudicated_negatives(
    scope, field, value, negative
):
    from training.benchmark_campo.models import Fact

    scopes = {"ITEM": "item", "CONDITIONS": "conditions", "TABLERO": "component"}
    with pytest.raises(ValueError):
        if negative:
            Commercial(scopes=scopes, facts=[], reviewed_keys=[scope + ":" + field])
        else:
            Commercial(scopes=scopes, facts=[Fact(scope=scope, field=field, value=value)])


@pytest.mark.parametrize(
    "row",
    [
        [],
        {"asr": []},
        {"faithful": {"text": "synthetic", "sha256": "0" * 64}},
        {"reference": "invalid"},
    ],
)
def test_malformed_previously_open_representations_rejected(row):
    with pytest.raises(ValueError):
        leakage(batch(), [row])


def test_historical_fixture_input_and_results_preserved_additively():
    import subprocess

    old_input = subprocess.check_output(
        ["git", "show", "59a7a03:tests/fixtures/benchmark_campo/synthetic.json"], text=True
    )
    assert FIXTURE.read_text() == old_input
    old_report = json.loads(
        subprocess.check_output(
            ["git", "show", "59a7a03:tests/fixtures/benchmark_campo/report.json"], text=True
        )
    )
    current = score(batch())
    intentional = {("seal", "scoring_rules_digest"), ("methods", "commercial")}

    def previous_contract(before, after, path=()):
        if path in intentional:
            return
        if isinstance(before, dict):
            for key, value in before.items():
                previous_contract(value, after[key], (*path, key))
        else:
            assert before == after, path

    previous_contract(old_report, current)
