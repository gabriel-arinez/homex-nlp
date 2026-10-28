"""Compile private full-item adjudications without promoting automatic proposals.

Inputs are original documents, private adjudications and a separate frozen
certificate manifest. Missing reviews fail closed. The output is immutable:
rebuilds must use a new empty directory, never a historical experiment directory.
"""

import argparse
import json
import os
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path

from spacy.tokens import DocBin

from training.canonical_v2.build import family
from training.canonical_v2.io import digest, dump, jsonl, private_path, protect, read
from training.canonical_v2.private_ingest import ingest
from training.canonical_v2.validate import normalized
from training.integral_v2.review import VERSION, seal, validate_review
from training.integral_v2.tokenizer import create_nlp


def partition(items):
    """Join numerical/template variants before hashing whole groups into splits.

    This is an internal holdout of known documents, not external source
    independence. Pairwise joins are transitive, across files as well as within
    them. Short/common snippets are not used to determine full-item similarity.
    """
    ids = [i["id"] for i in items]
    parents = {key: key for key in ids}

    def root(key):
        while parents[key] != key:
            parents[key] = parents[parents[key]]
            key = parents[key]
        return key

    texts = {i["id"]: normalized(i["item_text"]) for i in items}
    edges = []
    for idx, a in enumerate(ids):
        for b in ids[idx + 1 :]:
            similarity = SequenceMatcher(None, texts[a], texts[b], autojunk=False).ratio()
            if similarity >= 0.80:
                parents[root(b)] = root(a)
                edges.append({"a": a, "b": b, "similarity": similarity})
    groups = {}
    for key in ids:
        groups.setdefault(root(key), []).append(key)
    assignment = {}
    for members in groups.values():
        group = "GROUP-" + seal(sorted(members))[:20]
        bucket = int(digest(group)[:8], 16) % 10
        split = "test" if bucket == 0 else "dev" if bucket == 1 else "train"
        for key in members:
            assignment[key] = {"leakage_group": group, "split": split}
    return assignment, edges


def build(sources, adjudications, certificates, output):
    os.umask(0o077)
    output = private_path(output)
    if output.exists():
        raise ValueError("DESTINATION_EXISTS")
    # Resolve and read both private artifacts before any output is created.
    reviews = read(private_path(adjudications))
    certs = json.loads(private_path(certificates).read_text())
    output.mkdir(mode=0o700, parents=True)
    ingest(sources, output / "sources")
    items = read(output / "sources/document_items.jsonl")
    by_id = {r["item_id"]: r for r in reviews}
    if len(reviews) != len(by_id) or set(by_id) != {i["id"] for i in items}:
        raise ValueError("INVENTORY_RECONCILIATION")
    if set(certs) != set(by_id):
        raise ValueError("CERTIFICATE_INVENTORY")
    for item in items:
        validate_review(item, by_id[item["id"]], certs[item["id"]])
    assignments, edges = partition(items)
    nlp = create_nlp()
    rows, refs, ledger = [], [], []
    bins = {s: DocBin(store_user_data=True) for s in ("train", "dev", "test")}
    for item in items:
        review = by_id[item["id"]]
        decision = {
            "item_id": item["id"],
            "source_file": item["source_file"],
            "source_sha256": item["source_sha256"],
            "text_sha256": item["item_sha256"],
            "source_lines": [item["line_start"], item["line_end"]],
            "source_chars": [item["char_start"], item["char_end"]],
            "source_bytes": [item["byte_start"], item["byte_end"]],
            "decision": review["decision"],
            "reason": review["reason"],
            "certificate": certs[item["id"]],
            **assignments[item["id"]],
        }
        if review["decision"] != "APTO":
            decision["split"] = "quarantine"
            ledger.append(decision)
            continue
        ledger.append(decision)
        row = {
            "id": item["id"],
            "parent_id": item["id"],
            "source_item_id": item["id"],
            "text": item["item_text"],
            "text_sha256": item["item_sha256"],
            "entities": review["entities"],
            "origin": "DOCUMENTO_HOMEX_LITERAL",
            "style": "documental",
            "category": family(item),
            "human_reviewed": False,
            "review_kind": review["review_kind"],
            "annotation_scope": "FULL_ITEM",
            **assignments[item["id"]],
        }
        doc = nlp.make_doc(row["text"])
        doc.ents = [doc.char_span(a, b, label=label) for a, b, label in row["entities"]]
        doc.user_data["id"] = row["id"]
        bins[row["split"]].add(doc)
        rows.append(row)
        refs.append(
            {
                "id": item["id"],
                "text_sha256": item["item_sha256"],
                "expected": review["expected"],
                "facts": review["facts"],
                "human_reviewed": False,
                "partial": False,
            }
        )
    jsonl(output / "records.jsonl", rows)
    jsonl(output / "expected.jsonl", refs)
    jsonl(output / "decisions.jsonl", ledger)
    jsonl(output / "near_duplicates.jsonl", edges)
    jsonl(output / "adjudications.jsonl", reviews)
    dump(output / "certificates.json", certs)
    nlp.tokenizer.to_disk(output / "tokenizer")
    for split, docbin in bins.items():
        target = output / f"{split}.spacy"
        docbin.to_disk(target)
        restored = list(DocBin().from_disk(target).get_docs(nlp.vocab))
        source = [r for r in rows if r["split"] == split]
        if len(source) != len(restored) or any(
            d.text != r["text"]
            or [[e.start_char, e.end_char, e.label_] for e in d.ents] != r["entities"]
            for r, d in zip(source, restored)
        ):
            raise ValueError("DOCBIN_ROUNDTRIP")
    manifest = {
        "version": VERSION,
        "inventory": len(items),
        "decisions": dict(Counter(r["decision"] for r in ledger)),
        "full_items": len(rows),
        "families": dict(Counter(r["category"] for r in rows)),
        "labels": dict(Counter(e[2] for r in rows for e in r["entities"])),
        "splits": dict(Counter(r["split"] for r in rows)),
        "independence": "HOLDOUT_INTERNO_DE_DOCUMENTOS_CONOCIDOS",
        "human_gold": False,
        "external_test": False,
        "coverage_complete": all(
            r["decision"] in {"APTO", "CUARENTENA", "DESCARTADO"} for r in ledger
        ),
        "promotion": False,
        "release_status": "REVIEW_IN_PROGRESS",
        "training_ready": False,
    }
    dump(output / "manifest.json", manifest)
    dump(
        output / "sha256.json",
        {
            str(p.relative_to(output)): digest(p.read_bytes())
            for p in sorted(output.rglob("*"))
            if p.is_file()
        },
    )
    protect(output)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sources", type=Path, nargs=3, required=True)
    parser.add_argument("--adjudications", type=Path, required=True)
    parser.add_argument("--certificates", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.sources, args.adjudications, args.certificates, args.output)))


if __name__ == "__main__":
    main()
