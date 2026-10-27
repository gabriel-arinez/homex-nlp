"""SYNTHETIC ONLY: tiny PCM waves created in temporary dirs, no real audio/model."""

import csv
import hashlib
import io
import json
from dataclasses import replace
from types import SimpleNamespace

import pytest

from training.audio_pilot.asr import Decode, LocalWhisper, model_manifest
from training.audio_pilot.dataset import IDS, PilotError, validate
from training.audio_pilot.export import export_batch
from training.audio_pilot.runner import compare, evaluate, load_run
from training.benchmark_campo.pipeline import canonical, digest, score


def wav(number):
    import wave

    stream = io.BytesIO()
    with wave.open(stream, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(16000)
        w.writeframes(bytes([number, 0]) * (100 + number))
    return stream.getvalue()


def write_manifest(root, rows):
    with (root / "manifest.csv").open("w", newline="") as s:
        writer = csv.DictWriter(s, fieldnames=["guion", "archivo", "sha256", "bytes"])
        writer.writeheader()
        writer.writerows(rows)


@pytest.fixture
def dataset(tmp_path):
    root = tmp_path / "dataset"
    (root / "audios").mkdir(parents=True)
    rows = []
    for number, case in enumerate(IDS, 1):
        data = wav(number)
        (root / "audios" / f"{case}.wav").write_bytes(data)
        rows.append(
            {
                "guion": case,
                "archivo": f"audios/{case}.wav",
                "sha256": hashlib.sha256(data).hexdigest(),
                "bytes": str(len(data)),
            }
        )
    write_manifest(root, rows)
    return root, rows


class StubASR:
    def __init__(self, directory, parameters):
        self.manifest = {"model_digest": "SYNTHETIC_MODEL_NOT_REAL"}
        self.versions = {"stub": "SINTETICO_SOLO_PRUEBA"}
        self.load_seconds = 0.0

    def transcribe(self, payload):
        assert payload.startswith(b"RIFF")
        return [{"start": 0.0, "end": 0.005, "text": " TEXTO_SINTETICO_PRIVADO"}]


def stub_run(dataset, tmp_path, name="run"):
    root, _ = dataset
    output = tmp_path / name
    evaluate(root, output, execute=True, synthetic=True, factory=StubASR)
    return output


def test_exact_input_hashes_determinism_and_no_gold(dataset):
    root, _ = dataset
    a = validate(root, synthetic=True)
    assert canonical(a) == canonical(validate(root, synthetic=True))
    assert [r["id"] for r in a["entries"]] == list(IDS)
    assert a["HUMAN_GOLD"] == "NO" and a["WER"] == "N/A" and a["HOLDOUT_EXTERNO"] == 0
    assert a["training_use"] == "PROHIBITED"


@pytest.mark.parametrize(
    "bad",
    [
        "missing",
        "duplicate",
        "extra",
        "unpad",
        "traversal",
        "absolute",
        "extension",
        "hash",
        "size",
        "duplicate-content",
    ],
)
def test_reject_manifest_mutations(dataset, bad):
    root, rows = dataset
    if bad == "missing":
        rows.pop()
    elif bad == "duplicate":
        rows[-1] = rows[0]
    elif bad == "extra":
        rows.append(rows[0])
    elif bad == "unpad":
        rows[0]["guion"] = "1"
    elif bad == "traversal":
        rows[0]["archivo"] = "../01.wav"
    elif bad == "absolute":
        rows[0]["archivo"] = "/tmp/01.wav"
    elif bad == "extension":
        rows[0]["archivo"] = "mueble.m4a"
    elif bad == "hash":
        rows[0]["sha256"] = "0" * 64
    elif bad == "size":
        rows[0]["bytes"] = "1"
    else:
        rows[1]["sha256"] = rows[0]["sha256"]
    write_manifest(root, rows)
    with pytest.raises(PilotError):
        validate(root)


@pytest.mark.parametrize("kind", ["file", "audios", "manifest", "root"])
def test_symlinks_rejected(dataset, tmp_path, kind):
    root, _ = dataset
    if kind == "root":
        link = tmp_path / "link"
        link.symlink_to(root, target_is_directory=True)
        root = link
    elif kind == "audios":
        target = root / "audios"
        target.rename(root / "actual")
        target.symlink_to(root / "actual", target_is_directory=True)
    else:
        f = root / ("manifest.csv" if kind == "manifest" else "audios/01.wav")
        target = tmp_path / "original"
        f.rename(target)
        f.symlink_to(target)
    with pytest.raises(PilotError):
        validate(root)


@pytest.mark.parametrize("kind", ["missing", "lfs", "corrupt", "truncated", "extra-m4a"])
def test_audio_integrity_and_extras(dataset, kind):
    root, rows = dataset
    f = root / "audios/01.wav"
    if kind == "missing":
        f.unlink()
    elif kind == "extra-m4a":
        (root / "audios/mueble.m4a").write_bytes(b"not audio")
    else:
        data = (
            b"version https://git-lfs.github.com/spec/v1\noid sha256:abc\n"
            if kind == "lfs"
            else b"corrupt"
            if kind == "corrupt"
            else wav(1)[:-2]
        )
        f.write_bytes(data)
        rows[0].update(sha256=hashlib.sha256(data).hexdigest(), bytes=str(len(data)))
        write_manifest(root, rows)
    with pytest.raises(PilotError, match="LFS_POINTER_NOT_HYDRATED" if kind == "lfs" else ".*"):
        validate(root)


def test_validate_only_never_calls_model_and_creates_blank_annotation(dataset, tmp_path):
    def forbidden(*a):
        raise AssertionError("ASR must not be instantiated")

    result = evaluate(dataset[0], tmp_path / "output", synthetic=True, factory=forbidden)
    assert result["status"] == "ASR_NO_EJECUTADO"
    kit = json.loads((tmp_path / "output/annotation-template.json").read_text())
    assert all(r["reference"] is None for r in kit["entries"])
    assert "TEXTO" not in canonical(kit)


def test_private_outputs_quality_vs_timings_and_aggregate_redaction(dataset, tmp_path):
    a = stub_run(dataset, tmp_path, "one")
    b = stub_run(dataset, tmp_path, "two")
    ra, rb = load_run(a), load_run(b)
    assert ra["quality_digest"] == rb["quality_digest"]
    assert ra["records"][0]["text"].startswith(" TEXTO_SINTETICO")
    summary = json.loads((a / "summary.json").read_text())
    public = canonical(summary)
    assert "TEXTO_SINTETICO" not in public and str(tmp_path) not in public
    assert summary["asr_seconds"]["first_inference"]["n"] == 1
    assert summary["asr_seconds"]["warm"]["n"] == 19
    assert summary["WER"] == "N/A"
    assert all(f.stat().st_mode & 0o777 == 0o600 for f in a.iterdir())
    result = compare([a, b])
    assert result["quality_improvement"].startswith("NOT_EVALUABLE")
    assert result["independent_processes"] == "UNVERIFIED_ARTIFACTS_ONLY"
    with pytest.raises(PilotError):
        compare([a, a])


def test_changed_input_or_output_cannot_be_compared(dataset, tmp_path):
    a = stub_run(dataset, tmp_path, "one")
    b = stub_run(dataset, tmp_path, "two")
    p = b / "run.json"
    r = json.loads(p.read_text())
    r["records"][0]["text"] = "TAMPER"
    p.write_text(json.dumps(r))
    with pytest.raises(PilotError, match="INVALID_RUN_OR_DIGEST"):
        compare([a, b])


def test_output_in_git_and_symlink_rejected(dataset, tmp_path):
    from training.audio_pilot.runner import ROOT

    with pytest.raises(ValueError):
        evaluate(dataset[0], ROOT / "DO_NOT_CREATE", synthetic=True)
    path = tmp_path / "alias"
    path.symlink_to(tmp_path / "destination")
    with pytest.raises(PilotError):
        evaluate(dataset[0], path, synthetic=True)


def test_model_missing_and_ci_guard_before_heavy_import(tmp_path, monkeypatch):
    monkeypatch.setenv("CI", "true")
    with pytest.raises(PilotError, match="REAL_ASR_FORBIDDEN_IN_CI"):
        LocalWhisper(tmp_path / "missing", Decode())
    with pytest.raises(PilotError, match="MODEL_NOT_INSTALLED"):
        model_manifest(tmp_path / "missing", "base")


def test_model_absence_preserves_honest_blocked_report(dataset, tmp_path, monkeypatch):
    def unavailable(*a):
        raise PilotError("MODEL_NOT_INSTALLED")

    with pytest.raises(PilotError):
        evaluate(
            dataset[0], tmp_path / "blocked", execute=True, synthetic=True, factory=unavailable
        )
    result = json.loads((tmp_path / "blocked/summary.json").read_text())
    assert result["status"] == "ASR_NO_EJECUTADO"
    assert result["model_load_seconds"] is None and result["asr_seconds"]["all"]["n"] == 0


def test_decode_fixed_reproducible_and_invalid_options():
    assert digest(Decode().validate()) == digest(Decode().validate())
    assert digest(Decode().validate()) != digest(replace(Decode(), beam_size=3).validate())
    with pytest.raises(PilotError):
        replace(Decode(), beam_size=0).validate()


def test_cli_error_never_prints_private_values(dataset, tmp_path, capsys):
    from training.audio_pilot.cli import main

    assert (
        main(
            [
                "evaluate",
                "--dataset-dir",
                str(tmp_path / "PRIVATE_SECRET"),
                "--validate-only",
                "--synthetic-test-data",
                "--output-dir",
                str(tmp_path / "out"),
            ]
        )
        == 2
    )
    assert "PRIVATE_SECRET" not in capsys.readouterr().out


def test_real_data_blocked_in_ci(dataset, tmp_path, monkeypatch):
    monkeypatch.setenv("CI", "true")
    with pytest.raises(PilotError, match="REAL_AUDIO_FORBIDDEN_IN_CI"):
        evaluate(dataset[0], tmp_path / "out")


def test_export_uses_real_benchmark_schema_without_fabricated_consent_or_gold(
    dataset, tmp_path, monkeypatch
):
    # Synthetic engine output, relabelled only inside this stub test to exercise
    # the REAL transport schema. Never persisted as a fixture or real evidence.
    path = stub_run(dataset, tmp_path)
    p = path / "run.json"
    run = json.loads(p.read_text())
    run["input"]["source_type"] = "PILOTO_REAL_DIAGNOSTICO_CONOCIDO"
    from training.audio_pilot.runner import quality

    run["quality_digest"] = digest(quality(run))
    p.write_text(json.dumps(run))
    declarations = {
        "batch_id": "SYN-BATCH",
        "frozen_date": "2026-10-26",
        "sessions": [
            {
                "id": i,
                "speaker_id": "SYN-SPEAKER",
                "consent": {
                    "human_declared": True,
                    "act_id": "SYN-ACT",
                    "use_policy_id": "SYN-USE",
                    "retention_policy_id": "SYN-RETENTION",
                },
            }
            for i in IDS
        ],
    }
    d = tmp_path / "declarations.json"
    d.write_text(json.dumps(declarations))
    batch = export_batch(path, d)
    from training.benchmark_campo.models import Batch

    typed = Batch.model_validate_json(json.dumps(batch))
    assert len(typed.sessions) == 20 and all(
        s.reference is None and s.provenance.partition == "PREVIOUSLY_OPEN" for s in typed.sessions
    )
    assert all(not s.engines for s in typed.sessions)
    # Existing scorer, no review decisions -> no real-reference scoring eligible.
    report = score(typed)
    assert report["HUMAN_GOLD"] == "NO"
    declarations["sessions"][0]["consent"]["human_declared"] = False
    d.write_text(json.dumps(declarations))
    with pytest.raises(ValueError):
        export_batch(path, d)


def test_local_adapter_uses_explicit_decode_and_no_download(tmp_path, monkeypatch):
    import sys

    monkeypatch.delenv("CI", raising=False)
    monkeypatch.delenv("HOMEX_DATA_GATE_NO_TRAINING", raising=False)
    model = tmp_path / "model"
    model.mkdir()
    (model / "config.json").write_text('{"d_model":512}')
    (model / "model.bin").write_bytes(b"SYNTHETIC_MODEL_STUB")
    (model / "tokenizer.json").write_text("{}")
    calls = {}

    class WhisperStub:
        def __init__(self, path, **kwargs):
            calls["load"] = kwargs

        def transcribe(self, audio, **kwargs):
            assert audio.read().startswith(b"RIFF")
            calls["decode"] = kwargs
            return iter([SimpleNamespace(start=0, end=0.001, text=" SINTETICO")]), None

    import training.audio_pilot.asr as adapter

    monkeypatch.setitem(sys.modules, "faster_whisper", SimpleNamespace(WhisperModel=WhisperStub))
    monkeypatch.setattr(adapter.importlib.metadata, "version", lambda name: "STUB")
    params = Decode(
        beam_size=3, expected_model_sha256=hashlib.sha256(b"SYNTHETIC_MODEL_STUB").hexdigest()
    )
    engine = LocalWhisper(model, params)
    assert engine.transcribe(wav(1))[0]["text"] == " SINTETICO"
    assert calls["load"]["local_files_only"] is True
    assert calls["decode"]["beam_size"] == 3 and calls["decode"]["language"] == "es"
    with pytest.raises(PilotError, match="EXPECTED_MODEL_SHA256_MISMATCH"):
        LocalWhisper(model, replace(params, expected_model_sha256="0" * 64))
    with pytest.raises(PilotError, match="MODEL_VARIANT_ARCHITECTURE_MISMATCH"):
        model_manifest(model, "small")


def test_asr_inference_error_records_fixed_code_not_private_exception(dataset, tmp_path):
    class Broken(StubASR):
        def transcribe(self, payload):
            raise RuntimeError("SECRET_CONTENT_AND_PRIVATE_PATH")

    output = tmp_path / "failed"
    summary = evaluate(dataset[0], output, execute=True, synthetic=True, factory=Broken)
    assert summary["failed"] == 20 and summary["status"] == "ASR_PARTIAL_FAILURE"
    assert summary["asr_seconds"]["all"]["n"] == 0
    assert "SECRET_CONTENT" not in (output / "run.json").read_text()


def test_export_annotation_audio_binding(dataset, tmp_path):
    # Membership/audio binding is checked before accepting human reference input.
    path = stub_run(dataset, tmp_path)
    source = path / "run.json"
    run = json.loads(source.read_text())
    run["input"]["source_type"] = "PILOTO_REAL_DIAGNOSTICO_CONOCIDO"
    from training.audio_pilot.runner import quality

    run["quality_digest"] = digest(quality(run))
    source.write_text(json.dumps(run))
    declared = tmp_path / "declarations.json"
    declared.write_text(json.dumps({"sessions": [{"id": i} for i in IDS]}))
    annotations = json.loads((path / "annotation-template.json").read_text())
    annotations["entries"][0]["audio_sha256"] = "0" * 64
    p = tmp_path / "annotations.json"
    p.write_text(json.dumps(annotations))
    with pytest.raises(PilotError, match="ANNOTATION_AUDIO_MISMATCH"):
        export_batch(path, declared, p)


def test_audio_scope_first_push_exact_allowlist_and_production(monkeypatch):
    from tools import ci_corpus_scope
    from training.audio_pilot.gate import ALLOWED, BASE

    assert ci_corpus_scope.corpus_only(sorted(ALLOWED))
    assert not ci_corpus_scope.corpus_only(["training/audio_pilot/secret.json"])
    assert not ci_corpus_scope.corpus_only(["training/audio_pilot/model.bin"])
    assert not ci_corpus_scope.corpus_only(
        ["training/audio_pilot/asr.py", "src/homex_nlp/engine.py"]
    )
    responses = iter([BASE + "\n", "training/audio_pilot/asr.py\n"])
    monkeypatch.setattr(
        ci_corpus_scope.subprocess, "check_output", lambda *a, **kw: next(responses)
    )
    assert ci_corpus_scope.corpus_only(ci_corpus_scope.changed_paths({"before": "0" * 40}))


def test_missing_columns_and_extra_csv_values_rejected(dataset):
    root, rows = dataset
    rows[0]["archivo"] = None
    write_manifest(root, rows)
    with pytest.raises(PilotError):
        validate(root)


def test_compare_changed_dataset_rejected_even_when_resealed(dataset, tmp_path):
    from training.audio_pilot.runner import quality

    a = stub_run(dataset, tmp_path, "one")
    b = stub_run(dataset, tmp_path, "two")
    path = b / "run.json"
    run = json.loads(path.read_text())
    run["input"]["entries"][0]["audio_sha256"] = "1" * 64
    run["input"]["dataset_digest"] = digest(run["input"]["entries"])
    run["records"][0]["audio_sha256"] = "1" * 64
    run["quality_digest"] = digest(quality(run))
    path.write_text(json.dumps(run))
    with pytest.raises(PilotError, match="COMPARISON_REQUIRES_IDENTICAL_INPUT_MANIFEST"):
        compare([a, b])


def test_output_never_overwrites_prior_evidence(dataset, tmp_path):
    out = tmp_path / "output"
    evaluate(dataset[0], out, synthetic=True)
    with pytest.raises(FileExistsError):
        evaluate(dataset[0], out, synthetic=True)


def test_cli_validate_only_is_deterministic_synthetic(dataset, tmp_path, capsys):
    from training.audio_pilot.cli import main

    for i in [1, 2]:
        assert (
            main(
                [
                    "evaluate",
                    "--validate-only",
                    "--synthetic-test-data",
                    "--dataset-dir",
                    str(dataset[0]),
                    "--output-dir",
                    str(tmp_path / str(i)),
                ]
            )
            == 0
        )
    assert (tmp_path / "1/validation.json").read_bytes() == (
        tmp_path / "2/validation.json"
    ).read_bytes()
    assert str(tmp_path) not in capsys.readouterr().out
