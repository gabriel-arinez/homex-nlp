"""Evaluación offline explícita de un modelo spaCy sobre un DocBin indicado."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import spacy
from spacy.scorer import Scorer
from spacy.tokens import DocBin
from spacy.training import Example


def evaluate(model: Path, corpus: Path) -> dict:
    nlp = spacy.load(model)
    reference_docs = list(DocBin().from_disk(corpus).get_docs(nlp.vocab))
    examples = [Example(nlp(reference.text), reference) for reference in reference_docs]
    scores = Scorer().score(examples)
    return {
        "documents": len(examples),
        "ents_p": scores["ents_p"],
        "ents_r": scores["ents_r"],
        "ents_f": scores["ents_f"],
        "ents_per_type": scores["ents_per_type"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("model", type=Path)
    parser.add_argument("corpus", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = evaluate(args.model, args.corpus)
    encoded = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
