"""Actual v13 evaluation worker in a separate wheel-only interpreter."""

import json
import os
import resource
import time
from copy import deepcopy
from pathlib import Path

from training.benchmark_campo.pipeline import digest, private_path, write_private
from training.offline_rc2_v13.protocol import config, load_split, references, runtime, tree_hash


def reconcile(a, b, model_version):
    """A supplies structure. B can veto conflicting fields, never invent missing ones.

    Reuses the existing NER assembler as B; deliberately does not reuse its hybrid
    which can inherit NER quantity/price when rules abstain. No relation-by-position.
    """
    out = deepcopy(a)
    conflicts = []
    item, other = out["item_proposal"], b["item_proposal"]
    if item and other:
        if (item["name"] or "").casefold() != (other["name"] or "").casefold():
            conflicts.append("PRODUCT_DISAGREEMENT")
            out.update(item_proposal=None, status="NO_PROPOSAL", proposed_item_count=0)
            out["warnings"].append(
                {
                    "code": "NO_PRODUCT",
                    "path": "",
                    "severity": "REVIEW",
                    "message": "Offline engines disagree on the product; no proposal.",
                }
            )
            for c in out["candidates"]:
                c["component_ref"] = None
        else:
            quantity_conflict = (
                item["quantity"] is not None
                and other["quantity"] is not None
                and item["quantity"] != other["quantity"]
            )
            currency_conflict = any(
                w["code"] == "UNSUPPORTED_CURRENCY" for r in (a, b) for w in r["warnings"]
            )
            price_conflict = (
                item["price"] is not None
                and other["price"] is not None
                and any(
                    item["price"].get(k) != other["price"].get(k)
                    for k in ("mode", "currency", "stated_amount")
                )
            )
            labels = set()
            if quantity_conflict:
                conflicts.append("QUANTITY_DISAGREEMENT")
                item["quantity"] = None
                labels.add("CANTIDAD")
                out["warnings"].append(
                    {
                        "code": "NO_QUANTITY",
                        "path": "/item_proposal/quantity",
                        "severity": "REVIEW",
                        "message": "Offline quantity conflict; abstain.",
                    }
                )
            if quantity_conflict or currency_conflict or price_conflict:
                item["price"] = None  # Also invalidates any derived total/reference.
                labels.update({"PRECIO", "PRECIO_TOTAL", "PRECIO_UNITARIO"})
            if currency_conflict:
                conflicts.append("CURRENCY_CONFLICT")
            if price_conflict:
                conflicts.append("PRICE_DISAGREEMENT")
            for c in out["candidates"]:
                if c["label"] in labels:
                    c["decision"] = "UNRESOLVED"
                    if c["candidate_id"] not in item["unresolved"]:
                        item["unresolved"].append(c["candidate_id"])
    elif item and any(w["code"] == "UNSUPPORTED_CURRENCY" for w in b["warnings"]):
        item["price"] = None
        conflicts.append("CURRENCY_CONFLICT")
    if conflicts:
        out["warnings"].append(
            {
                "code": "CONFLICTING_VALUES",
                "path": "",
                "severity": "REVIEW",
                "message": "Offline NER/rules conflict; no field inferred.",
            }
        )
    used = {c["candidate_id"] for c in out["candidates"]}
    for i, c in enumerate(b["candidates"]):
        c = deepcopy(c)
        identifier = "offline-ner-" + str(i)
        while identifier in used:
            identifier += "-x"
        used.add(identifier)
        c.update(
            candidate_id=identifier,
            component_ref=None,
            decision="REJECTED",
            reason="Auxiliary NER audit; never a naive union of accepted fields.",
        )
        out["candidates"].append(c)
    out["engine"] = {
        "mode": "HYBRID",
        "rules_version": "offline-v13-ner-veto-v1",
        "normalization_version": "1.0",
        "model_version": model_version,
    }
    return out, conflicts


def evidence(result, labels, raw=False):
    spans = set()
    unmapped = set()
    for c in result["candidates"]:
        if not raw and c["decision"] != "ACCEPTED":
            continue
        label = c["label"]
        if (
            label == "PRECIO"
            and result.get("item_proposal")
            and result["item_proposal"].get("price")
        ):
            label = (
                "PRECIO_UNITARIO"
                if result["item_proposal"]["price"]["mode"] == "PRECIO_UNITARIO"
                else "PRECIO_TOTAL"
            )
        if label not in labels:
            unmapped.add(label)
            continue
        spans.add((c["start"], c["end"], label))
    return sorted(spans), sorted(unmapped)


def evaluate(wheel, model_run, output):
    if os.environ.get("CI") or os.environ.get("HOMEX_DATA_GATE_NO_TRAINING"):
        raise RuntimeError("HEAVY_MODEL_EVALUATION_OFFLINE_ONLY")
    private_path(output)
    if output.exists():
        raise ValueError("NO_OVERWRITE_EVALUATION")
    provenance = runtime(wheel)
    training = json.loads((model_run / "training.json").read_text())
    if (
        training["protocol_digest"] != digest(config())
        or training["model_files"] != tree_hash(model_run / "model-final")
        or training["training_ids"] != [r["id"] for r in load_split("train")]
        or training["dev_documents_seen_by_optimizer"] != 0
    ):
        raise ValueError("MODEL_OR_TRAINING_PROVENANCE")
    rows, refs = load_split("dev"), references("dev")
    from homex_nlp.contracts import ExtractionRequest, ExtractionResult
    from homex_nlp.engine import RulesEngine
    from training.experimental_engines import NerExperimentalEngine

    labels = json.loads(
        (Path(__file__).resolve().parents[2] / "data/manifests/prf04_labels.json").read_text()
    )["labels"]
    start = time.perf_counter()
    a = RulesEngine()
    rules_load = time.perf_counter() - start
    start = time.perf_counter()
    b = NerExperimentalEngine(model_run / "model-final")
    ner_load = time.perf_counter() - start
    predictions, latencies = [], []
    for index, row in enumerate(rows):
        currency = refs[row["id"]]["comercial"].get("moneda_codigo") or "BOB"
        request = ExtractionRequest(
            request_id=row["id"], text=row["text"], currency_context=currency
        )
        result, elapsed, errors = {}, {}, {}
        for name, engine in (("A", a), ("B", b)):
            start = time.perf_counter()
            try:
                r = engine.extract(request)
                result[name] = ExtractionResult.model_validate(r.model_dump()).model_dump(
                    mode="json"
                )
            except (ValueError, TypeError) as exc:
                errors[name] = type(exc).__name__
                result[name] = None
            elapsed[name] = (time.perf_counter() - start) * 1000
        if result["A"] is None:
            raise ValueError("AUTHENTIC_BASELINE_CONTRACT_FAILED")
        if result["A"]["engine"]["rules_version"] != "prf04-rules-v13":
            raise ValueError("BASELINE_CHANGED_VERSION")
        conflicts = []
        start = time.perf_counter()
        if result["B"] is not None:
            c, conflicts = reconcile(result["A"], result["B"], b.model_version)
            try:
                result["C"] = ExtractionResult.model_validate(c).model_dump(mode="json")
            except (ValueError, TypeError):
                result["C"] = None
                errors["C"] = "NOT_EVALUABLE_CONTRACT"
        else:
            result["C"] = None
            errors["C"] = "NOT_EVALUABLE_B_DEPENDENCY"
        elapsed["C"] = elapsed["A"] + elapsed["B"] + (time.perf_counter() - start) * 1000
        ner, unmapped = {}, {}
        for name, r in result.items():
            if r is not None:
                ner[name], unmapped[name] = evidence(r, labels, raw=name == "B")
                r.pop("latency_nlp_ms", None)  # Dynamic performance excluded from quality hash.
        predictions.append(
            {
                "id": row["id"],
                "text_sha256": row["text_sha256"],
                "currency_context": currency,
                "results": result,
                "ner": ner,
                "unmapped_labels": unmapped,
                "errors": errors,
                "hybrid_conflicts": conflicts,
            }
        )
        latencies.append(
            {
                "id": row["id"],
                "phase": "first_dev_call" if index == 0 else "warm",
                "milliseconds": elapsed,
            }
        )
    output.mkdir(mode=0o700, parents=True)
    quality = {
        "schema": "offline-predictions-1",
        "protocol_digest": digest(config()),
        "v13": {k: v for k, v in provenance.items() if k != "import_path_private"},
        "model_files_digest": digest(training["model_files"]),
        "rows": predictions,
    }
    write_private(output / "predictions.json", quality)
    write_private(
        output / "performance.json",
        {
            "load_seconds": {"A": rules_load, "B": ner_load},
            "latencies": latencies,
            "process_peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            "model_bytes": sum(
                p.stat().st_size for p in (model_run / "model-final").rglob("*") if p.is_file()
            ),
            "method": "perf_counter; C=A+B+merge sequential composite; first dev call after provenance probe; A global rules may be primed; no ASR cold-start claim; process peak RSS includes Python/imports/all models, not marginal engine RAM",
        },
    )
    return quality
