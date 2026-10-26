"""Count-first metrics, fixed normalization; no engine execution or inferred references."""

import math
from collections import defaultdict
from decimal import Decimal
from statistics import median

from training.evaluar_campo_prf04 import palabras


def ratio(a, b):
    return a / b if b else None


def alignment(reference, hypothesis):
    """Levenshtein; deterministic ties: match/substitute, delete, insert."""
    r, h = palabras(reference), palabras(hypothesis)
    matrix = [[0] * (len(h) + 1) for _ in range(len(r) + 1)]
    for i in range(len(r) + 1):
        matrix[i][0] = i
    for j in range(len(h) + 1):
        matrix[0][j] = j
    for i, word in enumerate(r, 1):
        for j, other in enumerate(h, 1):
            matrix[i][j] = min(
                matrix[i - 1][j - 1] + (word != other), matrix[i - 1][j] + 1, matrix[i][j - 1] + 1
            )
    i, j = len(r), len(h)
    s = d = ins = 0
    while i or j:
        if i and j and matrix[i][j] == matrix[i - 1][j - 1] + (r[i - 1] != h[j - 1]):
            s += r[i - 1] != h[j - 1]
            i, j = i - 1, j - 1
        elif i and matrix[i][j] == matrix[i - 1][j] + 1:
            d += 1
            i -= 1
        else:
            ins += 1
            j -= 1
    return wer_counts(s, d, ins, len(r))


def wer_counts(s, d, i, n):
    return {
        "status": "EVALUABLE" if n else "NOT_EVALUABLE",
        "S": s,
        "D": d,
        "I": i,
        "N": n,
        "wer": ratio(s + d + i, n),
    }


def prf(tp, fp, fn):
    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": ratio(tp, tp + fp),
        "recall": ratio(tp, tp + fn),
        "f1": ratio(2 * tp, 2 * tp + fp + fn),
    }


def ner_counts(gold, predicted):
    a = {(s.start, s.end, s.label) for s in gold}
    b = {(s.start, s.end, s.label) for s in predicted}
    return {
        label: [
            len({x for x in a & b if x[2] == label}),
            len({x for x in b - a if x[2] == label}),
            len({x for x in a - b if x[2] == label}),
        ]
        for label in sorted({x[2] for x in a | b})
    }


def ner_report(counts, n):
    if not n:
        return {
            "status": "NOT_EVALUABLE",
            "sessions": 0,
            "micro": None,
            "macro_f1": None,
            "by_label": {},
        }
    by_label = {label: prf(*values) for label, values in sorted(counts.items())}
    fs = [v["f1"] for v in by_label.values() if v["f1"] is not None]
    return {
        "status": "EVALUABLE",
        "sessions": n,
        "micro": prf(*(sum(v[i] for v in counts.values()) for i in range(3))),
        "macro_f1": sum(fs) / len(fs) if fs else None,
        "macro_labels": len(fs),
        "macro": {
            metric: {
                "value": sum(values) / len(values) if values else None,
                "labels": len(values),
            }
            for metric in ("precision", "recall", "f1")
            for values in [[v[metric] for v in by_label.values() if v[metric] is not None]]
        },
        "by_label": by_label,
    }


NUMERIC = {
    "sold_quantity",
    "internal_quantity",
    "capacity",
    "length",
    "width",
    "height",
    "thickness",
    "accessory_quantity",
    "unit_price",
    "total_price",
    "discount",
}
CRITICAL = {
    "product",
    "sold_quantity",
    "unit",
    "unit_price",
    "total_price",
    "discount",
    "currency",
    "length",
    "width",
    "height",
    "thickness",
    "material",
    "accessory_quantity",
}
DIMENSIONS = {"length", "width", "height", "thickness"}


def fact_value(f):
    value = Decimal(f.value.replace(",", ".")) if f.field in NUMERIC else f.value
    return value, f.unit


def commercial_counts(gold, predicted):
    a = {(f.scope, f.field): f for f in gold.facts}
    b = {(f.scope, f.field): f for f in predicted.facts} if predicted else {}
    keys = set(a) | set(b)
    if gold.coverage == "partial":
        keys &= {tuple(x.split(":")) for x in gold.reviewed_keys}
        keys |= {tuple(x.split(":")) for x in gold.reviewed_keys}
    result = defaultdict(lambda: defaultdict(int))
    critical_errors = critical_n = 0
    for key in sorted(keys):
        wanted, actual = a.get(key), b.get(key)
        field = key[1]
        row = result[field]
        row["opportunities"] += 1
        complete = wanted and (field not in DIMENSIONS or wanted.unit is not None)
        correct = bool(complete and actual and fact_value(wanted) == fact_value(actual))
        row["expected_positive"] += wanted is not None
        row["predicted_positive"] += actual is not None
        row["correct"] += correct
        row["omission"] += bool(wanted and not correct)
        row["false_assertion"] += bool(actual and not correct)
        row["safe_abstention"] += wanted is None and actual is None
        error = bool((wanted or actual) and not correct)
        if field in CRITICAL:
            critical_n += 1
            critical_errors += error
    return {k: dict(v) for k, v in result.items()}, critical_errors, critical_n


def commercial_report(counts, errors, n, sessions):
    return {
        "status": "EVALUABLE" if sessions else "NOT_EVALUABLE",
        "sessions": sessions,
        "by_field": {
            k: dict(v)
            | {
                "accuracy": ratio(v["correct"], v["expected_positive"]),
                "omission_rate": ratio(v["omission"], v["expected_positive"]),
                "false_assertion_rate": ratio(v["false_assertion"], v["predicted_positive"]),
            }
            for k, v in sorted(counts.items())
        },
        "critical_errors": errors,
        "critical_opportunities": n,
        "critical_error_rate": ratio(errors, n),
    }


def stats(values):
    """Nearest rank p95 (ceil(.95*n)); p50 median, including mean of middle pair."""
    values = sorted(values)
    return {
        "n": len(values),
        "p50": median(values) if values else None,
        "p95": values[math.ceil(0.95 * len(values)) - 1] if values else None,
        "max": max(values) if values else None,
    }


def productivity(rows):
    pairs = [
        p
        for p in rows
        if p
        and p.commercial_validated
        and p.exclusion == "NONE"
        and p.manual_seconds is not None
        and p.assisted_seconds is not None
        and p.corrections is not None
    ]
    reasons = defaultdict(int)
    for p in rows:
        if p not in pairs:
            reasons[p.exclusion if p and p.exclusion != "NONE" else "INCOMPLETE"] += 1
    return {
        "status": "EVALUABLE" if pairs else "NOT_EVALUABLE",
        "n": len(pairs),
        "excluded": dict(sorted(reasons.items())),
        "manual_seconds": stats([p.manual_seconds for p in pairs]),
        "assisted_seconds": stats([p.assisted_seconds for p in pairs]),
        "paired_saving_seconds": stats([p.manual_seconds - p.assisted_seconds for p in pairs]),
        "corrections": sum(p.corrections for p in pairs) if pairs else None,
        "order": {
            order: sum(p.order == order for p in pairs)
            for order in ("manual_first", "assisted_first")
        },
    }
