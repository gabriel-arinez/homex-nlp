"""Frozen-model comparison only; private inputs/outputs, never training or runtime edits."""

import argparse
import json
import resource
import statistics
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

from homex_nlp.contracts import ExtractionRequest, ExtractionResult
from homex_nlp.engine import RulesEngine
from training.canonical_v2 import experiment as base
from training.canonical_v2.commercial import compare_fields, predicted_fields, reference_fields
from training.canonical_v2.io import digest, dump, jsonl, private_path, protect, read
from training.canonical_v2.reconcile import evidence
from training.integral_v2.assembler import IntegralNerEngine
from training.integral_v2.experiment import hybrid, preflight
from training.integral_v2.project import compare, fields, project
from training.integral_v2.validate import validate_bundle

CRITICAL = {
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


def critical(key):
    return key in CRITICAL or key.startswith("dimension:")


def wilson(success, n):
    if not n:
        return None
    z = 1.96
    p = success / n
    den = 1 + z * z / n
    center = (p + z * z / (2 * n)) / den
    radius = z * (p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5 / den
    return [max(0, center - radius), min(1, center + radius)]


def field_errors(wanted, actual):
    return [
        {
            "scope": scope,
            "field": key,
            "expected": wanted.get((scope, key)),
            "actual": actual.get((scope, key)),
            "kind": "omission"
            if (scope, key) not in actual
            else "false_assertion"
            if (scope, key) not in wanted
            else "wrong_value_or_scope",
        }
        for scope, key in sorted(set(wanted) | set(actual))
        if wanted.get((scope, key)) != actual.get((scope, key))
    ]


def logical(result):
    """Full deterministic output comparison: no engine fields are dropped."""
    return result.model_dump(mode="json")


def instrument(engine, request):
    start = time.perf_counter()
    doc = engine.nlp(request.text)
    spans = [(e.start_char, e.end_char, e.label_) for e in doc.ents]
    ner_ms = (time.perf_counter() - start) * 1000
    start = time.perf_counter()
    result = engine.assemble(request, spans)
    assembly_ms = (time.perf_counter() - start) * 1000
    # Instrumentation must be observational, not a different mechanism.
    assert logical(result) == logical(engine.extract(request)), "INSTRUMENTATION_CHANGED_ENGINE"
    return result, spans, ner_ms, assembly_ms


def metrics(rows):
    """Each subset/mechanism is aggregated once, never pooling train/dev/test."""
    evaluated = [r for r in rows if r["commercial_evaluable"]]
    positives = [r for r in evaluated if not r["negative"]]
    n = len(positives)
    negatives = sum(r["negative"] for r in evaluated)
    fp = sum(r["negative"] and r["has_proposal"] for r in evaluated)
    exact = sum(r["full_exact"] for r in positives)
    counters = {}
    for r in evaluated:
        for key, counts in r["counts"].items():
            counters.setdefault(key, Counter()).update(counts)
    labels = [r for r in rows if r["ner_evaluable"]]
    raw = (
        base.ner_metrics([r["input"] for r in labels], [r["raw"] for r in labels])
        if labels
        else None
    )
    accepted = (
        base.ner_metrics([r["input"] for r in labels], [r["accepted"] for r in labels])
        if labels
        else None
    )
    return {
        "entries": len(rows),
        "commercial_n": len(evaluated),
        "positive_full_n": n,
        "full_exact": exact,
        "full_exact_ratio": exact / n if n else None,
        "wilson95": wilson(exact, n),
        "negative_n": negatives,
        "false_proposals": fp,
        "correct_negative_abstentions": sum(
            r["negative"] and not r["has_proposal"] and not r["contract_failure"] for r in evaluated
        ),
        "no_proposal": sum(not r["has_proposal"] for r in rows),
        "requires_review": sum(r["status"] == "REQUIRES_REVIEW" for r in rows),
        "fields": {k: dict(v) for k, v in counters.items()},
        "critical_fp": sum(v["fp"] for k, v in counters.items() if critical(k)),
        "critical_fn": sum(v["fn"] for k, v in counters.items() if critical(k)),
        "raw_ner": raw,
        "accepted_ner": accepted,
        "literal_offset_violations": sum(r["literal_offset_violations"] for r in rows),
        "currency_context_violations": sum(r["currency_context_violations"] for r in rows),
        "contract_failures": sum(r["contract_failure"] for r in rows),
        "projection_failures": sum(r["projection_failure"] for r in rows),
        "legacy_16": {
            "n": sum(r["legacy_evaluable"] for r in rows),
            "exact": sum(r["legacy_exact"] for r in rows),
        },
        "latency_ms": {
            key: {
                "n": len(rows),
                "first": rows[0][key] if rows else None,
                "warm_p50": statistics.median([r[key] for r in rows[1:]])
                if len(rows) > 1
                else None,
                "warm_p95": base.pct([r[key] for r in rows[1:]], 0.95),
            }
            for key in ["nlp_ms", "assembly_ms", "reconciliation_ms", "projection_ms"]
        },
        "causal_events": dict(sum((Counter(r["causes"]) for r in rows), Counter())),
        "ner_n": len(labels),
    }


def causal(row, raw, accepted, errors, result):
    causes = Counter()
    if row.get("entities") is not None:
        gold = {tuple(e) for e in row["entities"]}
        predicted = {tuple(e) for e in raw}
        for a, b, label in gold - predicted:
            causes[
                "entity_wrong_class"
                if any(x[:2] == (a, b) for x in predicted)
                else "entity_missing_or_boundary"
            ] += 1
        causes["gold_entity_rejected_event_not_always_error"] += len(
            gold & predicted - {tuple(e) for e in accepted}
        )
    for error in errors:
        key = error["field"]
        if key in {"material", "color", "espesor", "conjunto", "cantidad_interna"}:
            causes["scoped_relation_or_attribute_error"] += 1
        elif key.startswith("dimension:"):
            causes["axis_unit_or_dimension_error"] += 1
        elif key == "cantidad":
            causes["commercial_quantity_error"] += 1
        elif key.startswith("precio") or key == "descuento_linea":
            causes["commercial_price_or_discount_error"] += 1
        else:
            causes["other_field_" + error["kind"]] += 1
    if result is not None:
        for warning in result.warnings:
            if warning.code in {"MISSING_UNIT", "MISSING_AXIS"}:
                causes["unresolved_axis_or_unit_warning"] += 1
    if row.get("reference_kind") in {
        "NO_INDEPENDENT_AUDIO_REFERENCE",
        "PLANNED_SCRIPT_NOT_AUDIO_GOLD",
    }:
        causes["reference_not_independent_of_intended_script"] += 1
    return dict(causes)


def evaluate_rows(inputs, engine_name, ner=None):
    rule = RulesEngine()
    outputs = []
    for row in inputs:
        req = ExtractionRequest(request_id=row["id"], text=row["text"], currency_context="BOB")
        start = time.perf_counter()
        ar = rule.extract(req)
        rule_ms = (time.perf_counter() - start) * 1000
        spans = []
        assembly_ms = reconciliation_ms = 0.0
        engine_error = None
        contract_failure = False
        if engine_name == "M-A":
            result = ar
            elapsed = rule_ms
            spans = evidence(logical(ar), base.LABELS, raw=True)[0]
        else:
            br, spans, ner_ms, assembly_ms = instrument(ner, req)
            result = br
            elapsed = ner_ms + assembly_ms
            if engine_name == "M-C":
                start = time.perf_counter()
                try:
                    result = hybrid(ar, br, ner.model_version)
                except (ValueError, TypeError, KeyError) as exc:
                    result = None
                    engine_error = {"stage": "hybrid_reconciliation", "error": repr(exc)}
                    contract_failure = True
                reconciliation_ms = (time.perf_counter() - start) * 1000
                elapsed += rule_ms + reconciliation_ms
        projection_failure = False
        try:
            if result is not None:
                ExtractionResult.model_validate(logical(result))
                assert result.text_original == row["text"]
        except (ValueError, AssertionError):
            contract_failure = True
        start = time.perf_counter()
        try:
            projected = project(logical(result)) if result is not None else None
        except (ValueError, TypeError, KeyError):
            projected = None
            projection_failure = True
        projection_ms = (time.perf_counter() - start) * 1000
        accepted = evidence(logical(result), base.LABELS)[0] if result is not None else []
        commercial_evaluable = (
            row.get("expected") is not None and row["category"] == "muebles_pedido"
        )
        counts = {}
        errors = []
        exact = False
        negative = False
        if commercial_evaluable:
            wanted = fields(row["expected"])
            actual = fields(projected) if projected else {}
            counts = compare(wanted, actual)
            errors = field_errors(wanted, actual)
            negative = row["expected"].get("status") == "NO_PROPOSAL" or not row["expected"].get(
                "comercial", {}
            ).get("nombre")
            exact = not errors
        legacy = row["subset"] == "known_synthetic_dev" and row["category"] == "muebles_pedido"
        legacy_exact = False
        if legacy:
            wanted, reviewed = reference_fields(row["expected"])
            counts_old = compare_fields(
                wanted, predicted_fields(logical(result)) if result is not None else {}, reviewed
            )
            legacy_exact = all(
                not c["omission"] and not c["false_assertion"] for c in counts_old.values()
            )
        item = result.item_proposal if result is not None else None
        outputs.append(
            {
                "id": row["id"],
                "subset": row["subset"],
                "category": row["category"],
                "text_sha256": digest(row["text"]),
                "input": {"entities": row.get("entities")},
                "result": logical(result) if result is not None else None,
                "engine_error": engine_error,
                "projection": projected,
                "raw": spans,
                "accepted": accepted,
                "status": result.status if result is not None else "ENGINE_ERROR",
                "commercial_evaluable": commercial_evaluable,
                "ner_evaluable": row.get("entities") is not None,
                "negative": bool(negative),
                "has_proposal": item is not None,
                "counts": counts,
                "field_errors": errors,
                "full_exact": exact,
                "legacy_evaluable": legacy,
                "legacy_exact": legacy_exact,
                "literal_offset_violations": sum(
                    row["text"][c.start : c.end] != c.text
                    for c in (result.candidates if result is not None else [])
                ),
                "currency_context_violations": int(
                    bool(item and item.price and item.price.currency != "BOB")
                ),
                "contract_failure": contract_failure,
                "projection_failure": projection_failure,
                "nlp_ms": elapsed,
                "assembly_ms": assembly_ms,
                "reconciliation_ms": reconciliation_ms,
                "projection_ms": projection_ms,
                "causes": causal(row, spans, accepted, errors, result)
                | ({"hybrid_reconciliation_contract_failure": 1} if engine_error else {}),
            }
        )
    return outputs


def run(bundle, models, inputs_path, output):
    private_path(output)
    if output.exists():
        raise ValueError("EVALUATION_OUTPUT_EXISTS")
    output.mkdir(mode=0o700, parents=True)
    validate_bundle(bundle, training=True)
    inputs = read(inputs_path)
    if len({r["id"] for r in inputs}) != len(inputs):
        raise ValueError("DUPLICATE_INPUT_ID")
    sealed = preflight(bundle)
    inventory = []
    for variant in ["D1", "D2", "D3", "D4", "D4W"]:
        for seed in [404, 405]:
            p = models / f"{variant}-{seed}"
            t = json.loads((p / "training.json").read_text())
            if t["sealed"] != sealed or base.sha_tree(p / "model-best") != t["model_sha256"]:
                raise ValueError("CHECKPOINT_OR_FROZEN_CODE_CHANGED")
            inventory.append(
                {
                    "variant": variant,
                    "seed": seed,
                    "checkpoint": str(p / "model-best"),
                    "model_digest": digest(json.dumps(t["model_sha256"], sort_keys=True)),
                    "training_code_revision": t["code_revision"],
                }
            )
    dump(output / "inventario_modelos.json", inventory)
    dump(
        output / "protocol.json",
        {
            "source_inputs_sha256": digest(inputs_path.read_bytes()),
            "evaluations": 21,
            "same_text_for_all": True,
            "new_training": False,
            "currency_context": "BOB",
            "source_code_sha256": digest(Path(__file__).read_bytes()),
            "subset_sizes": dict(Counter(r["subset"] for r in inputs)),
            "selection": "commercial safety, structured quality, coverage, cost, maintainability; conservative tie-break",
            "frozen_training_preflight": sealed,
        },
    )
    names = ["M-A"] + [
        m + "-" + r["variant"] + "-" + str(r["seed"]) for r in inventory for m in ["M-B", "M-C"]
    ]
    summaries = []
    for name in names:
        start = time.perf_counter()
        subprocess.run(
            [
                sys.executable,
                "-m",
                "training.decision_nlp",
                "--bundle",
                str(bundle),
                "--models",
                str(models),
                "--inputs",
                str(inputs_path),
                "--output",
                str(output),
                "--worker",
                name,
            ],
            check=True,
        )
        summary = json.loads((output / (name + "-summary.json")).read_text())
        summary["worker_wall_seconds"] = time.perf_counter() - start
        summaries.append(summary)
    dump(
        output / "resultados_comparativos.json",
        {
            "runs": summaries,
            "not_blind": True,
            "human_gold": False,
            "new_training": False,
            "source_inputs_sha256": digest(inputs_path.read_bytes()),
        },
    )
    protect(output)


def worker(inputs_path, output, name):
    inventory = json.loads((output / "inventario_modelos.json").read_text())
    mechanism = name[:3]
    info = next(
        (r for r in inventory if name == mechanism + "-" + r["variant"] + "-" + str(r["seed"])),
        None,
    )
    if name != "M-A" and info is None:
        raise ValueError("UNKNOWN_FROZEN_MODEL")
    inputs = read(inputs_path)
    start = time.perf_counter()
    engine = IntegralNerEngine(Path(info["checkpoint"])) if info else RulesEngine()
    load_seconds = time.perf_counter() - start
    data = evaluate_rows(inputs, mechanism, engine if info else None)
    jsonl(output / (name + "-predictions.jsonl"), data)
    summary = {
        "name": name,
        "mechanism": mechanism,
        "variant": info["variant"] if info else None,
        "seed": info["seed"] if info else None,
        "load_seconds": load_seconds,
        "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "memory_scope": "fresh process peak including imports, not marginal model allocation",
        "subsets": {
            s: metrics([r for r in data if r["subset"] == s])
            for s in sorted({r["subset"] for r in inputs})
        },
    }
    dump(output / (name + "-summary.json"), summary)
    print(name, "PASS", len(data), flush=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ["bundle", "models", "inputs", "output"]:
        p.add_argument("--" + name, type=Path, required=True)
    p.add_argument("--worker")
    a = p.parse_args()
    if a.worker:
        worker(a.inputs, a.output, a.worker)
    else:
        run(a.bundle, a.models, a.inputs, a.output)


if __name__ == "__main__":
    main()
