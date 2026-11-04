"""Evidence-only audit: provenance, near duplicates, split support and review ledger."""

import argparse
import itertools
from collections import Counter
from pathlib import Path

from training.canonical_v2.io import digest, dump, jsonl, private_path, read
from training.canonical_v2.validate import LABELS, ROOT, normalized, validate


def grams(text):
    words = normalized(text).split()
    return {tuple(words[i : i + 4]) for i in range(len(words) - 3)}


def audit(bundle, output):
    private_path(output)
    output.mkdir(parents=True, exist_ok=False)
    rows, refs = read(bundle / "records.jsonl"), read(bundle / "expected.jsonl")
    items = read(bundle / "sources/document_items.jsonl")
    sources = read_manifest(bundle / "sources/source_manifest.json")
    source_map = {s["sha256"]: s for s in sources}
    item_map = {i["id"]: i for i in items}
    evidence_errors = []
    for row in rows:
        if row["origin"] != "DOCUMENTO_HOMEX_LITERAL":
            continue
        for source in [row["source_ref"], *row["additional_source_refs"]]:
            item = item_map[source["source_item_id"]]
            literal = item["item_text"][slice(*source["item_offset"])]
            original = bundle / "sources/originals" / source_map[source["source_sha256"]]["file"]
            raw = original.read_bytes()
            text = raw.decode("utf-8-sig")
            if (
                digest(raw) != source["source_sha256"]
                or literal != row["text"]
                or text[source["char_start"] : source["char_end"]] != literal
            ):
                evidence_errors.append(row["id"])
    risks = []
    fingerprints = {r["id"]: grams(r["text"]) for r in rows}
    for a, b in itertools.combinations(rows, 2):
        x, y = fingerprints[a["id"]], fingerprints[b["id"]]
        similarity = len(x & y) / len(x | y) if x | y else 0
        if similarity >= 0.25:
            risks.append(
                dict(
                    a=a["id"],
                    b=b["id"],
                    jaccard_4gram=similarity,
                    cross_split=a["split"] != b["split"],
                    high_risk=similarity >= 0.5,
                )
            )
    high_cross = [r for r in risks if r["cross_split"] and r["high_risk"]]
    jsonl(output / "similarity_pairs.jsonl", risks)
    public = dict(
        source_manifests=[{k: s[k] for k in ("file", "sha256", "bytes", "lines")} for s in sources],
        source_blocks=len(items),
        proformas_identified=0,
        provenance_errors=len(evidence_errors),
        high_risk_cross_split_pairs=len(high_cross),
        lower_similarity_cross_split_alerts=sum(
            r["cross_split"] and not r["high_risk"] for r in risks
        ),
        threshold_policy="Normalized numeric-masked 4grams; >=.5 high, .25-.5 lexical alert. Does not certify semantic independence.",
        validation=validate(rows, refs),
        coverage={
            s: dict(
                records=sum(r["split"] == s for r in rows),
                families=dict(Counter(r["category"] for r in rows if r["split"] == s)),
                labels={
                    label: sum(
                        e[2] == label for r in rows if r["split"] == s for e in r["entities"]
                    )
                    for label in LABELS
                },
                groups=len({r["leakage_group"] for r in rows if r["split"] == s}),
                lengths=length_summary([len(r["text"]) for r in rows if r["split"] == s]),
            )
            for s in ("train", "dev", "test")
        },
        missing_train_labels=[
            label
            for label in LABELS
            if not any(e[2] == label for r in rows if r["split"] == "train" for e in r["entities"])
        ],
        protected_test_ids=98,
        canonical_test_records=0,
        external_records=0,
        human_reviewed=0,
    )
    # Every history row gets a disposition. Metadata-only for frozen test.
    history = read(ROOT / "data/canonical_v2/historical_decisions.jsonl")
    old = {r["v1_id"]: r for r in history}
    matrix = read(bundle / "v1_reconciliation.jsonl")
    for r in matrix:
        r["rc1_proposal"] = old[r["id"]]
        r["rc1_resolution"] = "ARCHIVED_NOT_APPLIED_TO_V1; use objective 49-span overlay separately"
    jsonl(output / "v1_reconciliation_complete.jsonl", matrix)
    ledger = []
    for row in rows:
        ledger.append(
            dict(
                id=row["id"],
                state="CORREGIDO" if row.get("canonical_corrections") else "APROBADO",
                reason="Technical closed-scope annotation, not human gold",
                human_reviewed=False,
                text_sha256=row["text_sha256"],
            )
        )
    ledger += [
        dict(
            id=i["id"],
            state="PENDIENTE",
            reason="Ambiguous source; preserve literal, no speculative repair",
            human_reviewed=False,
        )
        for i in read(bundle / "sources/document_quarantine.jsonl")
    ]
    jsonl(output / "review_ledger.jsonl", ledger)
    public["review_states"] = dict(Counter(r["state"] for r in ledger))
    public["historical_rc1_operations"] = dict(Counter(r["operation"] for r in history))
    public["historical_v1_dispositions"] = dict(Counter(r["decision"] for r in matrix))
    public["known_limits"] = [
        "Literal fragments are not complete quotation specifications",
        "RC1/RC2 and historical dev already observed; no blind test",
        "Semantic embedding independence not established",
        "48-case historic pilot not recovered; RC1 40 oral cases differ",
        "V1 synthetic templates share linguistic source despite original ID split",
        "No domain-human sign-off or real voice generalization claim",
    ]
    public["valid"] = not evidence_errors and not high_cross and public["validation"]["valid"]
    dump(output / "audit.json", public)
    if not public["valid"]:
        raise ValueError("AUDIT_FAILED")
    return public


def read_manifest(path):
    import json

    return json.loads(path.read_text())


def length_summary(values):
    if not values:
        return dict(min=None, median=None, max=None)
    import statistics

    return dict(min=min(values), median=statistics.median(values), max=max(values))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("bundle", type=Path)
    p.add_argument("output", type=Path)
    a = p.parse_args()
    result = audit(a.bundle, a.output)
    print(result["valid"], result["review_states"])


if __name__ == "__main__":
    main()
