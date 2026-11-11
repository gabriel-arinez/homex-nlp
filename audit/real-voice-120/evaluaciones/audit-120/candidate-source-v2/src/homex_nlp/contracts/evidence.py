"""Offsets Unicode de Python, final exclusivo, sobre texto original inalterado."""

from typing import Literal

from pydantic import JsonValue, model_validator

from homex_nlp.contracts.base import Contract, Count, NonBlank

WarningCode = Literal[
    "NO_PRODUCT",
    "NO_QUANTITY",
    "MULTIPLE_MAIN_PRODUCTS",
    "MISSING_UNIT",
    "MISSING_AXIS",
    "CONFLICTING_VALUES",
    "UNSUPPORTED_MATERIAL",
    "UNKNOWN_TERM",
    "INVALID_NUMBER",
    "INVALID_PRICE",
    "UNSUPPORTED_CURRENCY",
    "REQUIRED_FIELD_MISSING",
    "RULES_ONLY_MODE",
    "MODEL_UNAVAILABLE",
    "INVALID_OFFSET",
    "OUT_OF_VOICE_SCOPE",
]


class Warning(Contract):
    code: WarningCode
    path: str  # JSON Pointer; vacío refiere al documento completo.
    severity: Literal["INFO", "REVIEW", "ERROR"]
    message: NonBlank

    @model_validator(mode="after")
    def pointer(self):
        if self.path and not self.path.startswith("/"):
            raise ValueError("path debe ser un JSON Pointer o vacío")
        return self


class Candidate(Contract):
    candidate_id: NonBlank
    label: NonBlank
    start: Count
    end: Count
    text: NonBlank
    source: Literal["NER", "RULE", "PARSER"]
    normalized_value: JsonValue = None
    component_ref: NonBlank | None = None
    decision: Literal["ACCEPTED", "REJECTED", "UNRESOLVED"] = "UNRESOLVED"
    reason: NonBlank | None = None

    @model_validator(mode="after")
    def interval(self):
        if self.end <= self.start:
            raise ValueError("El span debe tener inicio < fin")
        if self.decision == "REJECTED" and self.reason is None:
            raise ValueError("Un candidato rechazado requiere motivo")
        return self
