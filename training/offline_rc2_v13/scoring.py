"""Public aggregate counts only; private field diffs, fixed technical references."""

import re
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path

from training.benchmark_campo.metrics import ner_counts, ner_report, prf, ratio, stats
from training.benchmark_campo.models import Span
from training.benchmark_campo.pipeline import digest
from training.offline_rc2_v13.protocol import check_runtime, config

ROOT_FIELDS = {
    "nombre": "product",
    "cantidad": "sold_quantity",
    "unidad_codigo": "unit",
    "precio_unitario": "unit_price",
    "precio_total_explicito": "total_price",
}
AXES = {"alto", "ancho", "largo", "profundidad", "diametro"}


def literal(value):
    return " ".join(str(value).casefold().split())


def numeric(value):
    if not re.fullmatch(r"\d+(?:[.,]\d+)?", str(value)):
        raise ValueError("AMBIGUOUS_NUMERIC_REFERENCE")
    return format(Decimal(str(value).replace(",", ".")).normalize(), "f")


def measurement(value):
    if isinstance(value, dict):
        amount, unit = value.get("valor"), value.get("unidad")
    else:
        match = re.fullmatch(r"\s*([\d.,]+)\s*(mm|cm|m)\s*", str(value), re.I)
        if not match:
            raise ValueError("NOT_EVALUABLE_MEASUREMENT")
        amount, unit = match[1], match[2].lower()
    if unit not in {"mm", "cm", "m"}:
        raise ValueError("NOT_EVALUABLE_UNIT")
    return numeric(amount), unit


def component_scope(name):
    return "COMP-" + digest(literal(name))[:16]


def reference_fields(ref):
    fields = {}
    reviewed = {("ITEM", field) for field in ROOT_FIELDS.values()}
    for key, field in ROOT_FIELDS.items():
        value = ref["comercial"].get(key)
        if value is not None:
            fields["ITEM", field] = (
                numeric(value)
                if field in {"sold_quantity", "unit_price", "total_price"}
                else literal(value)
            )
    technical = ref.get("especificacion", {}).get("datos_tecnicos", {})
    components = technical.get("componentes", [])
    if len({literal(c["nombre"]) for c in components}) != len(components):
        raise ValueError("NOT_EVALUABLE_AMBIGUOUS_COMPONENT_NAMES")
    for c in components:
        scope = component_scope(c["nombre"])
        fields[scope, "component_name"] = literal(c["nombre"])
        for field in ("material", "color", "acabado", "espesor"):
            if c.get(field) is not None:
                fields[scope, field] = (
                    measurement(c[field]) if field == "espesor" else literal(c[field])
                )
        for axis, value in c.get("dimensiones", {}).items():
            if axis in AXES:
                fields[scope, "dimension_" + axis] = measurement(value)
    for axis, value in (
        technical.get("caracteristicas_generales", {}).get("dimensiones", {}).items()
    ):
        if axis in AXES:
            fields["ITEM", "dimension_" + axis] = measurement(value)
    for accessory in technical.get("accesorios", []):
        if not isinstance(accessory, str):
            raise ValueError("NOT_EVALUABLE_ACCESSORY_REFERENCE")
        fields["ACCESSORY-" + digest(literal(accessory))[:16], "accessory_name"] = literal(
            accessory
        )
    reviewed.update(fields)
    return fields, reviewed


def assign(fields, key, value):
    if key in fields and fields[key] != value:
        raise ValueError("NOT_EVALUABLE_AMBIGUOUS_PREDICTED_FIELD")
    fields[key] = value


def predicted_fields(result):
    fields = {}
    item = result.get("item_proposal")
    if not item:
        return fields
    for key, field in (("name", "product"), ("quantity", "sold_quantity")):
        if item.get(key) is not None:
            fields["ITEM", field] = (
                numeric(item[key]) if field == "sold_quantity" else literal(item[key])
            )
    price = item.get("price")
    if price:
        if price["mode"] == "PRECIO_UNITARIO":
            fields["ITEM", "unit_price"] = numeric(price["unit_price_input"])
        else:
            fields["ITEM", "total_price"] = numeric(price["line_total"])
    units = {
        c["normalized_value"]
        for c in result["candidates"]
        if c["label"] == "UNIDAD_MEDIDA"
        and c["decision"] == "ACCEPTED"
        and isinstance(c.get("normalized_value"), str)
    }
    if len(units) == 1:
        fields["ITEM", "unit"] = literal(next(iter(units)))
    components = {c["component_id"]: component_scope(c["name"]) for c in item["components"]}
    if len(set(components.values())) != len(components):
        raise ValueError("NOT_EVALUABLE_DUPLICATE_COMPONENT_NAMES")
    for c in item["components"]:
        fields[components[c["component_id"]], "component_name"] = literal(c["name"])
    for c in result["candidates"]:
        if c["decision"] == "ACCEPTED" and c["label"] in {"MATERIAL", "COLOR", "ACABADO"}:
            scope = components.get(c.get("component_ref"), "ITEM")
            assign(fields, (scope, c["label"].lower()), literal(c["text"]))
    for d in item["dimensions"]:
        if d.get("axis") and d.get("unit"):
            fields[components.get(d.get("component_ref"), "ITEM"), "dimension_" + d["axis"]] = (
                numeric(d["value"]),
                d["unit"],
            )
    for d in item["thicknesses"]:
        if d.get("unit"):
            fields[components.get(d.get("component_ref"), "ITEM"), "espesor"] = (
                numeric(d["value"]),
                d["unit"],
            )
    for accessory in item["accessories"]:
        fields["ACCESSORY-" + digest(literal(accessory["name"]))[:16], "accessory_name"] = literal(
            accessory["name"]
        )
    return fields


def compare_fields(wanted, actual, reviewed):
    counts = defaultdict(Counter)
    # Root negatives are explicitly scoped; observed extra relation assertions are
    # scored under RC2's SIN_EVIDENCIA_NO_COMPLETAR policy, never whole-universe TN.
    for key in reviewed | set(wanted) | set(actual):
        a, b = wanted.get(key), actual.get(key)
        row = counts[key[1]]
        row["opportunities"] += 1
        row["positive_reference"] += a is not None
        row["positive_prediction"] += b is not None
        correct = a is not None and b is not None and a == b
        row["correct"] += correct
        row["omission"] += a is not None and not correct
        row["false_assertion"] += b is not None and not correct
        row["safe_abstention"] += a is None and b is None
    return {k: dict(v) for k, v in counts.items()}


def summarize(rows, refs, predictions, *, ner_view=None):
    """Default preserves historical mixed-view numbers; explicit views are post hoc.

    Same-view NER is reconstructed from sealed DTO candidates through the original
    adapter, never from the historical A-accepted/B-raw cached ``ner`` member.
    """
    if ner_view not in {None, "accepted", "all_candidates"}:
        raise ValueError("UNKNOWN_NER_VIEW")
    if ner_view is not None:
        import json

        from training.offline_rc2_v13.protocol import ROOT
        from training.offline_rc2_v13.worker import evidence

        labels = json.loads((ROOT / "data/manifests/prf04_labels.json").read_text())["labels"]
    check_runtime(predictions["v13"])
    if predictions["protocol_digest"] != digest(config()):
        raise ValueError("SCORING_PROTOCOL_CHANGED")
    if any(
        p["results"]["A"]["engine"]["rules_version"] != "prf04-rules-v13"
        for p in predictions["rows"]
    ):
        raise ValueError("BASELINE_IS_NOT_V13")
    if [r["id"] for r in rows] != [r["id"] for r in predictions["rows"]]:
        raise ValueError("EVALUATION_MEMBERSHIP_OR_ORDER")
    for r, p in zip(rows, predictions["rows"]):
        if r["text_sha256"] != p["text_sha256"]:
            raise ValueError("EVALUATION_TEXT_CHANGED")
    result = {
        "status": "EXPERIMENTO_OFFLINE_LIMITADO_EJECUTADO",
        "HUMAN_GOLD": "NO",
        "TEST_VOZ_REAL": "NO",
        "HOLDOUT_EXTERNO": 0,
        "PROMOCION": "NO",
        "recommendation": "MANTENER_RULES_ONLY_SIN_EVIDENCIA_EXTERNA",
        "reference": "REFERENCIAS_TECNICAS_SINTETICAS_NO_HOMOLOGADAS",
        "protocol_digest": predictions["protocol_digest"],
        "prediction_digest": digest(predictions),
        "engines": {},
    }
    if ner_view is not None:
        result.update(analysis_type="SUPPLEMENTARY_POST_HOC", ner_view=ner_view)
    for engine in ("A", "B") if ner_view == "all_candidates" else ("A", "B", "C"):
        report = {}
        for family in [
            "ALL_SYNTHETIC",
            "muebles_pedido",
            "AUXILIARY_NON_VOICE",
            "otros_productos",
            "pisos_flotantes",
            "sillas",
        ]:
            selected = [
                (r, p)
                for r, p in zip(rows, predictions["rows"])
                if family == "ALL_SYNTHETIC"
                or r["category"] == family
                or family == "AUXILIARY_NON_VOICE"
                and r["category"] != "muebles_pedido"
            ]
            counts = defaultdict(lambda: [0, 0, 0])
            if ner_view is not None:
                counts.update({label: [0, 0, 0] for label in labels})
            ner_n = 0
            fields = defaultdict(Counter)
            commercial_n = 0
            failed = Counter()
            negative_n = false_proposals = safe_proposals = 0
            multiple_n = multiple_false = 0
            conflicts = Counter()
            relations = [0, 0, 0]
            currency_n = currency_errors = 0
            for r, p in selected:
                actual = p["results"].get(engine)
                conflicts.update(p["hybrid_conflicts"] if engine == "C" else [])
                if actual is None:
                    failed[p["errors"].get(engine, "NOT_EVALUABLE")] += 1
                    continue
                ner_n += 1
                gold = [Span(start=a, end=b, label=label) for a, b, label in r["entities"]]
                spans = (
                    p["ner"][engine]
                    if ner_view is None
                    else evidence(actual, labels, raw=ner_view == "all_candidates")[0]
                )
                predicted = [Span(start=a, end=b, label=label) for a, b, label in spans]
                for label, values in ner_counts(gold, predicted).items():
                    counts[label] = [a + b for a, b in zip(counts[label], values)]
                if r["category"] != "muebles_pedido":
                    continue
                ref = refs[r["id"]]
                try:
                    wanted, reviewed = reference_fields(ref)
                    observed = predicted_fields(actual)
                except ValueError:
                    failed["NOT_EVALUABLE_REFERENCE_OR_ADAPTER"] += 1
                    continue
                commercial_n += 1
                for field, cs in compare_fields(wanted, observed, reviewed).items():
                    fields[field].update(cs)
                a = {
                    (scope, field, str(value))
                    for (scope, field), value in wanted.items()
                    if scope != "ITEM"
                }
                b = {
                    (scope, field, str(value))
                    for (scope, field), value in observed.items()
                    if scope != "ITEM"
                }
                relations = [x + y for x, y in zip(relations, [len(a & b), len(b - a), len(a - b)])]
                negative = ref.get("status") == "NO_PROPOSAL" or (
                    ref["comercial"].get("nombre") is None
                )
                if negative:
                    negative_n += 1
                    false_proposals += actual["item_proposal"] is not None
                    safe_proposals += actual["item_proposal"] is None
                    if "multiproducto" in r.get("phenomena", []):
                        multiple_n += 1
                        multiple_false += actual["item_proposal"] is not None
                if actual.get("item_proposal") and actual["item_proposal"].get("price"):
                    currency_n += 1
                    currency_errors += (
                        actual["item_proposal"]["price"]["currency"] != p["currency_context"]
                    )
            by_field = {
                k: dict(v)
                | {
                    "accuracy": ratio(v["correct"], v["positive_reference"]),
                    "omission_rate": ratio(v["omission"], v["positive_reference"]),
                    "false_assertion_rate": ratio(v["false_assertion"], v["positive_prediction"]),
                }
                for k, v in sorted(fields.items())
            }
            critical_n = sum(
                v["opportunities"] for k, v in fields.items() if k != "color" and k != "acabado"
            )
            critical_errors = sum(
                v["opportunities"] - v["correct"] - v["safe_abstention"]
                for k, v in fields.items()
                if k != "color" and k != "acabado"
            )
            ner_summary = ner_report(counts, ner_n)
            eligible = [r for r, p in selected if p["results"].get(engine) is not None]
            for label, metrics in ner_summary["by_label"].items():
                metrics["reference_documents"] = sum(
                    any(e[2] == label for e in r["entities"]) for r in eligible
                )
                metrics["reference_entities"] = sum(
                    sum(e[2] == label for e in r["entities"]) for r in eligible
                )
                metrics["reference_groups"] = len(
                    {
                        r["leakage_group"]
                        for r in eligible
                        if any(e[2] == label for e in r["entities"])
                    }
                )
            report[family] = {
                "documents": len(selected),
                "entities": sum(len(r["entities"]) for r, p in selected),
                "groups": len({r["leakage_group"] for r, p in selected}),
                "ner": ner_summary,
                "commercial": {
                    "status": "EVALUABLE_TECHNICAL_SUBSET" if commercial_n else "NOT_EVALUABLE",
                    "documents": commercial_n,
                    "by_field": by_field,
                    "relations": prf(*relations),
                    "critical_errors": critical_errors,
                    "critical_opportunities": critical_n,
                    "critical_error_rate": ratio(critical_errors, critical_n),
                    "negative_documents": negative_n,
                    "false_proposals": false_proposals,
                    "safe_no_proposals": safe_proposals,
                    "multiple_product_negatives": multiple_n,
                    "multiple_product_false_proposals": multiple_false,
                    "currency_context_checks": currency_n,
                    "currency_context_errors": currency_errors,
                    "NOT_EVALUABLE": [
                        "capacity_no_reference",
                        "internal_quantity_no_contract_field",
                        "discount_no_contract_field",
                        "accessory_quantities_no_paired_references",
                        "currency_accuracy_when_reference_null",
                        "backend_projection",
                        "end_to_end_voice",
                        "human_gold",
                    ],
                },
                "not_evaluable": dict(failed),
                "hybrid_conflicts": dict(conflicts),
            }
        result["engines"][engine] = report
    return result


def performance_summary(performance):
    return {
        "load_seconds": performance["load_seconds"],
        "process_peak_rss_kib": performance["process_peak_rss_kib"],
        "model_bytes": performance["model_bytes"],
        "method": performance["method"],
        "extraction_ms": {
            e: {
                phase: stats(
                    [
                        r["milliseconds"][e]
                        for r in performance["latencies"]
                        if phase == "all" or r["phase"] == phase
                    ]
                )
                for phase in ("all", "first_dev_call", "warm")
            }
            for e in ("A", "B", "C")
        },
    }


def private_differences(rows, refs, predictions):
    """Literal case differences; caller must use an explicitly private output."""
    output = []
    for row, prediction in zip(rows, predictions["rows"]):
        record = {
            "id": row["id"],
            "family": row["category"],
            "text": row["text"],
            "reference_entities": row["entities"],
            "engines": {},
        }
        for engine in "ABC":
            actual = prediction["results"].get(engine)
            item = {
                "predicted_entities": prediction["ner"].get(engine),
                "hypothesis": "NLP_BOUNDARY_LABEL_OR_ASSEMBLY_NOT_ASR",
                "status": "NOT_EVALUABLE" if actual is None else "TECHNICAL_SYNTHETIC_ONLY",
            }
            if actual is not None and row["category"] == "muebles_pedido":
                try:
                    wanted, reviewed = reference_fields(refs[row["id"]])
                    observed = predicted_fields(actual)
                    item["field_differences"] = [
                        {
                            "scope": k[0],
                            "field": k[1],
                            "reference": wanted.get(k),
                            "prediction": observed.get(k),
                        }
                        for k in sorted(reviewed | set(wanted) | set(observed))
                        if wanted.get(k) != observed.get(k)
                    ]
                except ValueError as exc:
                    item["reason"] = str(exc)
            record["engines"][engine] = item
        output.append(record)
    return output


def comparison(evaluation_dirs, preflight):
    """Reproducible comparison command: no fitting, ranking, or model selection."""
    import json

    from training.offline_rc2_v13.protocol import load_split, references

    if len(evaluation_dirs) < 2:
        raise ValueError("TWO_INDEPENDENT_EVALUATIONS_REQUIRED")
    evaluation_dirs = [Path(directory).resolve(strict=True) for directory in evaluation_dirs]
    if len(set(evaluation_dirs)) != len(evaluation_dirs):
        raise ValueError("DUPLICATE_EVALUATION_DIRECTORY")
    plan = json.loads(preflight.read_text())
    rows, refs = load_split("dev"), references("dev")
    predictions = [json.loads((p / "predictions.json").read_text()) for p in evaluation_dirs]
    reports = [summarize(rows, refs, p) for p in predictions]
    same = all(digest(p) == digest(predictions[0]) for p in predictions)
    if not same or plan["protocol_digest"] != predictions[0]["protocol_digest"]:
        raise ValueError("REPRODUCIBILITY_OR_PROTOCOL_MISMATCH")
    performance = []
    families = {r["id"]: r["category"] for r in rows}
    for directory in evaluation_dirs:
        raw = json.loads((directory / "performance.json").read_text())
        item = performance_summary(raw)
        item["by_family"] = {
            family: {
                e: stats(
                    [r["milliseconds"][e] for r in raw["latencies"] if families[r["id"]] == family]
                )
                for e in "ABC"
            }
            for family in sorted(set(families.values()))
        }
        performance.append(item)
    return reports[0] | {
        "ner_metric_policy": "LEGACY_MIXED_VIEWS_A_C_ACCEPTED_B_RAW_NOT_A_SAME_VIEW_COMPARISON",
        "engine_provenance": predictions[0]["v13"],
        "experimental_model_digest": predictions[0]["model_files_digest"],
        "reproducibility": {
            "predictions_identical": same,
            "summaries_identical": all(digest(r) == digest(reports[0]) for r in reports),
            "model_files_identical": len({p["model_files_digest"] for p in predictions}) == 1,
            "evaluations_supplied": len(evaluation_dirs),
            "distinct_evaluation_directories": len(set(evaluation_dirs)),
            "distinct_artifacts": len(
                {
                    digest(
                        {
                            name: __import__("hashlib")
                            .sha256((directory / name).read_bytes())
                            .hexdigest()
                            for name in ("predictions.json", "performance.json")
                        }
                    )
                    for directory in evaluation_dirs
                }
            ),
            "independent_runs_verified": 0,
            "independence_status": "UNVERIFIED",
            "independence_basis": "DISTINCT_PATHS_ONLY_NO_TRUSTED_PROCESS_AND_TRAINING_CHAIN",
            # Compatibility: historical integer counted inputs, not verified processes.
            "independent_evaluation_processes": None,
            "legacy_field_note": "Historical reports counted paths; retained unchanged as historical evidence only",
            "deterministic_predictions_sha256": __import__("hashlib")
            .sha256((evaluation_dirs[0] / "predictions.json").read_bytes())
            .hexdigest(),
        },
        "performance_runs": performance,
        "hardware": plan["machine"],
        "limitations": [
            "27 synthetic dev documents, 16 operational furniture; no independent holdout",
            "A/C accepted rule evidence; B raw statistical NER includes negative predictions",
            "No dev selection: seed606/fixed20epochs/final checkpoint",
            "C is a veto-only hybrid, not an entity union; no veto triggered on this dev",
            "First dev call after provenance probe is not true cold ASR; model loading separate",
            "Timings and process RSS vary, not part of deterministic quality hash",
        ],
    }


def supplementary_comparison(evaluation_dirs, preflight):
    """Retrospective sealed-prediction analysis; never executes an engine or fit.

    Historical process logs lack IDs/timestamps bound to individual model runs;
    they cannot establish independent processes. No retrospective certificates
    are minted. Different paths/measurements are only artifact distinctions.
    """
    import hashlib
    import json

    from training.offline_rc2_v13.protocol import load_split, references

    historical = comparison(evaluation_dirs, preflight)
    rows, refs = load_split("dev"), references("dev")
    sources = [
        Path(directory).resolve(strict=True) / "predictions.json" for directory in evaluation_dirs
    ]
    predictions = json.loads(sources[0].read_text())
    views = {}
    for view in ("accepted", "all_candidates"):
        report = summarize(rows, refs, predictions, ner_view=view)
        views[view] = {
            engine: {
                family: {
                    key: metrics[key]
                    for key in ("documents", "entities", "groups", "ner", "not_evaluable")
                }
                for family, metrics in families.items()
            }
            for engine, families in report["engines"].items()
        }
    return {
        "analysis_type": "SUPPLEMENTARY_POST_HOC",
        "protocol_changed": False,
        "HUMAN_GOLD": "NO",
        "TEST_VOZ_REAL": "NO",
        "HOLDOUT_EXTERNO": 0,
        "PROMOCION": "NO",
        "protocol_digest": predictions["protocol_digest"],
        "original_predictions_sha256": [
            hashlib.sha256(source.read_bytes()).hexdigest() for source in sources
        ],
        "experimental_model_digest": predictions["model_files_digest"],
        "views": views,
        "C_raw_status": "NOT_COMPARABLE_AUDIT_REJECTED_CANDIDATES_ACCEPTED_VETO_VIEW_ONLY",
        "reproducibility": historical["reproducibility"],
        "historical_metrics": "Preserved in results.json legacy fields and commit 3dcb8d8; mixed views are not a direct NER comparison",
        "recommendation": "MANTENER_RULES_ONLY_SIN_EVIDENCIA_EXTERNA",
        "conclusion": "B raw F1 exceeds A raw; B accepted F1 is lower than A accepted on furniture; no field-accuracy claim",
    }
