"""Salida singular y validación contextual de evidencia, referencias y estado."""

from typing import Literal

from pydantic import Field, model_validator

from homex_nlp.contracts.base import Contract, Count, NonBlank
from homex_nlp.contracts.error import ErrorDetail
from homex_nlp.contracts.evidence import Candidate, Warning
from homex_nlp.contracts.item import ItemProposal, Referenced


class EngineInfo(Contract):
    mode: Literal["RULES_ONLY", "HYBRID"]
    model_version: NonBlank | None = None
    rules_version: NonBlank
    normalization_version: NonBlank = "1.0"

    @model_validator(mode="after")
    def real_model(self):
        if (self.mode == "HYBRID") != (self.model_version is not None):
            raise ValueError("HYBRID requiere modelo; RULES_ONLY no declara modelo NER")
        return self


class ExtractionResult(Contract):
    schema_version: Literal["1.0"] = "1.0"
    request_id: NonBlank
    status: Literal["REQUIRES_REVIEW", "NO_PROPOSAL", "ERROR"]
    text_original: str
    item_proposal: ItemProposal | None
    proposed_item_count: Count
    candidates: list[Candidate] = Field(default_factory=list)
    warnings: list[Warning] = Field(default_factory=list)
    engine: EngineInfo
    error: ErrorDetail | None = None
    latency_nlp_ms: Count | None = None

    @model_validator(mode="after")
    def integrity(self):
        item = self.item_proposal
        if self.proposed_item_count != int(item is not None):
            raise ValueError("Conteo debe coincidir con propuesta singular o null")
        if self.status == "REQUIRES_REVIEW" and item is None:
            raise ValueError("REQUIRES_REVIEW requiere propuesta")
        if self.status == "NO_PROPOSAL" and item is not None:
            raise ValueError("NO_PROPOSAL no admite propuesta")
        if (self.status == "ERROR") != (self.error is not None):
            raise ValueError("ERROR requiere detalle de error y no puede presentarse como éxito")
        if self.status == "ERROR" and item is not None:
            raise ValueError("ERROR no admite propuesta parcial como resultado válido")
        codes = {w.code for w in self.warnings}
        if self.status == "NO_PROPOSAL" and not codes.intersection(
            {"NO_PRODUCT", "OUT_OF_VOICE_SCOPE", "MULTIPLE_MAIN_PRODUCTS"}
        ):
            raise ValueError("Indicar por qué no existe propuesta")
        if item and item.quantity is None and "NO_QUANTITY" not in codes:
            raise ValueError("Cantidad ausente requiere advertencia")
        if item and item.name is None and "NO_PRODUCT" not in codes:
            raise ValueError("Nombre ausente requiere advertencia")
        candidates = {c.candidate_id: c for c in self.candidates}
        if len(candidates) != len(self.candidates):
            raise ValueError("IDs de evidencia duplicados")
        components = {c.component_id for c in item.components} if item else set()
        for candidate in self.candidates:
            if candidate.end > len(self.text_original):
                raise ValueError("Offset fuera del texto original")
            if self.text_original[candidate.start : candidate.end] != candidate.text:
                raise ValueError("Span no coincide con el texto original")
            if candidate.component_ref is not None and candidate.component_ref not in components:
                raise ValueError("Componente de evidencia inexistente")
        if item:
            for component in item.components:
                self._check_ids(component.evidence_ids, candidates)
            values = [
                *item.dimensions,
                *item.thicknesses,
                *item.accessories,
                item.primary_color,
                item.secondary_color,
                item.price,
            ]
            for value in values:
                if isinstance(value, Referenced):
                    self._check_ids(value.evidence_ids, candidates)
                    if value.component_ref is not None and value.component_ref not in components:
                        raise ValueError("Componente de campo inexistente")
            self._check_ids(item.unresolved, candidates)
            if any(candidates[c].decision != "UNRESOLVED" for c in item.unresolved):
                raise ValueError("unresolved solo admite candidatos pendientes")
        return self

    @staticmethod
    def _check_ids(ids: list[str], candidates: dict[str, Candidate]) -> None:
        if len(ids) != len(set(ids)) or any(i not in candidates for i in ids):
            raise ValueError("Referencias de evidencia inexistentes o duplicadas")
