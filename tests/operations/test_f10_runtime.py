from __future__ import annotations

import json
import subprocess
import sys
import threading
import types
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from zipfile import ZipFile

import pytest

from homex_nlp.asr import AsrService
from homex_nlp.asr.faster_whisper_adapter import FasterWhisperAdapter
from homex_nlp.contracts import ExtractionRequest
from homex_nlp.engine import RulesEngine
from homex_nlp.errors import HomexError
from tools.verify_distribution import check_privacy


class ConcurrentTranscriber:
    model_version = "f10-concurrent-double"

    def __init__(self) -> None:
        self.barrier = threading.Barrier(2)

    def transcribe(self, path: Path):
        self.barrier.wait(timeout=2)
        yield 0.0, 1.0, path.stem


def test_import_asr_is_lazy_and_does_not_import_faster_whisper() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-I",
            "-B",
            "-c",
            "import sys, homex_nlp.asr; assert 'faster_whisper' not in sys.modules",
        ],
        cwd=Path(__file__).resolve().parents[2],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr


def test_adapter_requires_local_model_before_optional_import(tmp_path: Path) -> None:
    unavailable = tmp_path / "missing-model"
    sys.modules.pop("faster_whisper", None)

    with pytest.raises(HomexError) as raised:
        FasterWhisperAdapter(unavailable)

    assert raised.value.detail.code == "MODEL_UNAVAILABLE"
    assert "faster_whisper" not in sys.modules


def test_adapter_passes_existing_local_path_without_remote_identifier(
    tmp_path: Path, monkeypatch
) -> None:
    model_path = tmp_path / "faster-whisper-small"
    model_path.mkdir()
    calls: list[tuple[str, str, str]] = []

    class LocalModel:
        def __init__(self, source: str, *, device: str, compute_type: str) -> None:
            calls.append((source, device, compute_type))

        def transcribe(self, path: str, *, language: str):
            del path, language
            return [], None

    monkeypatch.setitem(
        sys.modules, "faster_whisper", types.SimpleNamespace(WhisperModel=LocalModel)
    )

    adapter = FasterWhisperAdapter(model_path)
    list(adapter.transcribe(tmp_path / "audio.wav"))

    assert calls == [(str(model_path), "cpu", "int8")]
    assert Path(calls[0][0]).is_absolute()


def test_two_simultaneous_asr_requests_are_isolated_and_delete_audio(tmp_path: Path) -> None:
    paths = [tmp_path / f"request-{index}.wav" for index in range(2)]
    for path in paths:
        path.write_bytes(b"audio-controlado")
    transcriber = ConcurrentTranscriber()

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(AsrService(transcriber).transcribe, paths))

    assert {result.text_original for result in results} == {"request-0", "request-1"}
    assert not any(path.exists() for path in paths)


def test_rules_only_is_deterministic_and_thread_safe_under_basic_load() -> None:
    engine = RulesEngine()

    def extract(index: int) -> dict:
        result = engine.extract(
            ExtractionRequest(
                request_id=f"f10-load-{index}",
                text="tres muebles, total 100",
                currency_context="BOB",
            )
        )
        payload = result.model_dump(mode="json")
        payload.pop("request_id")
        payload.pop("latency_nlp_ms")
        return payload

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(extract, range(100)))

    assert all(result == results[0] for result in results)
    assert results[0]["engine"]["mode"] == "RULES_ONLY"


def test_failure_is_sanitized_and_audio_is_removed(tmp_path: Path, caplog) -> None:
    class SensitiveFailure:
        model_version = "f10-failure-double"

        def transcribe(self, path: Path):
            raise RuntimeError(f"secreto-en-{path}")

    path = tmp_path / "private-audio.wav"
    path.write_bytes(b"audio-controlado")

    with pytest.raises(HomexError) as raised:
        AsrService(SensitiveFailure()).transcribe(path)

    assert raised.value.detail.code == "TRANSCRIPTION_FAILED"
    assert raised.value.detail.retryable is True
    assert "private-audio" not in raised.value.detail.message
    assert "secreto" not in caplog.text
    assert not path.exists()


def test_profile_contains_only_aggregate_metrics(tmp_path: Path) -> None:
    output = tmp_path / "profile.json"
    completed = subprocess.run(
        [
            sys.executable,
            "tools/profile_f10_runtime.py",
            "--iterations",
            "20",
            "--output",
            str(output),
        ],
        cwd=Path(__file__).resolve().parents[2],
        check=True,
        capture_output=True,
        text=True,
    )
    profile = json.loads(output.read_text())

    assert profile["mode"] == "RULES_ONLY"
    assert profile["workers"] == 2
    assert profile["audio_files_remaining"] == 0
    assert profile["contains_transcript_or_audio_path"] is False
    assert profile["real_model_profile_required_in_d07"] is True
    assert "texto controlado" not in completed.stdout
    assert "homex-f10-audio" not in completed.stdout


@pytest.mark.parametrize(
    "private_name",
    [".env", ".env.production", ".env.local", ".ENV.STAGING", "config/.env.backup"],
)
def test_distribution_rejects_private_env_variants(tmp_path: Path, private_name: str) -> None:
    artifact = tmp_path / "synthetic.whl"
    with ZipFile(artifact, "w") as archive:
        archive.writestr(private_name, "DUMMY_SECRET=only_for_test")
    with pytest.raises(SystemExit, match="archivos privados"):
        check_privacy(artifact)


def test_distribution_accepts_documented_env_example(tmp_path: Path) -> None:
    artifact = tmp_path / "synthetic.whl"
    with ZipFile(artifact, "w") as archive:
        archive.writestr(".env.example", "EXAMPLE_VARIABLE=placeholder")
    check_privacy(artifact)


def test_asr_sensitive_failure_not_present_in_serialized_contract(tmp_path: Path) -> None:
    class SensitiveFailure:
        model_version = "test-double"

        def transcribe(self, path: Path):
            raise RuntimeError(f"private-token-in-{path}")

    path = tmp_path / "secret-audio.wav"
    path.write_bytes(b"audio-controlado")
    with pytest.raises(HomexError) as raised:
        AsrService(SensitiveFailure()).transcribe(path)
    serialized = raised.value.detail.model_dump_json()
    assert "private-token" not in serialized
    assert "secret-audio" not in serialized
    assert raised.value.__cause__ is not None  # No exponer traceback al cliente ni logs.
    assert not path.exists()
