"""Offline CPU experiments with fixed data hashes, dev selection and private weights."""

import argparse
import json
import os
import random
import resource
import statistics
import subprocess
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

import spacy
from spacy.training import Example
from spacy.util import fix_random_seed, minibatch

from homex_nlp.contracts import ExtractionRequest, ExtractionResult
from homex_nlp.contracts.evidence import Warning
from homex_nlp.engine import RulesEngine
from training.canonical_v2.commercial import compare_fields, predicted_fields, reference_fields
from training.canonical_v2.io import digest, dump, jsonl, private_path, protect, read
from training.canonical_v2.reconcile import evidence, reconcile
from training.canonical_v2.validate import LABELS, ROOT, validate
from training.experimental_engines import NerExperimentalEngine

PROTOCOL = Path(__file__).with_name("protocol.json")


def sha_tree(path):
    return {
        str(p.relative_to(path)): digest(p.read_bytes())
        for p in sorted(path.rglob("*"))
        if p.is_file()
    }


def counts_report(counts):
    def prf(tp, fp, fn):
        return dict(
            tp=tp,
            fp=fp,
            fn=fn,
            support=tp + fn,
            precision=tp / (tp + fp) if tp + fp else None,
            recall=tp / (tp + fn) if tp + fn else None,
            f1=2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else None,
        )

    by = {k: prf(*counts.get(k, [0, 0, 0])) for k in LABELS}
    fs = [v["f1"] for v in by.values() if v["f1"] is not None]
    return dict(
        micro=prf(*(sum(v[i] for v in counts.values()) for i in range(3))),
        macro_f1=statistics.mean(fs) if fs else None,
        macro_labels=len(fs),
        by_label=by,
    )


def ner_metrics(rows, predictions):
    counts = defaultdict(lambda: [0, 0, 0])
    confusion = Counter()
    for row, spans in zip(rows, predictions):
        a, b = {tuple(x) for x in row["entities"]}, {tuple(x) for x in spans}
        for i, values in enumerate((a & b, b - a, a - b)):
            for span in values:
                counts[span[2]][i] += 1
        for start, end, label in a - b:
            other = next((s[2] for s in b if s[:2] == (start, end)), "MISSING_OR_BOUNDARY")
            confusion[label + " -> " + other] += 1
    return counts_report(counts) | {"error_matrix": dict(confusion)}


def score_nlp(nlp, rows):
    return ner_metrics(
        rows,
        [
            [(e.start_char, e.end_char, e.label_) for e in doc.ents]
            for doc in nlp.pipe([r["text"] for r in rows])
        ],
    )


def load_data(bundle, variant):
    rows = read(bundle / "records.jsonl")
    dev = [r for r in rows if r["split"] == "dev"]
    train = [r for r in rows if r["split"] == "train"]
    if variant == "D1":
        train = [
            r
            for f in sorted((ROOT / "data/corpus").glob("*.jsonl"))
            for r in read(f)
            if r["split"] == "train"
        ]
    elif variant == "D2":
        train = [r for r in train if r["style"] == "documental"]
    elif variant == "D3":
        train = [r for r in train if r["style"] == "oral"]
    elif variant not in ("D4", "D4W"):
        raise ValueError("UNKNOWN_DATA_EXPERIMENT")
    return train, dev


def preflight(bundle):
    rows, refs = read(bundle / "records.jsonl"), read(bundle / "expected.jsonl")
    if not validate(rows, refs)["valid"]:
        raise ValueError("CORPUS_GATE")
    baseline = json.loads((bundle / "baseline_sha256.json").read_text())
    if any(digest((ROOT / p).read_bytes()) != s for p, s in baseline.items()):
        raise ValueError("FROZEN_BASELINE_CHANGED")
    sealed = json.loads((bundle / "sha256.json").read_text())
    if any(digest((bundle / p).read_bytes()) != s for p, s in sealed.items()):
        raise ValueError("FROZEN_BUNDLE_CHANGED")
    return {
        p: digest((bundle / p).read_bytes())
        for p in ("records.jsonl", "expected.jsonl", "manifest.json")
    } | {"protocol": digest(PROTOCOL.read_bytes())}


def train(
    bundle, destination, variant, seed, *, protocol_path=None, preflight_fn=None, nlp_factory=None
):
    private_path(destination)
    if destination.exists():
        raise ValueError("MODEL_DESTINATION_EXISTS")
    sealed = (preflight_fn or preflight)(bundle)
    config = json.loads((protocol_path or PROTOCOL).read_text())
    if seed not in config["seeds"]:
        raise ValueError("UNDECLARED_SEED")
    train_rows, dev = load_data(bundle, variant)
    destination.mkdir(parents=True, mode=0o700)
    fix_random_seed(seed)
    rng = random.Random(seed)
    nlp = nlp_factory() if nlp_factory else spacy.blank("es")
    ner = nlp.add_pipe("ner")
    for label in LABELS:
        ner.add_label(label)
    examples = [
        Example.from_dict(nlp.make_doc(r["text"]), {"entities": r["entities"]}) for r in train_rows
    ]
    if variant == "D4W":
        examples += [
            Example.from_dict(nlp.make_doc(r["text"]), {"entities": r["entities"]})
            for r in train_rows
            if r["style"] == "oral"
        ]
    optimizer = nlp.initialize(lambda: examples)
    best, best_epoch, stale = -1, 0, 0
    history = []
    start = time.perf_counter()
    for epoch in range(1, config["epochs"] + 1):
        order = list(examples)
        rng.shuffle(order)
        losses = {}
        for batch in minibatch(order, size=config["batch_size"]):
            nlp.update(batch, sgd=optimizer, drop=config["dropout"], losses=losses)
        metric = score_nlp(nlp, dev)
        f1 = metric["micro"]["f1"] or 0
        history.append(
            dict(epoch=epoch, losses={k: float(v) for k, v in losses.items()}, dev=metric)
        )
        if f1 > best:
            best, best_epoch, stale = f1, epoch, 0
            nlp.to_disk(destination / "model-best")
        else:
            stale += 1
        print(f"{variant} seed={seed} epoch={epoch} dev_f1={f1:.5f}", flush=True)
        if epoch >= config["minimum_epochs"] and stale >= config["patience"]:
            break
    dump(
        destination / "training.json",
        dict(
            variant=variant,
            seed=seed,
            train_documents=len(train_rows),
            train_ids=[r["id"] for r in train_rows],
            dev_ids=[r["id"] for r in dev],
            repeated_samples=len(examples) - len(train_rows),
            train_labels=dict(Counter(e[2] for r in train_rows for e in r["entities"])),
            epochs=len(history),
            selected_epoch=best_epoch,
            best_dev_f1=best,
            seconds=time.perf_counter() - start,
            process_peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            spacy=spacy.__version__,
            sealed=sealed,
            model_sha256=sha_tree(destination / "model-best"),
            model_bytes=sum(
                p.stat().st_size for p in (destination / "model-best").rglob("*") if p.is_file()
            ),
            history=history,
            production=False,
        ),
    )
    protect(destination)


def ablate(result, field):
    out = result.model_copy(deep=True)
    item = out.item_proposal
    if item:
        labels = {
            "price": {"PRECIO", "PRECIO_TOTAL", "PRECIO_UNITARIO"},
            "quantity": {"CANTIDAD"},
            "dimensions": {"ALTO", "ANCHO", "LARGO", "PROFUNDIDAD", "DIAMETRO", "ESPESOR"},
        }[field]
        if field == "dimensions":
            item.dimensions, item.thicknesses = [], []
        else:
            setattr(item, field, None)
            if field == "quantity":
                item.price = None
                if not any(w.code == "NO_QUANTITY" for w in out.warnings):
                    out.warnings.append(
                        Warning(
                            code="NO_QUANTITY",
                            path="/item_proposal/quantity",
                            severity="REVIEW",
                            message="Diagnostic quantity ablation: no quantity proposed.",
                        )
                    )
                labels |= {"PRECIO", "PRECIO_TOTAL", "PRECIO_UNITARIO"}
        for c in out.candidates:
            if c.label in labels:
                c.decision = "UNRESOLVED"
    return ExtractionResult.model_validate(out.model_dump())


def pct(values, q):
    return sorted(values)[min(len(values) - 1, int((len(values) - 1) * q))] if values else None


def evaluate(bundle, run):
    sealed = preflight(bundle)
    training = json.loads((run / "training.json").read_text())
    if sealed != training["sealed"] or sha_tree(run / "model-best") != training["model_sha256"]:
        raise ValueError("MODEL_OR_DATA_CHANGED")
    rows = [r for r in read(bundle / "records.jsonl") if r["split"] == "dev"]
    refs = {r["id"]: r for r in read(bundle / "expected.jsonl")}
    start = time.perf_counter()
    a = RulesEngine()
    a_load = time.perf_counter() - start
    before = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    start = time.perf_counter()
    b = NerExperimentalEngine(run / "model-best")
    b_load = time.perf_counter() - start
    models = ["M-A", "M-A2-price", "M-A2-quantity", "M-A2-dimensions", "M-B", "M-C"]
    predictions = {m: [] for m in models}
    latencies = {m: [] for m in models}
    errors = Counter()
    details = []
    for row in rows:
        req = ExtractionRequest(
            request_id=row["id"],
            text=row["text"],
            currency_context=refs[row["id"]]["comercial"].get("moneda_codigo") or "BOB",
        )
        start = time.perf_counter()
        ar = a.extract(req)
        latencies["M-A"].append((time.perf_counter() - start) * 1000)
        results = {"M-A": ar}
        for field in ("price", "quantity", "dimensions"):
            # Diagnostic output ablation; no claim of independently optimized engine latency.
            results["M-A2-" + field] = ablate(ar, field)
        start = time.perf_counter()
        try:
            br = b.extract(req)
            results["M-B"] = ExtractionResult.model_validate(br.model_dump())
        except (ValueError, TypeError) as exc:
            br = None
            results["M-B"] = None
            errors["M-B:" + type(exc).__name__] += 1
        latencies["M-B"].append((time.perf_counter() - start) * 1000)
        start = time.perf_counter()
        if br:
            cr, conflicts = reconcile(
                ar.model_dump(mode="json"), br.model_dump(mode="json"), b.model_version
            )
            results["M-C"] = ExtractionResult.model_validate(cr)
        else:
            results["M-C"] = ar.model_copy(deep=True)
            conflicts = ["NER_CONTRACT_FAILURE_RULES_FALLBACK"]
        latencies["M-C"].append(
            latencies["M-A"][-1] + latencies["M-B"][-1] + (time.perf_counter() - start) * 1000
        )
        for model in models:
            result = results[model]
            predictions[model].append(result.model_dump(mode="json") if result else None)
        details.append(
            dict(id=row["id"], conflicts=conflicts, results={m: predictions[m][-1] for m in models})
        )
    summary = {}
    for model in models:
        preds = predictions[model]
        spans = [evidence(p, LABELS)[0] if p else [] for p in preds]
        # Accepted candidate view for every engine, including A/B/C. Raw B separately below.
        families = {}
        for fam in ["ALL", *sorted({r["category"] for r in rows})]:
            indices = [i for i, r in enumerate(rows) if fam == "ALL" or r["category"] == fam]
            rs = [rows[i] for i in indices]
            fields = defaultdict(Counter)
            exact, n, false, negatives, invalid = 0, 0, 0, 0, 0
            for i in indices:
                r, p = rows[i], preds[i]
                # Voice scope is furniture only; non-furniture NER is evaluable, voice proposal is not.
                if r["category"] != "muebles_pedido":
                    continue
                n += 1
                ref = refs[r["id"]]
                negative = (
                    ref.get("status") == "NO_PROPOSAL" or ref["comercial"].get("nombre") is None
                )
                negatives += negative
                false += int(negative and p is not None and p.get("item_proposal") is not None)
                try:
                    want, reviewed = reference_fields(ref)
                    actual = predicted_fields(p) if p else {}
                    cs = compare_fields(want, actual, reviewed)
                    exact += all(
                        c["omission"] == 0 and c["false_assertion"] == 0 for c in cs.values()
                    )
                    for key, c in cs.items():
                        fields[key].update(c)
                except ValueError:
                    invalid += 1
            opportunities = sum(c["opportunities"] for c in fields.values())
            correct = sum(c["correct"] + c["safe_abstention"] for c in fields.values())
            families[fam] = dict(
                documents=len(rs),
                ner=ner_metrics(rs, [spans[i] for i in indices]),
                commercial=dict(
                    documents=n,
                    full_exact=exact,
                    full_exact_accuracy=exact / n if n else None,
                    scoped_field_accuracy=correct / opportunities if opportunities else None,
                    opportunities=opportunities,
                    by_field={k: dict(v) for k, v in fields.items()},
                    critical_errors=sum(
                        c["omission"] + c["false_assertion"]
                        for k, c in fields.items()
                        if k not in {"color", "acabado"}
                    ),
                    critical_definition="FN+FP field events excluding color/finish; substitution counts twice",
                    negatives=negatives,
                    false_proposals=false,
                    adapter_failures=invalid,
                    not_evaluable=[
                        "discount_contract_field",
                        "internal_quantity_contract_field",
                        "capacity_reference",
                        "full_PRF03_projection",
                        "real_voice",
                        "independent_human_gold",
                    ],
                ),
            )
        values = latencies[model]
        summary[model] = dict(
            families=families,
            performance=dict(
                first_call_ms=values[0] if values else None,
                warm_p50_ms=statistics.median(values[1:]) if len(values) > 1 else None,
                warm_p95_ms=pct(values[1:], 0.95),
                method="perf_counter sequential A+B+reconcile for hybrid; ablations have no separate timings",
            ),
        )
    dump(
        run / "evaluation.json",
        dict(
            variant=training["variant"],
            seed=training["seed"],
            split="dev",
            independent_external=False,
            baseline_rules_version=details[0]["results"]["M-A"]["engine"]["rules_version"],
            models=summary,
            raw_ner=score_nlp(b.nlp, rows),
            performance=dict(
                rules_load_seconds=a_load,
                ner_load_seconds=b_load,
                peak_rss_before_ner_kib=before,
                process_peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                model_bytes=training["model_bytes"],
                memory_scope="Fresh evaluation process; includes Python/spaCy imports; peak is not marginal engine RAM",
            ),
            errors=dict(errors),
        ),
    )
    jsonl(run / "predictions.jsonl", details)
    protect(run)


def orchestrate(bundle, output, resume=False):
    private_path(output)
    if output.exists() and not resume:
        raise ValueError("EXPERIMENT_OUTPUT_EXISTS_USE_EXPLICIT_RESUME")
    output.mkdir(parents=True, exist_ok=resume)
    if resume and json.loads((output / "preflight.json").read_text()) != preflight(bundle):
        raise ValueError("RESUME_DATA_OR_PROTOCOL_CHANGED")
    config = json.loads(PROTOCOL.read_text())
    dump(output / "preflight.json", preflight(bundle))
    env = os.environ | {
        "OMP_NUM_THREADS": "2",
        "OPENBLAS_NUM_THREADS": "2",
        "MKL_NUM_THREADS": "2",
        "PYTHONHASHSEED": "0",
    }
    for variant in config["experiments"]:
        for seed in config["seeds"]:
            run = output / f"{variant}-{seed}"
            for mode in ("train", "evaluate"):
                if resume and mode == "train" and (run / "training.json").exists():
                    saved = json.loads((run / "training.json").read_text())
                    if saved["sealed"] != preflight(bundle) or saved["model_sha256"] != sha_tree(
                        run / "model-best"
                    ):
                        raise ValueError("RESUME_MODEL_CHANGED")
                    print(f"Reused verified training {variant}/{seed}", flush=True)
                    continue
                command = [
                    sys.executable,
                    "-m",
                    "training.canonical_v2.experiment",
                    mode,
                    "--bundle",
                    str(bundle),
                    "--output",
                    str(run),
                    "--variant",
                    variant,
                    "--seed",
                    str(seed),
                ]
                with (output / f"{variant}-{seed}-{mode}.log").open("w") as log:
                    started = time.time()
                    result = subprocess.run(command, env=env, stdout=log, stderr=subprocess.STDOUT)
                with (output / "commands.jsonl").open("a") as f:
                    f.write(
                        json.dumps(
                            dict(
                                command=command,
                                returncode=result.returncode,
                                started_unix=started,
                                duration=time.time() - started,
                            )
                        )
                        + "\n"
                    )
                if result.returncode:
                    raise RuntimeError(f"EXPERIMENT_FAILED:{variant}:{seed}:{mode}")
                print(f"Completed {variant}/{seed}/{mode}", flush=True)
    reports = [json.loads(p.read_text()) for p in sorted(output.glob("*/evaluation.json"))]
    dump(output / "comparison.json", reports)
    protect(output)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("mode", choices=["run", "train", "evaluate"])
    p.add_argument("--bundle", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--variant", default="D4")
    p.add_argument("--seed", type=int, default=404)
    p.add_argument("--resume", action="store_true")
    a = p.parse_args()
    if a.mode == "run":
        orchestrate(a.bundle, a.output, resume=a.resume)
    elif a.mode == "train":
        train(a.bundle, a.output, a.variant, a.seed)
    else:
        evaluate(a.bundle, a.output)


if __name__ == "__main__":
    main()
