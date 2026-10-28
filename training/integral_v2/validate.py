"""Verify frozen corpus, review membership, source anchors and split constraints."""

import argparse
import json
from collections import Counter
from pathlib import Path

from training.canonical_v2.io import digest, read
from training.canonical_v2.validate import ROOT, normalized
from training.integral_v2.review import seal, validate_review


def validate_bundle(bundle, *, training=False):
    manifest = json.loads((bundle / "manifest.json").read_text())
    sealed = json.loads((bundle / "sha256.json").read_text())
    if any(digest((bundle / p).read_bytes()) != value for p, value in sealed.items()):
        raise ValueError("FROZEN_BUNDLE_CHANGED")
    baseline = json.loads((bundle / "baseline_sha256.json").read_text())
    if any(digest((ROOT / p).read_bytes()) != v for p, v in baseline.items()):
        raise ValueError("HISTORICAL_V1_CHANGED")
    reviews = read(bundle / "adjudications.jsonl")
    certs = json.loads((bundle / "certificates.json").read_text())
    items = read(bundle / "sources/document_items.jsonl")
    by_id = {i["id"]: i for i in items}
    expected_reviews = {}
    for r in reviews:
        validate_review(by_id[r["item_id"]], r, certs[r["item_id"]])
        if r["decision"] == "APTO":
            expected_reviews[r["item_id"]] = r
    oral = read(bundle / "oral_reviews.jsonl")
    for e in oral:
        validate_review(e["item"], e["review"], e["certificate"])
        expected_reviews[e["item"]["id"]] = e["review"]
    rows = read(bundle / "records.jsonl")
    refs = {r["id"]: r for r in read(bundle / "expected.jsonl")}
    if (
        len(rows) != len({r["id"] for r in rows})
        or set(refs) != set(expected_reviews)
        or set(refs) != {r["id"] for r in rows}
    ):
        raise ValueError("SUPERVISED_MEMBERSHIP")
    groups = {}
    texts = {}
    fingerprints = {}
    assignments = json.loads((bundle / "assignments.json").read_text())
    for row in rows:
        review = expected_reviews[row["id"]]
        if seal(row["entities"]) != seal(review["entities"]) or row["text_sha256"] != digest(
            row["text"]
        ):
            raise ValueError("ENTITY_OR_TEXT_CHANGED")
        ref = refs[row["id"]]
        if seal(ref["expected"]) != seal(review["expected"]) or seal(ref["facts"]) != seal(
            review["facts"]
        ):
            raise ValueError("COMMERCIAL_REFERENCE_CHANGED")
        if row["split"] not in ("train", "dev", "test") or row["human_reviewed"] is not False:
            raise ValueError("FALSE_SPLIT_OR_HUMAN_GOLD")
        if (
            row["leakage_group"] != assignments[row["id"]]["leakage_group"]
            or row["split"] != assignments[row["id"]]["split"]
        ):
            raise ValueError("SPLIT_ASSIGNMENT_CHANGED")
        for lookup, key in (
            (groups, row["leakage_group"]),
            (texts, row["text_sha256"]),
            (fingerprints, normalized(row["text"])),
        ):
            if key in lookup and lookup[key] != row["split"]:
                raise ValueError("CROSS_SPLIT_LEAKAGE")
            lookup[key] = row["split"]
    for entry in oral:
        for parent in [entry["parent_id"], *entry.get("additional_parent_ids", [])]:
            if assignments[entry["item"]["id"]] != assignments[parent]:
                raise ValueError("PARAPHRASE_LEAKAGE")
    if training and not manifest["training_ready"]:
        raise ValueError("TRAINING_GATE_NOT_READY")
    return {
        "valid": True,
        "records": len(rows),
        "splits": dict(Counter(r["split"] for r in rows)),
        "baseline_files": len(baseline),
        "sealed_files": len(sealed),
        "human_gold": False,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("bundle", type=Path)
    parser.add_argument("--training", action="store_true")
    args = parser.parse_args()
    print(json.dumps(validate_bundle(args.bundle, training=args.training)))


if __name__ == "__main__":
    main()
