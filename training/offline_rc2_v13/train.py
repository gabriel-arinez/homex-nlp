"""Manual final-checkpoint training; dev is never loaded or used for selection."""

import json
import os
import random
import time
from pathlib import Path

from training.benchmark_campo.pipeline import digest, private_path, write_private
from training.offline_rc2_v13.protocol import (
    check_files,
    config,
    load_split,
    require_manual,
    runtime,
    sha,
    tree_hash,
)


def fit(nlp, examples, epochs, update_batches):
    """Small injectable loop, tested with stubs without invoking spaCy training in CI."""
    optimizer = nlp.initialize(lambda: examples)
    rng = random.Random(config()["seed"])
    history = []
    for epoch in range(epochs):
        order = list(examples)
        rng.shuffle(order)
        losses = {}
        for batch in update_batches(order):
            nlp.update(batch, sgd=optimizer, drop=config()["dropout"], losses=losses)
        history.append(
            {"epoch": epoch + 1, "losses": {name: float(value) for name, value in losses.items()}}
        )
    return history


def train(wheel, destination, allow_training=False, preflight=None):
    require_manual(allow_training)
    private_path(destination)
    check_files()
    if preflight is None:
        raise ValueError("VERIFIED_PREFLIGHT_REQUIRED")
    private_path(preflight)
    plan = json.loads(preflight.read_text())
    if plan["protocol_digest"] != digest(config()) or not plan["rc2_validation"]["valid"]:
        raise ValueError("STALE_OR_FAILED_PREFLIGHT")
    provenance = runtime(wheel)
    rows = load_split("train")  # Deliberately no dev loader/reference/score callback.
    if plan["train_ids"] != [r["id"] for r in rows]:
        raise ValueError("PREFLIGHT_TRAIN_MEMBERSHIP")
    import spacy
    from spacy.training import Example
    from spacy.util import fix_random_seed, minibatch

    c = config()
    fix_random_seed(c["seed"])
    nlp = spacy.blank("es")
    ner = nlp.add_pipe("ner")
    for label in sorted({e[2] for r in rows for e in r["entities"]}):
        ner.add_label(label)
    examples = [
        Example.from_dict(nlp.make_doc(r["text"]), {"entities": r["entities"]}) for r in rows
    ]
    destination.mkdir(mode=0o700, parents=True, exist_ok=False)
    start = time.perf_counter()
    history = fit(nlp, examples, c["epochs"], lambda order: minibatch(order, size=c["batch_size"]))
    nlp.to_disk(destination / "model-final")
    report = {
        "protocol_digest": digest(c),
        "training_ids": [r["id"] for r in rows],
        "train_content_digest": digest(rows),
        "trainer_source_digest": digest(
            {name: sha(Path(__file__).with_name(name)) for name in ("train.py", "protocol.py")}
        ),
        "checkpoint_selection": "FIXED_FINAL_EPOCH_NO_DEV",
        "history": history,
        "runtime": provenance,
        "model_files": tree_hash(destination / "model-final"),
        "fit_seconds": time.perf_counter() - start,
        "training_documents": len(rows),
        "dev_documents_seen_by_optimizer": 0,
        "PROMOCION": "NO",
    }
    write_private(destination / "training.json", report)
    for path in destination.rglob("*"):
        os.chmod(path, 0o700 if path.is_dir() else 0o600)
    return report
