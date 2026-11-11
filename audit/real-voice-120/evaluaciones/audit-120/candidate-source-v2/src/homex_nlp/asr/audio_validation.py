"""Validación local y deliberadamente conservadora de temporales de audio."""

from __future__ import annotations

from pathlib import Path

from homex_nlp.contracts.error import ErrorDetail
from homex_nlp.errors import HomexError

SUPPORTED_SUFFIXES = {".wav", ".mp3", ".m4a", ".ogg", ".webm"}


def validate_audio_file(path: Path, *, max_bytes: int = 25_000_000) -> None:
    if not path.is_file() or path.is_symlink():
        raise HomexError(
            ErrorDetail(code="AUDIO_INVALID", message="Audio temporal inexistente o inseguro.")
        )
    if path.suffix.lower() not in SUPPORTED_SUFFIXES:
        raise HomexError(ErrorDetail(code="AUDIO_INVALID", message="Formato de audio no admitido."))
    if path.stat().st_size == 0 or path.stat().st_size > max_bytes:
        raise HomexError(ErrorDetail(code="AUDIO_INVALID", message="Tamaño de audio no admitido."))
