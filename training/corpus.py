"""Formato canónico y operaciones puras para los corpus anotados."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Iterable
from pathlib import Path
from typing import Any

SOURCE_FILES = {
    name: Path(f"data/corpus/{name}.jsonl")
    for name in ("muebles_pedido", "sillas", "pisos_flotantes", "otros_productos")
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
