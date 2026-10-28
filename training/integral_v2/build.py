"""Compile private full-item adjudications without promoting automatic proposals.

Inputs are original documents, private adjudications and a separate frozen
certificate manifest. Missing reviews fail closed. The output is immutable:
rebuilds must use a new empty directory, never a historical experiment directory.
"""

import argparse
import json
import os
from collections import Counter
from copy import deepcopy
from difflib import SequenceMatcher
from pathlib import Path

from spacy.tokens import DocBin

from training.canonical_v2.build import FAMILIES, family
from training.canonical_v2.io import digest, dump, jsonl, private_path, protect, read
from training.canonical_v2.patches_v1 import patches
from training.canonical_v2.private_ingest import ingest
from training.canonical_v2.validate import ROOT, normalized
from training.integral_v2.review import VERSION, seal, validate_review
from training.integral_v2.tokenizer import create_nlp


def partition(items, links=(), *, coverage_items=()):
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

    for child, parent in links:
        if child not in parents or parent not in parents:
            raise ValueError("ORPHAN_PARAPHRASE_PARENT")
        parents[root(child)] = root(parent)
    texts = {i["id"]: normalized(i["item_text"]) for i in items}
    templates = {}
    for item in items:
        text = item["item_text"]
        for start, end, label in reversed(item.get("entities", [])):
            text = text[:start] + " " + label + " " + text[end:]
        templates[item["id"]] = normalized(text)
    edges = []
    for idx, a in enumerate(ids):
        for b in ids[idx + 1 :]:
            similarity = SequenceMatcher(None, texts[a], texts[b], autojunk=False).ratio()
            template_similarity = SequenceMatcher(
                None, templates[a], templates[b], autojunk=False
            ).ratio()
            if similarity >= 0.80 or (
                min(len(texts[a]), len(texts[b])) > 200 and template_similarity >= 0.85
            ):
                parents[root(b)] = root(a)
                edges.append(
                    {
                        "a": a,
                        "b": b,
                        "similarity": similarity,
                        "template_similarity": template_similarity,
                    }
                )
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
    # Coverage planning uses annotations only, never predictions or scores.
    # Move whole rare-label groups into train without emptying dev or holdout.
    labels = {entry[2] for item in coverage_items for entry in item.get("entities", [])}
    eligible = {item["id"]: item for item in coverage_items}
    for label in sorted(labels):
        carrying = {
            assignment[key]["leakage_group"]
            for key, item in eligible.items()
            if any(entity[2] == label for entity in item.get("entities", []))
        }
        if any(
            value["split"] == "train" and value["leakage_group"] in carrying
            for value in assignment.values()
        ):
            continue
        candidates = []
        for group in carrying:
            members = [key for key, value in assignment.items() if value["leakage_group"] == group]
            split = assignment[members[0]]["split"]
            others = {
                value["leakage_group"]
                for value in assignment.values()
                if value["split"] == split and value["leakage_group"] != group
            }
            if others:
                candidates.append((len(members), digest(group), group))
        if not candidates:
            raise ValueError("RARE_LABEL_CANNOT_BE_ISOLATED_WITH_TRAIN_SUPPORT")
        chosen = min(candidates)[2]
        for value in assignment.values():
            if value["leakage_group"] == chosen:
                value["split"] = "train"
    return assignment, edges


def build(sources, adjudications, certificates, output, oral_reviews=None):
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
    oral = read(private_path(oral_reviews)) if oral_reviews else []
    source_by_id = {i["id"]: i for i in items}
    links = []
    for entry in oral:
        for parent in [entry["parent_id"], *entry.get("additional_parent_ids", [])]:
            if parent not in source_by_id:
                raise ValueError("ORPHAN_ORAL_PARENT")
            links.append((entry["item"]["id"], parent))
        if entry["source_parent_sha256"] != source_by_id[entry["parent_id"]]["item_sha256"]:
            raise ValueError("ORAL_PARENT_CHANGED")
        if entry["origin"] != "SINTETICO_ORAL" or entry.get("audio_real") is not False:
            raise ValueError("FALSE_ORAL_PROVENANCE")
        validate_review(entry["item"], entry["review"], entry["certificate"])
    partition_items = [item | {"entities": by_id[item["id"]]["entities"]} for item in items]
    partition_items += [e["item"] | {"entities": e["review"]["entities"]} for e in oral]
    coverage_items = [
        item
        for item in partition_items
        if item["id"] not in by_id or by_id[item["id"]]["decision"] == "APTO"
    ]
    assignments, edges = partition(partition_items, links, coverage_items=coverage_items)
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
    for entry in oral:
        item, review = entry["item"], entry["review"]
        row = {
            "id": item["id"],
            "parent_id": entry["parent_id"],
            "source_item_id": entry["parent_id"],
            "text": item["item_text"],
            "text_sha256": digest(item["item_text"]),
            "entities": review["entities"],
            "origin": "SINTETICO_ORAL",
            "style": "oral",
            "category": entry["category"],
            "human_reviewed": False,
            "review_kind": review["review_kind"],
            "annotation_scope": "FULL_ITEM",
            **assignments[item["id"]],
        }
        rows.append(row)
        refs.append(
            {
                "id": item["id"],
                "text_sha256": row["text_sha256"],
                "expected": review["expected"],
                "facts": review["facts"],
                "human_reviewed": False,
                "partial": False,
            }
        )
        doc = nlp.make_doc(row["text"])
        doc.ents = [doc.char_span(a, b, label=label) for a, b, label in row["entities"]]
        doc.user_data["id"] = row["id"]
        bins[row["split"]].add(doc)
    baseline, reconciliation, overlays = {}, [], []
    for fam in FAMILIES:
        for folder, ext in [("corpus", "jsonl"), ("expected", "jsonl"), ("splits", "json")]:
            path = ROOT / "data" / folder / (fam + "." + ext)
            baseline[str(path.relative_to(ROOT))] = digest(path.read_bytes())
        for record in read(ROOT / "data/corpus" / (fam + ".jsonl")):
            patch = patches(deepcopy(record)) if record["split"] != "test" else None
            reconciliation.append(
                {
                    "id": record["id"],
                    "split": record["split"],
                    "text_sha256": record["text_sha256"],
                    "origin": "HISTORICO_V1_NO_PROMOVIDO_A_LITERAL",
                    "decision": "FROZEN_TEST"
                    if patch is None
                    else "OVERLAY_REVERSIBLE"
                    if patch["operations"]
                    else "HISTORICAL_UNCHANGED",
                    "operations": len(patch["operations"]) if patch else 0,
                }
            )
            if patch:
                overlays.append(patch)
    dump(output / "baseline_sha256.json", baseline)
    jsonl(output / "v1_reconciliation.jsonl", reconciliation)
    jsonl(output / "v1_reversible_overlays.jsonl", overlays)
    jsonl(
        output / "historical_decisions.jsonl",
        read(ROOT / "data/canonical_v2/historical_decisions.jsonl"),
    )
    known = [r for r in read(ROOT / "data/canonical_v2/synthetic.jsonl") if r["split"] == "dev"]
    known_ids = {r["id"] for r in known}
    jsonl(output / "diagnostic_known_dev.jsonl", known)
    jsonl(
        output / "diagnostic_known_expected.jsonl",
        [
            r
            for r in read(ROOT / "data/canonical_v2/synthetic_expected.jsonl")
            if r["id"] in known_ids
        ],
    )
    jsonl(output / "oral_reviews.jsonl", oral)
    jsonl(output / "records.jsonl", rows)
    jsonl(output / "expected.jsonl", refs)
    jsonl(output / "decisions.jsonl", ledger)
    jsonl(output / "near_duplicates.jsonl", edges)
    dump(output / "assignments.json", assignments)
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
        "full_items": sum(r["style"] == "documental" for r in rows),
        "oral_cases": len(oral),
        "origins": dict(Counter(r["origin"] for r in rows)),
        "families": dict(Counter(r["category"] for r in rows)),
        "labels": dict(Counter(e[2] for r in rows for e in r["entities"])),
        "train_labels": dict(
            Counter(e[2] for r in rows if r["split"] == "train" for e in r["entities"])
        ),
        "split_policy": "group hash plus deterministic rare-label train coverage; no prediction-based assignment",
        "splits": dict(Counter(r["split"] for r in rows)),
        "independence": "HOLDOUT_INTERNO_DE_DOCUMENTOS_CONOCIDOS",
        "human_gold": False,
        "external_test": False,
        "coverage_complete": all(
            r["decision"] in {"APTO", "CUARENTENA", "DESCARTADO"} for r in ledger
        ),
        "promotion": False,
        "release_status": "TECHNICAL_ASSISTED_OFFLINE",
        "training_ready": all(r["decision"] != "PARCIAL_NO_ENTRENABLE" for r in ledger)
        and all(any(r["split"] == split for r in rows) for split in ("train", "dev", "test"))
        and any(r["style"] == "oral" and r["split"] == "train" for r in rows),
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
    parser.add_argument("--oral-reviews", type=Path)
    args = parser.parse_args()
    print(
        json.dumps(
            build(
                args.sources, args.adjudications, args.certificates, args.output, args.oral_reviews
            )
        )
    )


if __name__ == "__main__":
    main()
