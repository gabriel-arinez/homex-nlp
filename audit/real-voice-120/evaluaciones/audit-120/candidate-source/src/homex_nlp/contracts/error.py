"""Sobre de error serializable, independiente de excepciones del runtime."""

from typing import Literal

from homex_nlp.contracts.base import Contract, NonBlank

ErrorCode = Literal[
    "INVALID_REQUEST",
    "INVALID_CONTRACT",
    "MODEL_UNAVAILABLE",
    "INVALID_CONFIGURATION",
    "AUDIO_INVALID",
    "AUDIO_EXPIRED",
    "TRANSCRIPTION_FAILED",
    "EXTRACTION_FAILED",
]


class ErrorDetail(Contract):
    code: ErrorCode
    message: NonBlank
    retryable: bool = False
