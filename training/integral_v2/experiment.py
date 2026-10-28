"""New full-item experiments; frozen train/dev, single final internal holdout."""

import argparse
import json
import os
import resource
import statistics
import subprocess
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

from homex_nlp.contracts import ExtractionRequest, ExtractionResult
from homex_nlp.engine import RulesEngine
from training.canonical_v2 import experiment as base
from training.canonical_v2.commercial import compare_fields, predicted_fields, reference_fields
from training.canonical_v2.io import digest, dump, jsonl, private_path, protect, read
from training.canonical_v2.reconcile import evidence, reconcile
from training.canonical_v2.validate import LABELS, ROOT
from training.integral_v2.assembler import IntegralNerEngine
from training.integral_v2.project import compare, fields, project
from training.integral_v2.tokenizer import create_nlp
from training.integral_v2.validate import validate_bundle

PROTOCOL = Path(__file__).with_name("protocol.json")


def preflight(bundle):
    validate_bundle(bundle, training=True)
    code_files = sorted(
        [
            *Path(__file__).parent.glob("*.py"),
            *Path(__file__).parent.glob("*.json"),
            ROOT / "training/canonical_v2/reconcile.py",
            ROOT / "training/canonical_v2/commercial.py",
            ROOT / "uv.lock",
        ]
    )
    return {
        "analysis_code_sha256": digest(
            json.dumps(
                {str(p.relative_to(ROOT)): digest(p.read_bytes()) for p in code_files},
                sort_keys=True,
            )
        ),
        "bundle_sha256": digest((bundle / "sha256.json").read_bytes()),
        "protocol_sha256": digest(PROTOCOL.read_bytes()),
        "training_code_sha256": digest((ROOT / "training/canonical_v2/experiment.py").read_bytes()),
        "tokenizer_sha256": digest(Path(__file__).with_name("tokenizer.py").read_bytes()),
    }


def train(bundle, output, variant, seed):
    base.train(
        bundle,
        output,
        variant,
        seed,
        protocol_path=PROTOCOL,
        preflight_fn=preflight,
        nlp_factory=None if variant == "D1" else create_nlp,
    )
    report = json.loads((output / "training.json").read_text())
    report["code_revision"] = (
        subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip()
    )
    dump(output / "training.json", report)
    protect(output)


def hybrid(a, b, version):
    if b is None:
        return a.model_copy(deep=True)
    aa, bb = a.item_proposal, b.item_proposal
    if aa is None and bb is not None:
        # Rules abstention is retained for its explicit voice-scope/multiproduct veto.
        veto = {"OUT_OF_VOICE_SCOPE", "MULTIPLE_MAIN_PRODUCTS"}
        if bb.quantity and not any(w.code in veto for w in a.warnings):
            return b.model_copy(deep=True)
    if (
        aa
        and bb
        and aa.name == bb.name
        and aa.quantity == bb.quantity
        and len(bb.components) > len(aa.components)
    ):
        merged = b.model_copy(deep=True)
        if bb.price is None and aa.price is not None:
            # Candidate namespaces differ, so preserve both evidence sets.
            merged.candidates.extend(a.candidates)
            merged.item_proposal.price = aa.price.model_copy(deep=True)
        return ExtractionResult.model_validate(merged.model_dump())
    out, _ = reconcile(a.model_dump(mode="json"), b.model_dump(mode="json"), version)
    return ExtractionResult.model_validate(out)


def evaluate(bundle, run):
    training = json.loads((run / "training.json").read_text())
    if training["sealed"] != preflight(bundle) or training["model_sha256"] != base.sha_tree(
        run / "model-best"
    ):
        raise ValueError("MODEL_OR_DATA_CHANGED")
    # All checkpoints must already be selected before accessing final holdout.
    rows = read(bundle / "records.jsonl")
    refs = {r["id"]: r["expected"] for r in read(bundle / "expected.jsonl")}
    known = read(bundle / "diagnostic_known_dev.jsonl")
    known_refs = {r["id"]: r for r in read(bundle / "diagnostic_known_expected.jsonl")}
    start = time.perf_counter()
    a = RulesEngine()
    rules_load = time.perf_counter() - start
    start = time.perf_counter()
    b = IntegralNerEngine(run / "model-best")
    load = time.perf_counter() - start
    reports = {}
    details = []
    for split, subset, reference in [
        ("dev", [r for r in rows if r["split"] == "dev"], refs),
        ("holdout_internal", [r for r in rows if r["split"] == "test"], refs),
        ("known_synthetic_dev", known, known_refs),
    ]:
        stats = {
            m: {
                "fields": defaultdict(Counter),
                "families": defaultdict(lambda: Counter()),
                "latencies": [],
                "raw_predictions": [],
                "exact": 0,
                "negatives": 0,
                "false_proposals": 0,
                "contract_failures": 0,
                "commercial_n": 0,
            }
            for m in ("M-A", "M-A2-price", "M-A2-quantity", "M-A2-dimensions", "M-B", "M-C")
        }
        for row in subset:
            request = ExtractionRequest(
                request_id=row["id"],
                text=row["text"],
                currency_context=reference[row["id"]].get("comercial", {}).get("moneda_codigo")
                or "BOB",
            )
            start = time.perf_counter()
            ar = a.extract(request)
            a_ms = (time.perf_counter() - start) * 1000
            start = time.perf_counter()
            failure = False
            try:
                br = b.extract(request)
            except (ValueError, TypeError):
                br = None
                failure = True
            b_ms = (time.perf_counter() - start) * 1000
            start = time.perf_counter()
            try:
                cr = hybrid(ar, br, b.model_version)
            except (ValueError, TypeError):
                cr = ar.model_copy(deep=True)
            c_ms = a_ms + b_ms + (time.perf_counter() - start) * 1000
            results = {"M-A": ar, "M-B": br, "M-C": cr}
            for field in ("price", "quantity", "dimensions"):
                results["M-A2-" + field] = base.ablate(ar, field)
            saved = {}
            for name, result in results.items():
                s = stats[name]
                serialized = result.model_dump(mode="json") if result else None
                saved[name] = serialized
                s["latencies"].append({"M-A": a_ms, "M-B": b_ms, "M-C": c_ms}.get(name, a_ms))
                s["raw_predictions"].append(evidence(serialized, LABELS)[0] if serialized else [])
                s["contract_failures"] += name == "M-B" and failure
                # Documentary chair/floor data is evaluated for NER. A furniture
                # voice proposal for those families remains outside this task.
                if row["category"] != "muebles_pedido":
                    continue
                s["commercial_n"] += 1
                ref = reference[row["id"]]
                negative = (
                    ref.get("status") == "NO_PROPOSAL"
                    or ref.get("comercial", {}).get("nombre") is None
                )
                s["negatives"] += negative
                s["false_proposals"] += (
                    negative
                    and serialized is not None
                    and serialized.get("item_proposal") is not None
                )
                wanted = fields(ref)
                actual = fields(project(serialized)) if serialized else {}
                counts = compare(wanted, actual)
                exact = all(v["fp"] == 0 and v["fn"] == 0 for v in counts.values())
                s["exact"] += exact
                s["families"][row["category"]]["documents"] += 1
                s["families"][row["category"]]["exact"] += exact
                for key, c in counts.items():
                    s["fields"][key].update(c)
            details.append({"id": row["id"], "split": split, "results": saved})
        legacy = {}
        if split == "known_synthetic_dev":
            split_details = details[-len(subset) :]
            for model in stats:
                exact = 0
                n = 0
                invalid = 0
                for row, detail in zip(subset, split_details):
                    if row["category"] != "muebles_pedido":
                        continue
                    n += 1
                    try:
                        want, reviewed = reference_fields(reference[row["id"]])
                        p = detail["results"][model]
                        actual = predicted_fields(p) if p else {}
                        cs = compare_fields(want, actual, reviewed)
                        exact += all(
                            v["omission"] == 0 and v["false_assertion"] == 0 for v in cs.values()
                        )
                    except ValueError:
                        invalid += 1
                legacy[model] = {
                    "n": n,
                    "exact": exact,
                    "adapter_failures": invalid,
                    "metric": "historical canonical scope-aware fields, separately from new full-reference metric",
                }
        summary = {}
        for name, s in stats.items():
            values = s["latencies"]
            n = s["commercial_n"]
            z = 1.96
            p = s["exact"] / n if n else 0
            den = 1 + z * z / n if n else 1
            center = (p + z * z / (2 * n)) / den if n else None
            radius = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / den if n else None
            summary[name] = {
                "documents": len(subset),
                "commercial_furniture_n": n,
                "full_exact": s["exact"],
                "full_exact_accuracy": s["exact"] / n if n else None,
                "wilson95": [max(0, center - radius), min(1, center + radius)] if n else None,
                "fields": {k: dict(v) for k, v in s["fields"].items()},
                "critical_errors": sum(
                    v["fp"] + v["fn"]
                    for k, v in s["fields"].items()
                    if k
                    in {
                        "nombre",
                        "cantidad",
                        "unidad_codigo",
                        "precio_unitario",
                        "precio_total_efectivo",
                        "descuento_linea",
                        "material",
                        "espesor",
                        "cantidad_interna",
                        "conjunto",
                    }
                    or k.startswith("dimension:")
                ),
                "critical_error_definition": "FP+FN in product/quantity/unit/money/material/thickness/dimension/internal-count/group fields; substitutions count twice",
                "negatives": s["negatives"],
                "false_proposals": s["false_proposals"],
                "contract_failures": s["contract_failures"],
                "ner_accepted": base.ner_metrics(subset, s["raw_predictions"]),
                "families": {k: dict(v) for k, v in s["families"].items()},
                "latency_ms": {
                    "first": values[0] if values else None,
                    "warm_p50": statistics.median(values[1:]) if len(values) > 1 else None,
                    "warm_p95": base.pct(values[1:], 0.95),
                    "ablations_are_output_diagnostics": name.startswith("M-A2"),
                },
            }
        reports[split] = {
            "models": summary,
            "raw_ner": base.score_nlp(b.nlp, subset),
            "historical_16_comparable": legacy,
            "ner_by_family": {
                fam: base.score_nlp(b.nlp, [r for r in subset if r["category"] == fam])
                for fam in sorted({r["category"] for r in subset})
            },
        }
    dump(
        run / "evaluation.json",
        {
            "variant": training["variant"],
            "seed": training["seed"],
            "sealed": training["sealed"],
            "independence": "HOLDOUT_INTERNO_DE_DOCUMENTOS_CONOCIDOS",
            "human_gold": False,
            "promotion": False,
            "splits": reports,
            "ner_load_seconds": load,
            "rules_load_seconds": rules_load,
            "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            "metric_policy": "Order-independent named component/group scopes, explicit price roles, all reviewed attributes; omissions remain errors, not adapter exclusions. Non-furniture commercial voice not deployed.",
        },
    )
    jsonl(run / "predictions.jsonl", details)
    protect(run)


def run_all(bundle, output):
    private_path(output)
    if output.exists():
        raise ValueError("EXPERIMENT_OUTPUT_EXISTS")
    output.mkdir(mode=0o700, parents=True)
    dump(output / "preflight.json", preflight(bundle))
    config = json.loads(PROTOCOL.read_text())
    env = os.environ | {
        "OMP_NUM_THREADS": "2",
        "OPENBLAS_NUM_THREADS": "2",
        "MKL_NUM_THREADS": "2",
        "PYTHONHASHSEED": "0",
    }
    runs = [
        (variant, seed, output / f"{variant}-{seed}")
        for variant in config["experiments"]
        for seed in config["seeds"]
    ]
    for variant, seed, destination in runs:
        subprocess.run(
            [
                sys.executable,
                "-m",
                "training.integral_v2.experiment",
                "train",
                "--bundle",
                str(bundle),
                "--output",
                str(destination),
                "--variant",
                variant,
                "--seed",
                str(seed),
            ],
            env=env,
            check=True,
        )
    dump(
        output / "checkpoints_frozen.json",
        {
            str(path.name): json.loads((path / "training.json").read_text())["model_sha256"]
            for _, _, path in runs
        },
    )
    for _, _, destination in runs:
        subprocess.run(
            [
                sys.executable,
                "-m",
                "training.integral_v2.experiment",
                "evaluate",
                "--bundle",
                str(bundle),
                "--output",
                str(destination),
            ],
            env=env,
            check=True,
        )
    summary = []
    for _, _, path in runs:
        t = json.loads((path / "training.json").read_text())
        e = json.loads((path / "evaluation.json").read_text())
        summary.append(
            {
                "variant": t["variant"],
                "seed": t["seed"],
                "train_documents": t["train_documents"],
                "epochs": t["epochs"],
                "best_dev_f1": t["best_dev_f1"],
                "seconds": t["seconds"],
                "model_digest": digest(json.dumps(t["model_sha256"], sort_keys=True)),
                "commercial": {
                    split: {
                        m: {
                            k: report[k]
                            for k in (
                                "commercial_furniture_n",
                                "full_exact",
                                "full_exact_accuracy",
                                "wilson95",
                                "false_proposals",
                                "contract_failures",
                                "latency_ms",
                            )
                        }
                        for m, report in value["models"].items()
                    }
                    for split, value in e["splits"].items()
                },
            }
        )
    dump(
        output / "aggregate.json",
        {"runs": summary, "promotion": False, "external_test": False, "human_gold": False},
    )
    protect(output)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("mode", choices=["run", "train", "evaluate"])
    p.add_argument("--bundle", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--variant")
    p.add_argument("--seed", type=int)
    args = p.parse_args()
    if args.mode == "run":
        run_all(args.bundle, args.output)
    elif args.mode == "train":
        train(args.bundle, args.output, args.variant, args.seed)
    else:
        evaluate(args.bundle, args.output)


if __name__ == "__main__":
    main()
