"""Experimento NER local reproducible; nunca promueve pesos al runtime."""

import argparse
import json
from pathlib import Path

import spacy
from spacy.scorer import Scorer
from spacy.training import Example
from spacy.util import fix_random_seed, minibatch

from training.corpus import read_jsonl, sha256_bytes


def evaluar(nlp, rows):
    scores = Scorer().score(
        [Example.from_dict(nlp(r["text"]), {"entities": r["entities"]}) for r in rows]
    )
    by_type = scores["ents_per_type"]
    return {
        "documentos": len(rows),
        "micro": {k: scores[f"ents_{k}"] for k in ("p", "r", "f")},
        "macro": {
            k: sum(v[k] for v in by_type.values()) / len(by_type) if by_type else 0
            for k in ("p", "r", "f")
        },
        "por_etiqueta": by_type,
    }


def entrenar(corpus, manifest, destination, epochs):
    split = json.loads(manifest.read_text())
    if not split["sealed"] or split["corpus_sha256"] != sha256_bytes(corpus.read_bytes()):
        raise ValueError("El corpus no coincide con la partición sellada")
    rows = {r["id"]: r for _, r in read_jsonl(corpus)}
    train = [rows[i] for i in split["assignments"]["train"]]
    dev = [rows[i] for i in split["assignments"]["dev"]]
    fix_random_seed(404)
    nlp = spacy.blank("es")
    ner = nlp.add_pipe("ner")
    for label in sorted({e[2] for r in train for e in r["entities"]}):
        ner.add_label(label)
    examples = [
        Example.from_dict(nlp.make_doc(r["text"]), {"entities": r["entities"]}) for r in train
    ]
    optimizer = nlp.initialize(lambda: examples)
    history, best = [], -1
    for epoch in range(epochs):
        losses = {}
        for batch in minibatch(examples, size=8):
            nlp.update(batch, sgd=optimizer, drop=0.2, losses=losses)
        scores = evaluar(nlp, dev)
        history.append({"epoca": epoch + 1, "loss": losses, "dev": scores})
        if scores["micro"]["f"] > best:
            best = scores["micro"]["f"]
            nlp.to_disk(destination / "model-dev-best")
        print(f"epoch={epoch + 1} dev_f1={scores['micro']['f']:.4f}", flush=True)
    report = {
        "corpus_sha256": split["corpus_sha256"],
        "seed": 404,
        "epocas": epochs,
        "spacy": spacy.__version__,
        "seleccion": "dev.micro.f",
        "historial": history,
        "promovido": False,
        "motivo": "Faltan gates semánticos y productividad humana",
    }
    (destination / "entrenamiento.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, default=float) + "\n"
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs", type=int, default=25)
    parser.add_argument("--destination", type=Path, required=True)
    args = parser.parse_args()
    args.destination.mkdir(parents=True, exist_ok=False)
    entrenar(
        Path("data/corpus/muebles_pedido.jsonl"),
        Path("data/splits/muebles_pedido.json"),
        args.destination,
        args.epochs,
    )


if __name__ == "__main__":
    main()
