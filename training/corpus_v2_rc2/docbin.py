"""Roundtrip NER data without loading or initializing any statistical model."""

import argparse
import json
from pathlib import Path

import spacy
from spacy.tokens import DocBin


def main():
    p = argparse.ArgumentParser()
    p.add_argument("candidate", type=Path)
    p.add_argument("output", type=Path)
    a = p.parse_args()
    nlp = spacy.blank("es")
    counts = {}
    for path in sorted((a.candidate / "development_v2").rglob("*.jsonl")):
        docs = []
        for line in path.read_text().splitlines():
            r = json.loads(line)
            d = nlp.make_doc(r["text"])
            spans = [
                d.char_span(x, y, label=label, alignment_mode="strict")
                for x, y, label in r["entities"]
            ]
            if any(s is None for s in spans):
                raise ValueError("Invalid offset")
            d.ents = spans
            d.user_data["id"] = r["id"]
            docs.append(d)
        relative = path.relative_to(a.candidate / "development_v2").with_suffix(".spacy")
        target = a.output / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        DocBin(docs=docs, store_user_data=True).to_disk(target)
        restored = list(DocBin().from_disk(target).get_docs(nlp.vocab))
        assert [
            (d.text, d.user_data, [(e.start_char, e.end_char, e.label_) for e in d.ents])
            for d in docs
        ] == [
            (d.text, d.user_data, [(e.start_char, e.end_char, e.label_) for e in d.ents])
            for d in restored
        ]
        counts[str(relative)] = len(docs)
    print(
        json.dumps(
            {
                "files": counts,
                "documents": sum(counts.values()),
                "roundtrip": True,
                "training": False,
            }
        )
    )


if __name__ == "__main__":
    main()
