from pathlib import Path

import pytest

from homex_nlp.asr.service import AsrService
from homex_nlp.errors import HomexError


class FakeTranscriber:
    model_version = "fake-asr-v1"

    def transcribe(self, path: Path):
        yield 0.0, 1.0, "dos escritorios"
        yield 1.0, 2.0, " total 2000"


class FailingTranscriber(FakeTranscriber):
    def transcribe(self, path: Path):
        raise RuntimeError("fallo interno")


def audio(tmp_path: Path) -> Path:
    path = tmp_path / "captura.webm"
    path.write_bytes(b"audio-de-prueba")
    return path


def test_asr_consumes_segments_and_removes_audio(tmp_path: Path) -> None:
    path = audio(tmp_path)
    result = AsrService(FakeTranscriber()).transcribe(path)
    assert result.text_original == "dos escritorios total 2000"
    assert len(result.segments) == 2
    assert not path.exists()


def test_asr_removes_audio_when_transcription_fails(tmp_path: Path) -> None:
    path = audio(tmp_path)
    with pytest.raises(HomexError) as error:
        AsrService(FailingTranscriber()).transcribe(path)
    assert error.value.detail.code == "TRANSCRIPTION_FAILED"
    assert not path.exists()


def test_invalid_audio_is_removed_too(tmp_path: Path) -> None:
    path = tmp_path / "captura.txt"
    path.write_text("no audio")
    with pytest.raises(HomexError) as error:
        AsrService(FakeTranscriber()).transcribe(path)
    assert error.value.detail.code == "AUDIO_INVALID"
    assert not path.exists()
