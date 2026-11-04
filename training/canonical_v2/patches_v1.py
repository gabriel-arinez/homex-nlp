"""Reversible development-only patches for literal, objective V1 omissions.

Does not apply patches to V1, change split groups, approve annotations or emit test rows.
"""

import argparse
import json
import re
from copy import deepcopy
from decimal import Decimal
from hashlib import sha256
from pathlib import Path

from training.audit_prf04 import FAMILIAS
from training.corpus import read_jsonl


def patches(row):
    if row["split"] not in {"train", "dev"}:
        return None
    text = row["text"]
    if sha256(text.encode()).hexdigest() != row["text_sha256"]:
        raise ValueError("SOURCE_TEXT_HASH")
    after = deepcopy(row["entities"])
    operations, facts = [], []
    for index, (start, end, label) in enumerate(row["entities"]):
        head = text.rfind("Membrana protectora ", 0, start)
        if (
            label == "ACCESORIO"
            and text[start:end] == "incluida con el piso"
            and head >= 0
            and text[head:start] == "Membrana protectora "
        ):
            after[index][0] = head
            operations.append(
                {
                    "path": f"/entities/{index}/0",
                    "before": start,
                    "after": head,
                    "rule": "MEMBRANA_INCLUDE_EXPLICIT_NOUN",
                    "evidence": {"start": head, "end": end, "literal": text[head:end]},
                }
            )
    for match in re.finditer(r"\bdescuento de línea (Bs|USD) (\d[\d.,]*)", text):
        raw = match[2]
        # V1 literal grammar: comma decimal, dot thousands; no extrapolation to spoken prices.
        if not re.fullmatch(r"(?:\d+|\d{1,3}(?:\.\d{3})+),\d{2}|\d+", raw):
            facts.append(
                {
                    "kind": "AMBIGUOUS_DISCOUNT_LITERAL_REQUIRES_REVIEW",
                    "start": match.start(2),
                    "end": match.end(2),
                    "literal": raw,
                }
            )
            continue
        value = Decimal(raw.replace(".", "").replace(",", ".")) if "," in raw else Decimal(raw)
        facts.append(
            {
                "kind": "EXPLICIT_LINE_DISCOUNT",
                "value": str(value),
                "currency_literal": match[1],
                "start": match.start(2),
                "end": match.end(2),
                "literal": raw,
                "rule": "V1_LITERAL_DECIMAL_NO_INFERENCE",
            }
        )
    for match in re.finditer(
        r"\b(una|dos|tres|cinco|\d+) (cajones|puertas|repisas interiores|apoyos)\b", text, re.I
    ):
        facts.append(
            {
                "kind": "INTERNAL_QUANTITY_LITERAL_REQUIRES_SCOPE_REVIEW",
                "start": match.start(),
                "end": match.end(),
                "literal": match[0],
                "commercial": False,
                "component_assignment": None,
            }
        )
    for match in re.finditer(r"\b\d+ personas\b", text):
        facts.append(
            {
                "kind": "CAPACITY_NOT_COMMERCIAL_QUANTITY",
                "start": match.start(),
                "end": match.end(),
                "literal": match[0],
                "commercial": False,
            }
        )
    # Strong invariant: only a noun-boundary extension changes entities; no text or label edits.
    for (a, b, label), (c, d, other_label) in zip(row["entities"], after):
        if b != d or label != other_label or c > a:
            raise ValueError("UNEXPECTED_TRANSFORMATION")
    previous = 0
    for start, end, _ in after:
        if start < previous or not 0 <= start < end <= len(text):
            raise ValueError("PATCH_OVERLAP_OR_BOUNDS")
        previous = end
    return {
        "parent_record_id": row["id"],
        "parent_sha256": row["text_sha256"],
        "split": row["split"],
        "origin": row["origin"],
        "operations": operations,
        "entities_before": row["entities"] if operations else None,
        "entities_after": after if operations else None,
        "technical_facts": facts,
        "human_reviewed": False,
        "status": "PENDIENTE_REVISION_HUMANA",
        "source_document_id": None,
        "reviewer": None,
        "rollback": "DISCARD_OVERLAY_V1_UNCHANGED",
    }


def build(root=Path("data")):
    rows = [r for family in FAMILIAS for _, r in read_jsonl(root / "corpus" / f"{family}.jsonl")]
    overlays = [p for row in rows if (p := patches(row)) is not None]
    return {
        "format": "homex-development-overlay-1",
        "active": False,
        "human_gold": False,
        "records_reviewed_mechanically": len(overlays),
        "test_records_emitted": 0,
        "entity_patch_records": sum(bool(p["operations"]) for p in overlays),
        "fact_records": sum(bool(p["technical_facts"]) for p in overlays),
        "records": overlays,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("OUTPUT_EXISTS")
    args.output.write_text(json.dumps(build(), ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
