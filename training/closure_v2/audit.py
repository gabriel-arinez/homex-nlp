"""Audit V1 without emitting test text, labels, IDs or per-test findings."""

import argparse
import json
import re
import unicodedata
from collections import Counter, defaultdict
from hashlib import sha256
from pathlib import Path

import spacy

from training.audit_prf04 import FAMILIAS
from training.corpus import read_jsonl


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def fingerprint(text):
    text = "".join(
        c for c in unicodedata.normalize("NFKD", text.casefold()) if not unicodedata.combining(c)
    )
    return " ".join(re.findall(r"\w+", text))


def audit(root=Path("data")):
    labels = set(json.loads((root / "manifests/prf04_labels.json").read_text())["labels"])
    tokenizer = spacy.blank("es")
    counts, origins, quality = Counter(), Counter(), Counter()
    groups = {
        k: defaultdict(set)
        for k in ("id", "family_id", "proforma_id", "exact", "normalized", "prefix65", "source_id")
    }
    files, families, errors, review = {}, {}, Counter(), []
    seen_ids = set()
    coverage = defaultdict(Counter)
    for family in FAMILIAS:
        source = root / "corpus" / f"{family}.jsonl"
        split_path = root / "splits" / f"{family}.json"
        expected_path = root / "expected" / f"{family}.jsonl"
        for path in (source, split_path, expected_path):
            files[str(path.relative_to(root))] = digest(path)
        split = json.loads(split_path.read_text())
        targets_list = [r for _, r in read_jsonl(expected_path)]
        targets = {r["id"]: r for r in targets_list}
        assignments = split["assignments"]
        assigned = [i for values in assignments.values() for i in values]
        errors["duplicate_assignment"] += len(assigned) - len(set(assigned))
        errors["duplicate_expected_id"] += len(targets_list) - len(targets)
        errors["unsealed_or_hash"] += not (
            split["sealed"] and split["corpus_sha256"] == digest(source)
        )
        rows = [r for _, r in read_jsonl(source)]
        errors["assignment_inventory"] += set(assigned) != {r["id"] for r in rows}
        errors["expected_inventory"] += set(targets) != {r["id"] for r in rows}
        families[family] = dict(Counter(r["split"] for r in rows))
        for row in rows:
            partition = row["split"]
            if row["id"] in seen_ids:
                errors["duplicate_id"] += 1
            seen_ids.add(row["id"])
            counts[partition] += 1
            origins[row.get("origin")] += 1
            quality[row.get("metadata", {}).get("calidad")] += 1
            text = row["text"]
            flags = []

            def flag(code):
                errors[code] += 1
                flags.append(code)

            if row["id"] not in assignments.get(partition, []):
                flag("split_mismatch")
            if row["text_sha256"] != sha256(text.encode()).hexdigest():
                flag("text_hash")
            if row["category"] != family:
                flag("category")
            if any(
                not row.get(k)
                for k in ("id", "family_id", "proforma_id", "source_id", "source_line", "origin")
            ):
                flag("provenance_missing")
            target = targets.get(row["id"], {})
            if target.get("text_sha256") != row["text_sha256"]:
                flag("expected_hash")
            for key in ("id", "family_id", "proforma_id", "source_id"):
                groups[key][row.get(key)].add(partition)
            for key, value in (
                ("exact", text),
                ("normalized", fingerprint(text)),
                ("prefix65", text[:65]),
            ):
                groups[key][value].add(partition)
            previous, seen = 0, set()
            doc = tokenizer.make_doc(text)
            for entity in row["entities"]:
                if not isinstance(entity, list) or len(entity) != 3:
                    flag("span_shape")
                    continue
                start, end, label = entity
                if (
                    type(start) is not int
                    or type(end) is not int
                    or not 0 <= start < end <= len(text)
                ):
                    flag("span_bounds")
                    continue
                if label not in labels:
                    flag("label")
                if start < previous:
                    flag("overlap_or_order")
                previous = end
                if tuple(entity) in seen:
                    flag("duplicate_span")
                seen.add(tuple(entity))
                if doc.char_span(start, end, alignment_mode="strict") is None:
                    flag("token_alignment")
                # Test label distribution deliberately not exported.
                if partition != "test":
                    coverage[partition][label] += 1
            if partition != "test":
                internal = bool(
                    re.search(r"\b\d+\s+(?:cajones|puertas|repisas|divisiones)\b", text, re.I)
                )
                review.append(
                    {
                        "id": row["id"],
                        "parent_sha256": row["text_sha256"],
                        "split": partition,
                        "origin": row["origin"],
                        "status": "PENDIENTE_REVISION_HUMANA",
                        "formal_errors": flags,
                        "internal_quantity_signal": internal,
                        "document_link": "NO_VERIFICADO",
                        "reference_status": target.get("revision"),
                        "operation": "SIDECAR_ONLY_NO_CONTENT_CHANGE",
                    }
                )
    crossing = {
        key: sum(len(splits) > 1 for splits in values.values()) for key, values in groups.items()
    }
    report = {
        "format": "homex-closure-audit-1",
        "files_sha256": files,
        "records": sum(counts.values()),
        "splits": dict(counts),
        "families": families,
        "origin": dict(origins),
        "quality": dict(quality),
        "unique_proformas": len(groups["proforma_id"]),
        "unique_families": len(groups["family_id"]),
        "cross_split_groups": crossing,
        "exact_duplicate_records": sum(counts.values()) - len(groups["exact"]),
        "normalized_duplicate_records": sum(counts.values()) - len(groups["normalized"]),
        "formal_errors": {k: v for k, v in errors.items() if v},
        "development_entity_counts": {k: dict(sorted(v.items())) for k, v in coverage.items()},
        "test_policy": "MECHANICAL_AGGREGATES_ONLY_NO_SCORING_OR_CURATION",
        "similarity_policy": "prefix65/source_id are alerts, not proven semantic leakage",
        "human_gold": False,
        "promotion": False,
    }
    return report, review


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report, review = audit(args.data)
    args.output.mkdir(parents=True, exist_ok=False)
    for name, value in (("audit.json", report), ("development_review.json", review)):
        (args.output / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    print(
        json.dumps(
            {
                "records": report["records"],
                "splits": report["splits"],
                "formal_errors": report["formal_errors"],
            }
        )
    )
    return int(bool(report["formal_errors"]))


if __name__ == "__main__":
    raise SystemExit(main())
