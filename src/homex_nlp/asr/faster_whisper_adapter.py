"""Adaptador perezoso de faster-whisper; nunca descarga pesos por sí mismo."""

from __future__ import annotations

from pathlib import Path

from homex_nlp.contracts.error import ErrorDetail
from homex_nlp.errors import HomexError


class FasterWhisperAdapter:
    def __init__(self, model_path: Path, *, device: str = "cpu", compute_type: str = "int8"):
        if not model_path.is_dir():
            raise HomexError(
                ErrorDetail(
                    code="MODEL_UNAVAILABLE", message="El modelo ASR local no está disponible."
                )
            )
        try:
            from faster_whisper import WhisperModel
        except ImportError as error:
            raise HomexError(
                ErrorDetail(
                    code="MODEL_UNAVAILABLE",
                    message="Instale el extra asr para usar faster-whisper.",
                )
            ) from error
        self._model = WhisperModel(str(model_path), device=device, compute_type=compute_type)
        self.model_version = model_path.name

    def transcribe(self, path: Path):
        segments, _ = self._model.transcribe(str(path), language="es")
        for segment in segments:
            yield segment.start, segment.end, segment.text
