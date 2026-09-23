"""Formato canónico y operaciones puras para los corpus anotados."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Iterable
from pathlib import Path
from typing import Any

SOURCE_FILES = {
    "homex_original": Path("data/raw/homex_original.jsonl"),
    "catalogo_sillas": Path("data/raw/catalogo_sillas_original.jsonl"),
}

# Correcciones exclusivamente técnicas, verificadas contra la fuente antes de
# aplicar. Las anotaciones de producto incluyen ``L.`` porque el tokenizador de
# spaCy considera la abreviatura como un único token.
OFFSET_PATCHES: dict[tuple[str, int, int, str], tuple[int, int, str]] = {
    ("homex_original", 22, 87, "PROFUNDIDAD"): (87, 95, "puntuación final fuera del token"),
    ("homex_original", 32, 103, "PROFUNDIDAD"): (103, 111, "puntuación final fuera del token"),
    ("homex_original", 52, 94, "PROFUNDIDAD"): (94, 102, "puntuación final fuera del token"),
    ("homex_original", 62, 15, "PRODUCTO"): (15, 31, "abreviatura L. debe conservarse completa"),
    ("homex_original", 72, 83, "PROFUNDIDAD"): (83, 91, "puntuación final fuera del token"),
    ("homex_original", 102, 17, "PRODUCTO"): (17, 33, "abreviatura L. debe conservarse completa"),
    ("homex_original", 102, 94, "PROFUNDIDAD"): (94, 102, "puntuación final fuera del token"),
    ("homex_original", 112, 98, "PROFUNDIDAD"): (98, 106, "puntuación final fuera del token"),
    ("homex_original", 132, 92, "PROFUNDIDAD"): (92, 100, "puntuación final fuera del token"),
    ("homex_original", 142, 91, "PROFUNDIDAD"): (91, 99, "puntuación final fuera del token"),
    ("homex_original", 152, 98, "PROFUNDIDAD"): (98, 106, "puntuación final fuera del token"),
}


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_text(value: str) -> str:
    return sha256_bytes(value.encode("utf-8"))


def read_jsonl(path: Path) -> Iterable[tuple[int, dict[str, Any]]]:
    """Lee JSONL sin ocultar números de línea ni registros vacíos."""
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if line.strip():
            yield line_number, json.loads(line)


def source_record_id(source_id: str, line_number: int, text: str) -> str:
    """ID estable por fuente/línea/texto; no depende de la copia curada."""
    digest = sha256_text(f"{source_id}:{line_number}:{sha256_text(text)}")[:16]
    return f"{source_id}-{digest}"


def family_id(text: str, entities: list[list[Any]]) -> str:
    """Agrupa plantillas anotadas sustituyendo spans por su etiqueta.

    Es una protección conservadora contra fuga de ejemplos casi idénticos. No
    pretende ser una clasificación comercial ni sustituye una revisión humana.
    """
    rendered = text
    for start, end, label in sorted(entities, key=lambda entity: entity[0], reverse=True):
        rendered = f"{rendered[:start]} <{label}> {rendered[end:]}"
    normalized = re.sub(r"\s+", " ", rendered.lower()).strip()
    return f"family-{sha256_text(normalized)[:16]}"


def json_dump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
