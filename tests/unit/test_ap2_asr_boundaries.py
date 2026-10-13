"""AP2: validación de tiempo ASR, fallo a mitad del streaming y limpieza segura."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from homex_nlp.asr.service import AsrService
from homex_nlp.contracts.input import TranscriptionResult, TranscriptSegment
from homex_nlp.errors import HomexError


class BrokenStream:
    model_version = "ap2-test-model"

    def transcribe(self, path: Path):
        yield 0.0, 1.0, "una mesa"
        raise TimeoutError("motor ASR interrumpido")


class MustNotRun:
    model_version = "ap2-test-model"

    def transcribe(self, path: Path):
        raise AssertionError("La validación debe impedir invocar el modelo")


def test_ap2_no_permite_timestamps_negativos_o_invertidos():
    with pytest.raises(ValidationError) as rejected:
        TranscriptSegment(start_seconds="-0.1", end_seconds="1", text="mesa")
    assert rejected.value.errors()[0]["loc"] == ("start_seconds",)
    with pytest.raises(ValidationError, match="Intervalo de transcripción invertido"):
        TranscriptSegment(start_seconds="2", end_seconds="1", text="mesa")


def test_ap2_rechaza_solapamiento_y_segmentos_fuera_de_duracion():
    first = TranscriptSegment(start_seconds="0", end_seconds="1.5", text="una")
    overlap = TranscriptSegment(start_seconds="1.4", end_seconds="2", text="mesa")
    too_long = TranscriptSegment(start_seconds="1.5", end_seconds="2.1", text="mesa")
    base = dict(text_original="una mesa", language="es", model_version="ap2-test-model")
    with pytest.raises(ValidationError, match="Segmentos desordenados o solapados"):
        TranscriptionResult(**base, segments=[first, overlap])
    with pytest.raises(ValidationError, match="Segmento fuera de duración"):
        TranscriptionResult(**base, segments=[first, too_long], duration_seconds="2")


def test_ap2_timeout_parcial_no_guarda_audio_ni_devuelve_transcripcion(tmp_path: Path):
    path = tmp_path / "parcial.webm"
    path.write_bytes(b"datos-audio-sinteticos")
    with pytest.raises(HomexError) as caught:
        AsrService(BrokenStream()).transcribe(path)
    assert caught.value.detail.code == "TRANSCRIPTION_FAILED"
    assert caught.value.detail.retryable is True
    assert not path.exists()


@pytest.mark.parametrize("content,max_bytes", [(b"", 64), (b"demasiado-largo", 3)])
def test_ap2_audio_vacio_y_sobredimensionado_se_elimina(tmp_path: Path, content, max_bytes):
    path = tmp_path / "rechazado.webm"
    path.write_bytes(content)
    with pytest.raises(HomexError) as caught:
        AsrService(MustNotRun(), max_bytes=max_bytes).transcribe(path)
    assert caught.value.detail.code == "AUDIO_INVALID"
    assert not path.exists()


def test_ap2_directorio_invalido_no_enmascara_error_ni_se_elimina(tmp_path: Path):
    path = tmp_path / "no-es-audio.wav"
    path.mkdir()
    with pytest.raises(HomexError) as caught:
        AsrService(MustNotRun()).transcribe(path)
    assert caught.value.detail.code == "AUDIO_INVALID"
    assert path.is_dir()


def test_ap2_symlink_rechazado_elimina_enlace_sin_borrar_destino(tmp_path: Path):
    original = tmp_path / "original.webm"
    original.write_bytes(b"evidencia-externa")
    enlace = tmp_path / "enlace.webm"
    enlace.symlink_to(original)
    with pytest.raises(HomexError) as caught:
        AsrService(MustNotRun()).transcribe(enlace)
    assert caught.value.detail.code == "AUDIO_INVALID"
    assert not enlace.is_symlink()
    assert original.read_bytes() == b"evidencia-externa"
