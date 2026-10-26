"""Verify private original bytes, every item range, exclusions and partial references."""

import argparse
import hashlib
import json
from pathlib import Path


def verify(root):
    errors = []
    manifest = json.loads((root / "source_manifest.json").read_text())
    sources = {r["file"]: r for r in manifest}
    raw = {name: (root / "originals" / name).read_bytes() for name in sources}
    items = [json.loads(x) for x in (root / "document_items.jsonl").read_text().splitlines()]
    ids = {r["id"] for r in items}
    for name, data in raw.items():
        if hashlib.sha256(data).hexdigest() != sources[name]["sha256"]:
            errors.append("ORIGINAL_HASH")
        if Path(sources[name]["original_path"]).read_bytes() != data:
            errors.append("ORIGINAL_BYTES")
        text = data.decode("utf-8-sig")
        covered = set()
        for item in items:
            if item["source_file"] != name:
                continue
            a, b = item["char_start"], item["char_end"]
            if (
                text[a:b] != item["item_text"]
                or data[item["byte_start"] : item["byte_end"]].decode() != item["item_text"]
            ):
                errors.append("ITEM_RANGE")
            if hashlib.sha256(item["item_text"].encode()).hexdigest() != item["item_sha256"]:
                errors.append("ITEM_HASH")
            if (
                item["line_start"] != text[:a].count("\n") + 1
                or item["line_end"] != text[:b].count("\n") + 1
            ):
                errors.append("LINE_RANGE")
            if item["supervised"] or item["proforma_id"] is not None:
                errors.append("UNSUPPORTED_PROMOTION")
            covered.update(range(a, b))
        if any(not c.isspace() and i not in covered for i, c in enumerate(text)):
            errors.append("UNINVENTORIED_TEXT")
    count = 0
    for path in (root / "04_CORPUS_DOCUMENTAL_V2").glob("*.jsonl"):
        rows = [json.loads(s) for s in path.read_text().splitlines()]
        refs = {
            r["id"]: r
            for r in map(
                json.loads,
                (root / "06_EXPECTED_ESTRUCTURADOS_V2" / path.name).read_text().splitlines(),
            )
        }
        for row in rows:
            count += 1
            if row["supervised"] or row["split"] != "quarantine":
                errors.append("PRIVATE_SUPERVISION")
            if row["source_ref"]["id"] not in ids:
                errors.append("SOURCE_REF")
            for fact in refs[row["id"]]["facts"]:
                e = fact["evidence"]
                if row["text"][e["start"] : e["end"]] != e["text"]:
                    errors.append("PRIVATE_FACT")
    for p in root.rglob("*"):
        if p.stat().st_mode & 0o077:
            errors.append("PRIVATE_PERMISSIONS")
    return {
        "valid": not errors,
        "sources": len(sources),
        "items": len(items),
        "partial_examples": count,
        "supervised_authentic": 0,
        "errors": errors,
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("path", type=Path)
    a = p.parse_args()
    r = verify(a.path)
    print(json.dumps(r))
    return int(not r["valid"])


if __name__ == "__main__":
    raise SystemExit(main())
