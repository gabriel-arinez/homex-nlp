"""Explicit candidate export, never trains and never overwrites active V1 artifacts."""

import argparse
import json
from collections import defaultdict
from pathlib import Path

import spacy
from spacy.tokens import DocBin


def export(candidate, output):
    candidate, output = candidate.resolve(), output.resolve()
    if output == candidate or candidate in output.parents:
        raise ValueError("Export outside the candidate dataset")
    nlp = spacy.blank("es")
    docs = defaultdict(list)
    for folder in ("04_CORPUS_DOCUMENTAL_V2", "05_CORPUS_ORAL_V2"):
        for path in sorted((candidate / folder).glob("*.jsonl")):
            for line in path.read_text().splitlines():
                row = json.loads(line)
                doc = nlp.make_doc(row["text"])
                entities = [
                    doc.char_span(a, b, label=label, alignment_mode="strict")
                    for a, b, label in row["entities"]
                ]
                if any(s is None for s in entities):
                    raise ValueError("Misaligned entity: " + row["id"])
                doc.ents = entities
                doc.user_data.update(id=row["id"], split=row["split"], origin=row["origin"])
                docs[(row["category"], row["split"])].append(doc)
    report = {}
    for (family, split), values in sorted(docs.items()):
        path = output / family / f"{split}.spacy"
        path.parent.mkdir(parents=True, exist_ok=True)
        DocBin(docs=values, store_user_data=True).to_disk(path)
        restored = list(DocBin().from_disk(path).get_docs(nlp.vocab))
        if [
            (d.text, d.user_data["id"], [(e.start_char, e.end_char, e.label_) for e in d.ents])
            for d in restored
        ] != [
            (d.text, d.user_data["id"], [(e.start_char, e.end_char, e.label_) for e in d.ents])
            for d in values
        ]:
            raise ValueError("DocBin round trip failed")
        report[f"{family}/{split}"] = len(values)
    return {"records": sum(report.values()), "files": report, "roundtrip": True, "training": False}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("candidate", type=Path)
    p.add_argument("output", type=Path)
    a = p.parse_args()
    print(json.dumps(export(a.candidate, a.output), sort_keys=True))


if __name__ == "__main__":
    main()
