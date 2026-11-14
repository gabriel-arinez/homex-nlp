"""Comparación pura de propuestas IA/revisadas para el futuro backend HITL."""

from __future__ import annotations

from typing import Any

from homex_nlp.contracts.review import FieldDifference, ReviewComparison


def compare_fields(original: dict[str, Any], reviewed: dict[str, Any]) -> ReviewComparison:
    """Compara valores proporcionados por el llamador; no aplica permisos ni persiste."""
    differences: list[FieldDifference] = []
    keys = sorted(set(original) | set(reviewed))
    for key in keys:
        before, after = original.get(key), reviewed.get(key)
        if before == after:
            continue
        if key not in original:
            change = "ADDED"
        elif key not in reviewed:
            change = "REMOVED"
        else:
            change = "CORRECTED"
        differences.append(
            FieldDifference(path=f"/{key}", change=change, original=before, reviewed=after)
        )
    evaluable = len(original)
    corrected = sum(item.change == "CORRECTED" for item in differences)
    added = sum(item.change == "ADDED" for item in differences)
    removed = sum(item.change == "REMOVED" for item in differences)
    precision = (
        None
        if evaluable == 0
        else f"{(evaluable - corrected - removed) / evaluable:.12f}".rstrip("0").rstrip(".")
    )
    return ReviewComparison(
        metric_version="field-comparison-v1",
        evaluable_fields=evaluable,
        corrected_fields=corrected,
        added_fields=added,
        removed_fields=removed,
        field_precision=precision,
        item_equal=not differences,
        differences=differences,
    )
