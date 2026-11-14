"""Offline review public CLI and annotation validation regressions."""

import hashlib
import json
import subprocess
import sys
import wave

import pytest


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture
def fixture(tmp_path):
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    for name in ("sample.wav", "sample.aac"):
        with wave.open(str(corpus / name), "wb") as wav:
            wav.setparams((1, 2, 16000, 0, "NONE", "not compressed"))
            wav.writeframes(b"\0\0" * 32000)
    refs = tmp_path / "refs"
    baseline = tmp_path / "baseline"
    comparison = tmp_path / "comparison"
    for directory in (
        refs / "cases",
        baseline / "cases",
        comparison / "cases/original__baseline_nlp",
        comparison / "cases/original__current_nlp",
    ):
        directory.mkdir(parents=True)
    reference = {
        "id": "MP-0001",
        "category": "OTRO",
        "source_sha256": "a" * 64,
        "script_text": "</script><img src=x onerror=alert(1)>",
        "document_text": "document",
        "script_fields": [{"field": "price", "value": 10, "unit": "money"}],
        "document_fields": [],
    }
    (refs / "cases/MP-0001.json").write_text(json.dumps(reference))
    audio = {
        f"{kind}_path": str(corpus / name)
        for kind, name in [("original", "sample.aac"), ("wav", "sample.wav")]
    }
    audio.update(
        {
            f"{kind}_sha256": digest(corpus / name)
            for kind, name in [("original", "sample.aac"), ("wav", "sample.wav")]
        }
    )
    record = {
        "id": "MP-0001",
        "audio": audio,
        "duration_seconds": 2,
        "asr": {
            "text_original": "ten",
            "segments": [{"start_seconds": "0", "end_seconds": "1", "text": "ten"}],
        },
    }
    (baseline / "cases/MP-0001.json").write_text(json.dumps(record))
    for cell in ("baseline", "current"):
        (comparison / f"cases/original__{cell}_nlp/MP-0001.json").write_text(
            json.dumps({"id": "MP-0001", "nlp_raw": {"status": "OK"}, "predicted_fields": []})
        )
    return {
        "corpus": corpus,
        "references": refs,
        "baseline": baseline,
        "comparison": comparison,
        "output": tmp_path / "output",
    }


def run_cli(fixture, *extra):
    args = [sys.executable, "-m", "tools.review_commercial_voice"]
    for key, value in fixture.items():
        args += ["--" + key, str(value)]
    return subprocess.run(args + list(extra), capture_output=True, text=True)


def test_generate_preserves_audio_and_pending(fixture):
    before = digest(fixture["corpus"] / "sample.wav")
    result = run_cli(fixture)
    assert result.returncode == 0, result.stderr
    data = json.loads((fixture["output"] / "review.json").read_text())
    assert data["cases"][0]["status"] == "PENDIENTE"
    assert len(data["cases"][0]["field_types"]) == 14
    assert data["cases"][0]["nlp"]["previous_0_1_22"]["nlp_raw"]["status"] == "OK"
    assert digest(fixture["corpus"] / "sample.wav") == before
    html = (fixture["output"] / "review.html").read_text()
    assert "</script><img" not in html
    assert "connect-src" in html
    assert run_cli(fixture).returncode != 0


def test_refuse_path_escape_and_integrity(fixture, tmp_path):
    path = fixture["baseline"] / "cases/MP-0001.json"
    record = json.loads(path.read_text())
    outside = tmp_path / "outside.wav"
    outside.write_bytes(b"x")
    record["audio"]["wav_path"] = str(outside)
    path.write_text(json.dumps(record))
    assert run_cli(fixture).returncode != 0
    record["audio"]["wav_path"] = str(fixture["corpus"] / "sample.wav")
    record["audio"]["wav_sha256"] = "0" * 64
    path.write_text(json.dumps(record))
    assert run_cli(fixture).returncode != 0
    assert not fixture["output"].exists()


def test_annotation_validation(fixture, tmp_path):
    assert run_cli(fixture).returncode == 0
    data = json.loads((fixture["output"] / "review.json").read_text())
    export = {
        "schema_version": "commercial-human-review/1",
        "corpus_fingerprint": data["corpus_fingerprint"],
        "decisions": [],
    }
    path = tmp_path / "decisions.json"
    path.write_text(json.dumps(export))
    from tools.review_commercial_voice import validate_annotations

    validate_annotations(export, data)
    decision = {
        "decision_id": "test-1",
        "case_id": "MP-0001",
        "field_key": "new:price:1",
        "field": "price",
        "source_sha256": "a" * 64,
        "status": "CORREGIDO",
        "provenance": "HUMAN_AUDIO",
        "listening_attested": True,
        "reviewer": "Synthetic reviewer",
        "start_seconds": 0,
        "end_seconds": 1,
        "note": "Synthetic audio",
        "reason": "Synthetic correction",
        "uncertainty": "NONE",
        "value": 12,
        "unit": "money",
        "axis": None,
        "component": None,
        "modality": None,
        "created_at": "2026-01-01T00:00:00Z",
    }
    export["decisions"] = [decision]
    validate_annotations(export, data)
    for key, bad in [
        ("listening_attested", False),
        ("case_id", "BAD"),
        ("field", "other"),
        ("end_seconds", 3),
        ("reviewer", ""),
        ("source_sha256", "b" * 64),
        ("field_key", "nonsense"),
    ]:
        changed = dict(decision, **{key: bad})
        with pytest.raises(ValueError):
            validate_annotations(dict(export, decisions=[changed]), data)
    without_attestation = dict(decision)
    without_attestation.pop("listening_attested")
    with pytest.raises(ValueError):
        validate_annotations(dict(export, decisions=[without_attestation]), data)
    with pytest.raises(ValueError):
        validate_annotations(dict(export, corpus_fingerprint="wrong"), data)


def test_import_is_separate_and_rejects_wrong_dataset(fixture, tmp_path):
    assert run_cli(fixture).returncode == 0
    data = json.loads((fixture["output"] / "review.json").read_text())
    annotations = tmp_path / "annotations.json"
    annotations.write_text(
        json.dumps(
            {
                "schema_version": "commercial-human-review/1",
                "corpus_fingerprint": "wrong",
                "decisions": [],
            }
        )
    )
    fixture["output"] = tmp_path / "other-output"
    assert run_cli(fixture, "--annotations", str(annotations)).returncode != 0
    assert not fixture["output"].exists()
    annotations.write_text(
        json.dumps(
            {
                "schema_version": "commercial-human-review/1",
                "corpus_fingerprint": data["corpus_fingerprint"],
                "decisions": [],
            }
        )
    )
    assert run_cli(fixture, "--annotations", str(annotations)).returncode == 0
    assert (
        json.loads((fixture["output"] / "review.json").read_text())["annotations"]["decisions"]
        == []
    )


def test_candidate_identity_does_not_invalidate_human_dataset(fixture, tmp_path):
    assert run_cli(fixture).returncode == 0
    before = json.loads((fixture["output"] / "review.json").read_text())
    candidate = tmp_path / "candidate"
    (candidate / "cases/original__current_nlp").mkdir(parents=True)
    (candidate / "cases/original__current_nlp/MP-0001.json").write_text(
        json.dumps({"id": "MP-0001", "nlp_raw": {"status": "CANDIDATE"}, "predicted_fields": []})
    )
    fixture["output"] = tmp_path / "candidate-output"
    assert run_cli(fixture, "--candidate", str(candidate)).returncode == 0
    after = json.loads((fixture["output"] / "review.json").read_text())
    assert before["corpus_fingerprint"] == after["corpus_fingerprint"]
    assert after["cases"][0]["nlp"]["candidate"]["nlp_raw"]["status"] == "CANDIDATE"
    assert after["cases"][0]["nlp"]["previous_0_1_22"]["nlp_raw"]["status"] == "OK"
