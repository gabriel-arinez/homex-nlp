"""Servicio ASR inyectable que siempre intenta borrar el temporal recibido."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from time import perf_counter
from typing import Protocol

from homex_nlp.asr.audio_validation import validate_audio_file
from homex_nlp.contracts import TranscriptionResult
from homex_nlp.contracts.error import ErrorDetail
from homex_nlp.contracts.input import TranscriptSegment
from homex_nlp.errors import HomexError


class Transcriber(Protocol):
    model_version: str

    def transcribe(self, path: Path) -> Iterable[tuple[float, float, str]]: ...


class AsrService:
    """Consume todos los segmentos antes de declarar una transcripción exitosa."""

    def __init__(self, transcriber: Transcriber, *, max_bytes: int = 25_000_000):
        self._transcriber = transcriber
        self._max_bytes = max_bytes

    def transcribe(self, path: Path, *, language: str = "es") -> TranscriptionResult:
        started = perf_counter()
        try:
            validate_audio_file(path, max_bytes=self._max_bytes)
            segments = [
                TranscriptSegment(start_seconds=str(start), end_seconds=str(end), text=text)
                for start, end, text in self._transcriber.transcribe(path)
            ]
            text = " ".join(segment.text.strip() for segment in segments if segment.text.strip())
            return TranscriptionResult(
                text_original=text,
                language=language,
                model_version=self._transcriber.model_version,
                segments=segments,
                latency_ms=int((perf_counter() - started) * 1000),
            )
        except HomexError:
            raise
        except Exception as error:
            raise HomexError(
                ErrorDetail(
                    code="TRANSCRIPTION_FAILED",
                    message="No se pudo transcribir el audio temporal.",
                    retryable=True,
                )
            ) from error
        finally:
            path.unlink(missing_ok=True)
