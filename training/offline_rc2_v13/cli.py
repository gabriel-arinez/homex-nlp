"""Explicit prepare/train/evaluate/summarize CLI; no default execution."""

import argparse
import json
from pathlib import Path

from training.benchmark_campo.pipeline import write_private
from training.offline_rc2_v13.protocol import load_split, prepare, references


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("operation", choices=["prepare", "train", "evaluate", "summarize", "compare"])
    p.add_argument("--wheel", type=Path)
    p.add_argument("--model-run", type=Path)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--allow-training", action="store_true")
    p.add_argument("--predictions", type=Path)
    p.add_argument("--preflight", type=Path)
    p.add_argument("--private-detail", type=Path)
    p.add_argument("--evaluation-dirs", type=Path, nargs="+")
    a = p.parse_args()
    if a.operation == "prepare":
        prepare(a.wheel, a.output)
    elif a.operation == "train":
        from training.offline_rc2_v13.train import train

        train(a.wheel, a.output, a.allow_training, a.preflight)
    elif a.operation == "evaluate":
        from training.offline_rc2_v13.worker import evaluate

        evaluate(a.wheel, a.model_run, a.output)
    elif a.operation == "compare":
        from training.offline_rc2_v13.scoring import comparison

        write_private(a.output, comparison(a.evaluation_dirs, a.preflight))
    else:
        from training.offline_rc2_v13.scoring import private_differences, summarize

        rows, refs = load_split("dev"), references("dev")
        predictions = json.loads(a.predictions.read_text())
        write_private(a.output, summarize(rows, refs, predictions))
        if a.private_detail:
            write_private(a.private_detail, private_differences(rows, refs, predictions))
    print(json.dumps({"ok": True, "operation": a.operation, "PROMOCION": "NO"}))


if __name__ == "__main__":
    main()
