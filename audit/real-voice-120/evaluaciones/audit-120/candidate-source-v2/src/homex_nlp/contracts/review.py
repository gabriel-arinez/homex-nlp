"""Contrato de comparación pura; F01 no implementa el algoritmo de evaluación."""

from typing import Literal

from pydantic import Field, JsonValue, model_validator

from homex_nlp.contracts.base import Contract, Count, NonBlank, Ratio


class FieldDifference(Contract):
    path: NonBlank
    change: Literal["CORRECTED", "ADDED", "REMOVED"]
    original: JsonValue = None
    reviewed: JsonValue = None


class ReviewComparison(Contract):
    schema_version: Literal["1.0"] = "1.0"
    metric_version: NonBlank
    evaluable_fields: Count
    corrected_fields: Count
    added_fields: Count
    removed_fields: Count
    field_precision: Ratio | None
    item_equal: bool | None
    differences: list[FieldDifference] = Field(default_factory=list)

    @model_validator(mode="after")
    def denominator(self):
        if self.corrected_fields + self.removed_fields > self.evaluable_fields:
            raise ValueError("Correcciones/eliminaciones exceden campos originales evaluables")
        if self.evaluable_fields == 0 and self.field_precision is not None:
            raise ValueError("Sin denominador, precisión debe ser null")
        counts = {
            kind: sum(d.change == kind for d in self.differences)
            for kind in ("CORRECTED", "ADDED", "REMOVED")
        }
        if [counts[k] for k in counts] != [
            self.corrected_fields,
            self.added_fields,
            self.removed_fields,
        ]:
            raise ValueError("Conteos no coinciden con diferencias")
        return self
