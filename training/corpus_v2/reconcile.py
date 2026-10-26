"""Compare every V1 literal against private items; export only safe match metadata."""

import argparse
import json
import re
from pathlib import Path

from training.corpus_v2.build import dump, table


def reconcile(private, public_summary):
    items = [json.loads(s) for s in (private / "document_items.jsonl").read_text().splitlines()]
    rows = [
        json.loads(s)
        for p in sorted(Path("data/corpus").glob("*.jsonl"))
        for s in p.read_text().splitlines()
    ]
    matches = []
    safe = []
    for r in rows:
        confirmed = [i for i in items if r["text"] == i["item_text"] or r["text"] in i["item_text"]]
        # Similar terms may guide a human; do not certify title-only provenance.
        words = set(re.findall(r"\w+", r["text"].lower()))
        candidates = []
        for i in items:
            other = set(re.findall(r"\w+", i["item_text"].lower()))
            score = len(words & other) / len(words | other)
            candidates.append((score, i, sorted(words & other)))
        score, best, terms = max(candidates, key=lambda x: x[0])
        state = "CONFIRMADA" if confirmed else "NO_IDENTIFICADA"
        entry = {
            "v1_id": r["id"],
            "text_sha256": r["text_sha256"],
            "state": state,
            "compared_source_items": len(items),
            "confirmed_refs": [
                {
                    "source_file": i["source_file"],
                    "block": i["block"],
                    "line_start": i["line_start"],
                    "line_end": i["line_end"],
                    "source_sha256": i["source_sha256"],
                    "item_sha256": i["item_sha256"],
                }
                for i in confirmed
            ],
        }
        safe.append(entry)
        matches.append(
            entry
            | {
                "nearest_diagnostic_source": best["id"],
                "nearest_jaccard_words": round(score, 6),
                "shared_terms": terms,
                "note": "Vocabulario o título compartido no certifica adaptación ni copia; no se asigna origen documental.",
            }
        )
    table(private / "02_RECONCILIACION_V1_DOCUMENTOS.csv", matches)
    dump(
        public_summary,
        {
            "method": "full-V1-literal-equality-or-inclusion-against-all-private-items-v1",
            "source_item_count": len(items),
            "v1_count": len(rows),
            "confirmed_count": sum(x["state"] == "CONFIRMADA" for x in safe),
            "records": safe,
        },
    )
    # Private complete review queue and confirmed private example source graph.
    anomalies = {
        r["id"]: r
        for r in map(json.loads, (private / "document_quarantine.jsonl").read_text().splitlines())
    }
    queue = []
    links = []
    docs = [
        r
        for p in (private / "04_CORPUS_DOCUMENTAL_V2").glob("*.jsonl")
        for r in map(json.loads, p.read_text().splitlines())
    ]
    for item in items:
        queue.append(
            {
                "id": item["id"],
                "source_file": item["source_file"],
                "block": item["block"],
                "line_start": item["line_start"],
                "line_end": item["line_end"],
                "state": "REQUIERE_REVISION_HUMANA",
                "supervised": False,
                "evidence": item["item_text"],
                "reason": anomalies.get(item["id"], {}).get(
                    "issues", ["Homologación y autorización de publicación pendientes."]
                ),
                "alternatives": "Preservar literal; no completar ni corregir sin evidencia.",
            }
        )
        found = next((d for d in docs if d["source_ref"]["id"] == item["id"]), None)
        links.append(
            {
                "source_file": item["source_file"],
                "block": item["block"],
                "line_start": item["line_start"],
                "line_end": item["line_end"],
                "item_id": item["id"],
                "v2_id": found["id"] if found else "",
                "status": "CONFIRMADA" if found else "NO_INCORPORADA_V2",
                "proof": item["item_sha256"],
                "note": "Texto literal del ítem y fuente con rangos verificados; referencia parcial privada, nunca gold.",
            }
        )
    table(private / "10_PENDIENTES_REVISION_HUMANA.csv", queue)
    table(private / "02_CORRESPONDENCIA_DOCUMENTAL.csv", links)
    for p in private.rglob("*"):
        p.chmod(0o700 if p.is_dir() else 0o600)
    print(
        json.dumps(
            {
                "v1_compared": len(rows),
                "source_items": len(items),
                "confirmed": sum(x["state"] == "CONFIRMADA" for x in safe),
            }
        )
    )


def main():
    p = argparse.ArgumentParser()
    p.add_argument("private", type=Path)
    p.add_argument("--public-summary", type=Path, required=True)
    a = p.parse_args()
    reconcile(a.private, a.public_summary)


if __name__ == "__main__":
    main()
