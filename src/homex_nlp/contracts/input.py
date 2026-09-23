"""Entrada de texto y metadatos ASR, sin URL de audio ni IDs comerciales."""

from decimal import Decimal
from typing import Literal

from pydantic import Field, model_validator

from homex_nlp.contracts.base import Contract, Count, Currency, DecimalText, NonBlank


class TranscriptSegment(Contract):
    start_seconds: DecimalText
    end_seconds: DecimalText
    text: str

    @model_validator(mode="after")
    def chronological(self):
        if Decimal(self.end_seconds) < Decimal(self.start_seconds):
            raise ValueError("Intervalo de transcripción invertido")
        return self


class TranscriptionResult(Contract):
    schema_version: Literal["1.0"] = "1.0"
    text_original: str
    language: NonBlank
    model_version: NonBlank
    segments: list[TranscriptSegment] = Field(default_factory=list)
    duration_seconds: DecimalText | None = None
    latency_ms: Count | None = None

    @model_validator(mode="after")
    def segment_limits(self):
        previous = Decimal(0)
        for segment in self.segments:
            start, end = Decimal(segment.start_seconds), Decimal(segment.end_seconds)
            if start < previous:
                raise ValueError("Segmentos desordenados o solapados")
            if self.duration_seconds is not None and end > Decimal(self.duration_seconds):
                raise ValueError("Segmento fuera de duración")
            previous = end
        return self


class ExtractionRequest(Contract):
    schema_version: Literal["1.0"] = "1.0"
    request_id: NonBlank
    text: str  # Incluso vacío: el motor futuro devuelve NO_PROPOSAL, no un mueble ficticio.
    language: Literal["es"] = "es"
    expected_item_type: Literal["MUEBLE_MEDIDA"] = "MUEBLE_MEDIDA"
    currency_context: Currency  # Sin default silencioso de moneda.
    domain_profile_version: NonBlank | None = None
    transcription: TranscriptionResult | None = None

    @model_validator(mode="after")
    def unchanged_transcript(self):
        if self.transcription is not None and self.text != self.transcription.text_original:
            raise ValueError("text debe ser la transcripción original exacta")
        return self
