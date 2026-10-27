"""Fixed-budget V1 development diagnostic; no test evaluation or promotion."""

import argparse
import json
import math
import platform
from collections import Counter
from hashlib import sha256
from pathlib import Path
from time import perf_counter_ns

import spacy

from homex_nlp.contracts import ExtractionRequest, ExtractionResult
from homex_nlp.engine import RulesEngine
from training.corpus import read_jsonl
from training.experimental_engines import NerExperimentalEngine


def metrics(reference, predicted, labels):
    if len(reference) != len(predicted):
        raise ValueError("UNEQUAL_DOCUMENTS")
    universe = sorted(set(labels) | {e[2] for spans in predicted for e in spans})
    by_label = {}
    totals = Counter()
    for label in universe:
        tp = fp = fn = support = 0
        for wanted, actual in zip(reference, predicted):
            a = {tuple(e) for e in wanted if e[2] == label}
            b = {tuple(e) for e in actual if e[2] == label}
            tp += len(a & b)
            fp += len(b - a)
            fn += len(a - b)
            support += bool(a)
        by_label[label] = score(tp, fp, fn) | {"documents_with_reference": support}
        totals.update(tp=tp, fp=fp, fn=fn)
    active = [v for v in by_label.values() if v["tp"] + v["fp"] + v["fn"]]
    macro = {}
    for key in ("precision", "recall", "f1"):
        defined = [v[key] for v in active if v[key] is not None]
        macro[key] = {
            "value": sum(defined) / len(defined) if defined else None,
            "labels": len(defined),
        }
    return {
        "documents": len(reference),
        "by_label": by_label,
        "micro": score(totals["tp"], totals["fp"], totals["fn"]),
        "macro": macro,
    }


def score(tp, fp, fn):
    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": tp / (tp + fp) if tp + fp else None,
        "recall": tp / (tp + fn) if tp + fn else None,
        "f1": 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else None,
    }


def latency(values):
    ordered = sorted(values)
    return {
        "n": len(values),
        "p50_ms": ordered[math.ceil(0.50 * len(values)) - 1],
        "p95_ms": ordered[math.ceil(0.95 * len(values)) - 1],
        "method": "nearest_rank",
        "scope": "warm_extraction_only",
    }


def accepted(result):
    spans = set()
    for c in result.candidates:
        if c.decision != "ACCEPTED":
            continue
        label = c.label
        if label == "PRECIO":
            price = result.item_proposal.price if result.item_proposal else None
            label = (
                ("PRECIO_UNITARIO" if price.mode == "PRECIO_UNITARIO" else "PRECIO_TOTAL")
                if price
                else "PRECIO_UNMAPPED"
            )
        spans.add((c.start, c.end, label))
    return spans


def evaluate(model, output):
    rows = [
        r for _, r in read_jsonl(Path("data/corpus/muebles_pedido.jsonl")) if r["split"] == "dev"
    ]
    labels = json.loads(Path("data/manifests/prf04_labels.json").read_text())["labels"]
    reference = [r["entities"] for r in rows]
    requests = [
        ExtractionRequest(
            request_id=r["id"], text=r["text"], currency_context=r["metadata"]["moneda"]
        )
        for r in rows
    ]
    started = perf_counter_ns()
    ner = NerExperimentalEngine(model)
    load_ms = (perf_counter_ns() - started) / 1e6
    engines = {"A_RULES_ONLY": RulesEngine(), "B_NER_ASSEMBLER": ner}
    results = {}
    for name, engine in engines.items():
        for request in requests[:5]:
            engine.extract(request)
        predictions, times, valid = [], [], 0
        for repeat in range(3):
            for request in requests:
                started = perf_counter_ns()
                result = engine.extract(request)
                times.append((perf_counter_ns() - started) / 1e6)
                ExtractionResult.model_validate_json(result.model_dump_json())
                valid += 1
                if repeat == 0:
                    predictions.append(accepted(result))
        results[name] = {
            "accepted_evidence": metrics(reference, predictions, labels),
            "latency": latency(times),
            "contract_valid": valid,
            "contract_denominator": len(times),
        }
    raw = [{(e.start_char, e.end_char, e.label_) for e in ner.nlp(r["text"]).ents} for r in rows]
    results["B_NER_ASSEMBLER"]["raw_statistical_spans"] = metrics(reference, raw, labels)
    model_files = {
        str(p.relative_to(model)): sha256(p.read_bytes()).hexdigest()
        for p in sorted(model.rglob("*"))
        if p.is_file()
    }
    report = {
        "format": "homex-dev-diagnostic-1",
        "dataset": "V1_675",
        "scope": "muebles_pedido_dev_62",
        "references": "SYNTHETIC_PREANNOTATION_NOT_HUMAN_GOLD",
        "test_scored": False,
        "promotion": False,
        "wer": None,
        "comparison_limit": "accepted evidence includes assembler abstention; raw NER reported separately",
        "independence": "UNVERIFIED_TEMPLATE_SIMILARITY_RISK",
        "timing": {
            "ner_load_ms": load_ms,
            "warmups_per_engine": 5,
            "passes": 3,
            "order": list(engines),
            "concurrency": 1,
            "e2e": False,
        },
        "environment": {
            "python": platform.python_version(),
            "spacy": spacy.__version__,
            "machine": platform.machine(),
            "platform": platform.system(),
            "processor": platform.processor(),
        },
        "model_files_sha256": model_files,
        "data_sha256": {
            str(p): sha256(p.read_bytes()).hexdigest()
            for p in (
                Path("data/corpus/muebles_pedido.jsonl"),
                Path("data/splits/muebles_pedido.json"),
                Path("uv.lock"),
            )
        },
        "variants": results,
    }
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("model", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("OUTPUT_EXISTS")
    evaluate(args.model, args.output)


if __name__ == "__main__":
    main()
