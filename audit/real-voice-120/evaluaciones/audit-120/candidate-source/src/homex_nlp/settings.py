"""Configuración inyectada: sin leer .env, crear directorios o cargar modelos."""

from pathlib import Path
from typing import Annotated, Literal, Mapping

from pydantic import Field, StringConstraints, model_validator

from homex_nlp.contracts.base import Contract, NonBlank

Sha256 = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]


class RuntimeSettings(Contract):
    schema_version: Literal["1.0"] = "1.0"
    nlp_mode: Literal["RULES_ONLY", "HYBRID"]
    ner_model_path: Path | None = None
    ner_model_sha256: Sha256 | None = None
    domain_profile_version: NonBlank | None = None
    asr_model_path: Path | None = None
    asr_device: Literal["cpu", "cuda"] = "cpu"
    asr_compute_type: Literal["int8", "float16", "float32"] = "int8"
    asr_cpu_threads: Annotated[int, Field(ge=1, le=64)] = 2

    @model_validator(mode="after")
    def configuration(self):
        for path in (self.ner_model_path, self.asr_model_path):
            if path is not None and not path.is_absolute():
                raise ValueError("Las rutas deben ser absolutas e independientes del CWD")
        if self.nlp_mode == "HYBRID":
            if self.ner_model_path is None or self.ner_model_sha256 is None:
                raise ValueError("HYBRID requiere ruta y hash del modelo")
        elif self.ner_model_path is not None or self.ner_model_sha256 is not None:
            raise ValueError("RULES_ONLY no configura un modelo NER")
        if self.asr_device == "cpu" and self.asr_compute_type == "float16":
            raise ValueError("float16 no forma parte del perfil CPU soportado")
        return self

    @classmethod
    def from_environment(cls, environment: Mapping[str, str]) -> "RuntimeSettings":
        """El llamador decide si pasar os.environ o un mapping de pruebas."""
        fields = {
            "HOMEX_NLP_MODE": "nlp_mode",
            "HOMEX_NER_MODEL_PATH": "ner_model_path",
            "HOMEX_NER_MODEL_SHA256": "ner_model_sha256",
            "HOMEX_DOMAIN_PROFILE_VERSION": "domain_profile_version",
            "HOMEX_ASR_MODEL_PATH": "asr_model_path",
            "HOMEX_ASR_DEVICE": "asr_device",
            "HOMEX_ASR_COMPUTE_TYPE": "asr_compute_type",
            "HOMEX_ASR_CPU_THREADS": "asr_cpu_threads",
        }
        values: dict[str, object] = {}
        for key, field in fields.items():
            if key not in environment:
                continue
            value = environment[key]
            if not value.strip():
                raise ValueError(f"Variable vacía: {key}")
            if field.endswith("_path"):
                values[field] = Path(value)
            elif field == "asr_cpu_threads":
                if not value.isascii() or not value.isdecimal():
                    raise ValueError("HOMEX_ASR_CPU_THREADS debe ser entero decimal")
                values[field] = int(value)
            else:
                values[field] = value
        return cls.model_validate(values)
