"""Strict transport contract. External acts remain external, not authenticated by flags."""

import hashlib
import re
from datetime import date
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

ID = Annotated[str, Field(pattern=r"^[A-Z0-9][A-Z0-9_-]{1,63}$")]
SHA = Annotated[str, Field(pattern=r"^[a-f0-9]{64}$")]


def sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, allow_inf_nan=False)


class Text(Strict):
    text: str
    sha256: SHA

    @model_validator(mode="after")
    def digest(self):
        if sha(self.text) != self.sha256:
            raise ValueError("TEXT_DIGEST")
        return self


class Span(Strict):
    start: int = Field(ge=0)
    end: int = Field(gt=0)
    label: Literal[
        "ACABADO",
        "ACCESORIO",
        "ALTO",
        "ANCHO",
        "APOYABRAZOS",
        "CABECERA",
        "CANTIDAD",
        "CLASE_RESISTENCIA",
        "COLOR",
        "COMPONENTE",
        "DESCUENTO",
        "DIAMETRO",
        "ERGONOMIA",
        "ESPESOR",
        "LARGO",
        "MATERIAL",
        "OBSERVACION",
        "PRECIO_TOTAL",
        "PRECIO_UNITARIO",
        "PRODUCTO",
        "PROFUNDIDAD",
        "SISTEMA",
        "SOPORTE_LUMBAR",
        "UNIDAD_MEDIDA",
    ]


class Ner(Strict):
    coordinate: Literal["asr", "faithful"]
    text_sha256: SHA
    spans: list[Span]
    coverage: Literal["complete", "partial"] = "complete"


class Fact(Strict):
    scope: ID  # ITEM, CONDITIONS or independently defined component/accessory ID
    field: Literal[
        "product",
        "sold_quantity",
        "internal_quantity",
        "capacity",
        "unit",
        "length",
        "width",
        "height",
        "thickness",
        "material",
        "color",
        "accessory_quantity",
        "unit_price",
        "total_price",
        "discount",
        "currency",
    ]
    value: str = Field(min_length=1)
    unit: Literal["mm", "cm", "m", "m2", "PIEZA", "JUEGO", "BARRA", "PERCENT"] | None = None
    evidence: Literal["explicit", "conditions", "human_adjudicated", "inferred"] = "explicit"

    @model_validator(mode="after")
    def semantics(self):
        numeric = {
            "sold_quantity",
            "internal_quantity",
            "capacity",
            "length",
            "width",
            "height",
            "thickness",
            "accessory_quantity",
            "unit_price",
            "total_price",
            "discount",
        }
        if self.field in numeric:
            if not re.fullmatch(r"-?\d+(?:[.,]\d+)?", self.value):
                raise ValueError("AMBIGUOUS_DECIMAL")
            if Decimal(self.value.replace(",", ".")) < 0:
                raise ValueError("NEGATIVE_VALUE")
        if self.field in {"unit_price", "total_price", "discount"} and self.evidence == "inferred":
            raise ValueError("INFERRED_PRICE")
        if self.field in {"length", "width", "height", "thickness"}:
            if self.unit not in {None, "mm", "cm", "m"}:
                raise ValueError("DIMENSION_UNIT")
        elif self.field == "discount":
            if self.unit not in {None, "PERCENT"}:
                raise ValueError("DISCOUNT_UNIT")
        elif self.unit is not None:
            raise ValueError("UNEXPECTED_VALUE_UNIT")
        if self.field == "currency" and (
            self.scope != "CONDITIONS" or self.value not in {"BOB", "USD"}
        ):
            raise ValueError("CURRENCY_SCOPE")
        return self


class Commercial(Strict):
    scopes: dict[ID, Literal["item", "component", "accessory", "conditions"]]
    facts: list[Fact]
    coverage: Literal["complete", "partial"] = "complete"
    reviewed_keys: list[str] = Field(
        default=[],
        description="Adjudicated keys including explicit negatives in complete references; exclusive scoring scope for partial references.",
    )

    @model_validator(mode="after")
    def scope(self):
        if self.scopes.get("ITEM") != "item" or self.scopes.get("CONDITIONS") != "conditions":
            raise ValueError("ROOT_SCOPES")
        if any(
            kind in {"item", "conditions"} and key not in {"ITEM", "CONDITIONS"}
            for key, kind in self.scopes.items()
        ):
            raise ValueError("ONE_COMMERCIAL_ITEM")

        def check_scope(scope, field):
            kind = self.scopes[scope]
            if (
                field
                in {
                    "product",
                    "sold_quantity",
                    "unit",
                    "unit_price",
                    "total_price",
                    "discount",
                    "capacity",
                }
                and kind != "item"
            ):
                raise ValueError("COMMERCIAL_SCOPE")
            if field == "currency" and scope != "CONDITIONS":
                raise ValueError("CURRENCY_SCOPE")
            if field == "accessory_quantity" and kind != "accessory":
                raise ValueError("ACCESSORY_SCOPE")
            if field == "internal_quantity" and kind not in {"component", "accessory"}:
                raise ValueError("RELATION_SCOPE")
            # PRF-03 general attributes are scoped to ITEM, not a fabricated component.
            if field in {"material", "color", "thickness"} and kind not in {
                "item",
                "component",
                "accessory",
            }:
                raise ValueError("RELATION_SCOPE")

        keys = []
        for f in self.facts:
            if f.scope not in self.scopes:
                raise ValueError("UNKNOWN_COMPONENT_SCOPE")
            check_scope(f.scope, f.field)
            keys.append(f.scope + ":" + f.field)
        if len(keys) != len(set(keys)):
            raise ValueError("DUPLICATE_FACT")
        if self.coverage == "partial" and not set(keys) <= set(self.reviewed_keys):
            raise ValueError("PARTIAL_REVIEW_KEYS")
        if len(self.reviewed_keys) != len(set(self.reviewed_keys)):
            raise ValueError("DUPLICATE_REVIEW_KEY")
        for key in self.reviewed_keys:
            parts = key.split(":")
            if (
                len(parts) != 2
                or parts[0] not in self.scopes
                or parts[1] not in Fact.model_fields["field"].annotation.__args__
            ):
                raise ValueError("REVIEW_SCOPE")
            check_scope(parts[0], parts[1])
        return self


class Reference(Strict):
    origin: Literal["independent_human", "synthetic_fixture"]
    faithful: Text | None = None
    ner: Ner | None = None
    commercial: Commercial | None = None
    review_status: Literal["PENDING", "human_declared", "human_verified"] = "PENDING"
    reviewer_ids: list[ID] = []
    attestation_ids: list[ID] = []
    arbitration: Literal["PENDING", "DISPUTED", "RESOLVED"] = "PENDING"


class Engine(Strict):
    engine_id: ID
    commit: Annotated[str, Field(pattern=r"^[a-f0-9]{40}$")]
    wheel_sha256: SHA
    version: str = Field(min_length=1, max_length=64)
    rules_version: ID
    coordinate: Literal["asr", "faithful"]
    text_sha256: SHA
    ner: Ner | None = None
    commercial: Commercial | None = None


BOUNDARIES = {
    "queue": ("queued", "worker_started"),
    "asr": ("asr_started", "asr_done"),
    "nlp": ("nlp_started", "nlp_done"),
    "projection": ("projection_started", "projection_done"),
    "frontend": ("frontend_received", "form_usable"),
    "end_to_form": ("recording_end", "form_usable"),
}


class Timing(Strict):
    metric: Literal["queue", "asr", "nlp", "projection", "frontend", "end_to_form"]
    unit: Literal["s", "ms"]
    start_boundary: str
    end_boundary: str
    start: float
    end: float
    clock: Literal["monotonic_common", "synchronized_common"]

    @model_validator(mode="after")
    def interval(self):
        if (self.start_boundary, self.end_boundary) != BOUNDARIES[
            self.metric
        ] or not 0 <= self.start <= self.end:
            raise ValueError("TIMING_BOUNDARIES")
        return self


class Productivity(Strict):
    case_id: ID
    order: Literal["manual_first", "assisted_first"]
    manual_seconds: float | None = Field(default=None, gt=0)
    assisted_seconds: float | None = Field(default=None, gt=0)
    corrections: int | None = Field(default=None, ge=0)
    commercial_validated: bool = False
    exclusion: Literal["INCOMPLETE", "NOT_VALIDATED", "NONE"] = "INCOMPLETE"
    seller_corrections: list[Fact] = []


class Audio(Strict):
    private_ref: ID  # opaque ID; operator mapping stays outside batch
    sha256: SHA


class Consent(Strict):
    human_declared: bool = False
    act_id: ID | None = None
    use_policy_id: ID | None = None
    retention_policy_id: ID | None = None
    # human_verified is calculated from an external registry; never accepted as a flag.


class Provenance(Strict):
    source_id: ID
    template_id: ID
    speaker_id: ID
    partition: Literal["QUARANTINE", "TRAIN", "DEV", "EXTERNAL_CANDIDATE", "PREVIOUSLY_OPEN"]
    independence: Literal["PENDING", "human_declared"] = "PENDING"
    access_act_id: ID | None = None


class Diagnosis(Strict):
    cause: Literal["ASR", "NLP", "projection", "UI", "human_review", "unknown"] = "unknown"
    evidence_ids: list[ID] = []  # external evidence IDs, never inferred by scorer

    @model_validator(mode="after")
    def evidence(self):
        if self.cause != "unknown" and not self.evidence_ids:
            raise ValueError("CAUSE_WITHOUT_EVIDENCE")
        return self


class Session(Strict):
    batch_id: ID
    session_id: ID
    case_id: ID
    source_type: Literal["ASR_REAL", "SINTETICO_PRUEBA"]
    capture_mode: Literal["offline_audio", "ephemeral_audio", "imported_asr", "synthetic_fixture"]
    consent: Consent
    provenance: Provenance
    audio: Audio | None = None
    asr: Text
    reference: Reference | None = None
    engines: list[Engine] = []
    timings: list[Timing] = []
    temperature: Literal["cold", "warm", "unknown"] = "unknown"
    hardware_class: Literal["CPU", "GPU", "unknown"] = "unknown"
    condition: Literal["quiet", "noise", "unknown"] = "unknown"
    language: Literal["es", "en", "other"] = "es"
    productivity: Productivity | None = None
    diagnosis: Diagnosis = Diagnosis()

    @model_validator(mode="after")
    def links(self):
        if self.source_type == "ASR_REAL":
            c = self.consent
            if (
                not c.human_declared
                or not all((c.act_id, c.use_policy_id, c.retention_policy_id))
                or self.capture_mode == "synthetic_fixture"
            ):
                raise ValueError("REAL_REQUIRES_EXTERNAL_CONSENT_DECLARATION")
            if self.reference and self.reference.origin != "independent_human":
                raise ValueError("MODEL_OR_SYNTHETIC_REFERENCE_FOR_REAL")
        elif self.capture_mode != "synthetic_fixture" or (
            self.reference and self.reference.origin != "synthetic_fixture"
        ):
            raise ValueError("SYNTHETIC_LABEL")
        texts = {"asr": self.asr}
        if self.reference and self.reference.faithful:
            texts["faithful"] = self.reference.faithful
        annotations = [e.ner for e in self.engines if e.ner]
        if self.reference and self.reference.ner:
            annotations.append(self.reference.ner)
        for n in annotations:
            text = texts.get(n.coordinate)
            if text is None or text.sha256 != n.text_sha256:
                raise ValueError("NER_TEXT_COORDINATE")
            previous = -1
            for span in sorted(n.spans, key=lambda s: (s.start, s.end)):
                if not previous <= span.start < span.end <= len(text.text):
                    raise ValueError("INVALID_OR_OVERLAPPING_SPAN")
                previous = span.end
        for e in self.engines:
            if (
                e.coordinate not in texts
                or e.text_sha256 != texts[e.coordinate].sha256
                or (
                    e.ner
                    and (e.ner.coordinate != e.coordinate or e.ner.text_sha256 != e.text_sha256)
                )
            ):
                raise ValueError("ENGINE_TEXT_COORDINATE")
        if len({e.engine_id for e in self.engines}) != len(self.engines):
            raise ValueError("DUPLICATE_ENGINE")
        if len({t.metric for t in self.timings}) != len(self.timings):
            raise ValueError("DUPLICATE_TIMING")
        # Shared clock landmarks must agree even across s/ms intervals.
        landmarks = {}
        clocks = {t.clock for t in self.timings}
        if len(clocks) > 1:
            raise ValueError("MIXED_CLOCKS")
        for t in self.timings:
            for key, val in ((t.start_boundary, t.start), (t.end_boundary, t.end)):
                seconds = Decimal(str(val)) / (1000 if t.unit == "ms" else 1)
                if key in landmarks and landmarks[key] != seconds:
                    raise ValueError("INCONSISTENT_LANDMARK")
                landmarks[key] = seconds
        ordered = (
            "recording_end",
            "queued",
            "worker_started",
            "asr_started",
            "asr_done",
            "nlp_started",
            "nlp_done",
            "projection_started",
            "projection_done",
            "frontend_received",
            "form_usable",
        )
        known = [landmarks[key] for key in ordered if key in landmarks]
        if known != sorted(known):
            raise ValueError("INCONSISTENT_PIPELINE_ORDER")
        if self.productivity and self.productivity.case_id != self.case_id:
            raise ValueError("UNPAIRED_CASE")
        return self


class Batch(Strict):
    schema_version: Literal["field-benchmark-1"]
    batch_id: ID
    frozen_date: date
    sessions: list[Session]

    @model_validator(mode="after")
    def unique(self):
        ids = [s.session_id for s in self.sessions]
        if len(ids) != len(set(ids)) or any(s.batch_id != self.batch_id for s in self.sessions):
            raise ValueError("DUPLICATE_ID_OR_BATCH")
        return self
