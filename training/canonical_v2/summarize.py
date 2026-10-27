"""Aggregate only measured results; never export private text, prices or weights."""

import argparse
import json
import statistics
from pathlib import Path

from training.canonical_v2.io import digest, dump


def summarize(bundle, experiments):
    evaluations = [json.loads(p.read_text()) for p in sorted(experiments.glob("*/evaluation.json"))]
    training = [json.loads(p.read_text()) for p in sorted(experiments.glob("*/training.json"))]
    if len(evaluations) != 10 or len(training) != 10:
        raise ValueError("TEN_COMPLETE_RUNS_REQUIRED")
    table = []
    for e in evaluations:
        for model, metrics in e["models"].items():
            all_metrics = metrics["families"]["ALL"]
            table.append(
                dict(
                    corpus=e["variant"],
                    seed=e["seed"],
                    model=model,
                    split="dev",
                    ner_f1=all_metrics["ner"]["micro"]["f1"],
                    commercial_exact=all_metrics["commercial"]["full_exact_accuracy"],
                    commercial_n=all_metrics["commercial"]["documents"],
                    false_proposals=all_metrics["commercial"]["false_proposals"],
                    negative_n=all_metrics["commercial"]["negatives"],
                    critical_errors=all_metrics["commercial"]["critical_errors"],
                    warm_p50_ms=metrics["performance"]["warm_p50_ms"],
                    warm_p95_ms=metrics["performance"]["warm_p95_ms"],
                    process_peak_rss_kib=e["performance"]["process_peak_rss_kib"],
                    model_bytes=e["performance"]["model_bytes"],
                )
            )
    variance = []
    for variant in ["D1", "D2", "D3", "D4", "D4W"]:
        for model in ["M-A", "M-B", "M-C"]:
            subset = [r for r in table if r["corpus"] == variant and r["model"] == model]
            fs = [r["ner_f1"] or 0 for r in subset]
            variance.append(
                dict(
                    corpus=variant,
                    model=model,
                    ner_f1_mean=statistics.mean(fs),
                    ner_f1_population_std=statistics.pstdev(fs),
                    commercial_exact_mean=statistics.mean(r["commercial_exact"] for r in subset),
                    false_proposals_by_seed=[r["false_proposals"] for r in subset],
                    warm_p95_ms_mean=statistics.mean(r["warm_p95_ms"] for r in subset),
                )
            )
    selected = max(training, key=lambda r: r["best_dev_f1"])
    return dict(
        corpus=json.loads((bundle / "manifest.json").read_text()),
        sealed_sha256=json.loads((bundle / "sha256.json").read_text()),
        training=[
            {
                k: r[k]
                for k in [
                    "variant",
                    "seed",
                    "train_documents",
                    "train_labels",
                    "repeated_samples",
                    "epochs",
                    "selected_epoch",
                    "best_dev_f1",
                    "seconds",
                    "process_peak_rss_kib",
                    "spacy",
                    "model_bytes",
                ]
            }
            | {
                "model_tree_sha256": digest(json.dumps(r["model_sha256"], sort_keys=True)),
                "model_files_sha256": r["model_sha256"],
            }
            for r in training
        ],
        comparisons=table,
        variability=variance,
        evaluation=evaluations,
        best_raw_dev_ner_checkpoint={
            k: selected[k] for k in ["variant", "seed", "best_dev_f1", "selected_epoch"]
        },
        recommendation="MANTENER_RULES_ONLY",
        promotion=False,
        interpretation="Synthetic development diagnostics only. No independent documentary, voice or human gold generalization established.",
    )


def main():
    p = argparse.ArgumentParser()
    p.add_argument("bundle", type=Path)
    p.add_argument("experiments", type=Path)
    p.add_argument("output", type=Path)
    a = p.parse_args()
    result = summarize(a.bundle, a.experiments)
    dump(a.output, result)
    print(json.dumps(result["best_raw_dev_ner_checkpoint"]))


if __name__ == "__main__":
    main()
