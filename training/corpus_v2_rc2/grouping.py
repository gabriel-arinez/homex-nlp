"""Versioned evidence hierarchy: generic family/prefix alerts never imply identity."""

import hashlib
import itertools
import re
import unicodedata
from collections import Counter

POLICY = "case-paraphrase-specific-template-and-semantic-fingerprint-v2"


def normalized(text):
    text = "".join(
        c for c in unicodedata.normalize("NFD", text.casefold()) if not unicodedata.combining(c)
    )
    text = re.sub(r"\b(?:un[ao]?|dos|tres|cuatro|cinco|seis|siete|ocho|diez)\b", " <n> ", text)
    text = re.sub(r"\d+(?:[.,]\d+)*", " <n> ", text)
    text = re.sub(r"centimetros?", "cm", text)
    text = re.sub(r"milimetros?", "mm", text)
    return " ".join(re.findall(r"\w+|<n>", text))


def semantic_key(ref):
    # Preserve nonnumeric claims and scope; different evidence wording alone is not independence.
    def mask(x):
        if isinstance(x, dict):
            return {
                k: mask(v)
                for k, v in sorted(x.items())
                if k not in {"uid", "descripcion_original", "advertencias"}
            }
        if isinstance(x, list):
            return [mask(v) for v in x]
        if x is None:
            return None
        if isinstance(x, (int, float)):
            return "<n>"
        return normalized(str(x))

    import json

    return json.dumps(
        mask(
            {
                "comercial": ref["comercial"],
                "especificacion": ref["especificacion"],
                "status": ref["status"],
            }
        ),
        sort_keys=True,
        ensure_ascii=False,
    )


def pair_risks(rows, refs):
    result = []
    grams = {
        r["id"]: {
            tuple(normalized(r["text"]).split()[i : i + 4])
            for i in range(max(0, len(normalized(r["text"]).split()) - 3))
        }
        for r in rows
    }
    for a, b in itertools.combinations(rows, 2):
        reasons = []
        x, y = grams[a["id"]], grams[b["id"]]
        score = len(x & y) / len(x | y) if x | y else 0
        if a["text"] == b["text"]:
            reasons.append("EXACT")
        if normalized(a["text"]) == normalized(b["text"]):
            reasons.append("NUMBER_ACCENT_UNIT_FINGERPRINT")
        for key in ("source_case_id", "paraphrase_group_id", "template_id"):
            if a.get(key) and a.get(key) == b.get(key):
                reasons.append(key.upper())
        if semantic_key(refs[a["id"]]) == semantic_key(refs[b["id"]]):
            reasons.append("SEMANTIC_FACTS_NUMERIC_MASK")
        if score >= 0.50:
            reasons.append("NEAR_DUPLICATE_4GRAM")
        elif score >= 0.25:
            reasons.append("SHARED_LANGUAGE_ALERT")
        if reasons:
            strong = any(r != "SHARED_LANGUAGE_ALERT" for r in reasons)
            result.append(
                {
                    "a": a["id"],
                    "b": b["id"],
                    "reasons": reasons,
                    "jaccard_normalized_4gram": round(score, 6),
                    "severity": "HIGH" if strong else "LOW",
                    "decision": "SAME_CASE_GROUP" if strong else "GENERIC_LANGUAGE_FALSE_POSITIVE",
                    "rationale": "Same source/case, specific template or equivalent structured claims; one partition required."
                    if strong
                    else "Only partial formulaic commercial wording; other detectors do not establish same case.",
                }
            )
    return result


class Union:
    def __init__(self, ids):
        self.parent = {i: i for i in ids}

    def find(self, i):
        if self.parent[i] != i:
            self.parent[i] = self.find(self.parent[i])
        return self.parent[i]

    def join(self, a, b):
        x, y = sorted((self.find(a), self.find(b)))
        self.parent[y] = x


def old_graph(rows):
    from training.corpus_v2.build import template

    union = Union([r["id"] for r in rows])
    keys = {}
    edges = []
    for row in rows:
        for kind, value in [
            ("proforma", row["proforma_id"]),
            ("family_id", row["family_id"]),
            ("masked_template", template(row)),
            ("generic_prefix", row["text"][:65]),
        ]:
            key = (kind, value)
            if key in keys:
                before = union.find(row["id"]) != union.find(keys[key])
                union.join(row["id"], keys[key])
                edges.append(
                    {
                        "a": keys[key],
                        "b": row["id"],
                        "signal": kind,
                        "key_sha256": hashlib.sha256(value.encode()).hexdigest(),
                        "merged_components": before,
                        "rc2_interpretation": "ARCHIVE_PROVENANCE"
                        if kind == "proforma"
                        else "ALERT_NOT_PROOF_OF_SAME_COMMERCIAL_CASE",
                    }
                )
            else:
                keys[key] = row["id"]
    count = Counter(union.find(r["id"]) for r in rows)
    return {
        "policy_rc1": "transitive proforma+family_id+masked_template+prefix",
        "components": len(count),
        "component_sizes": sorted(count.values(), reverse=True),
        "edges_by_signal": dict(Counter(e["signal"] for e in edges)),
        "actual_merges_by_signal": dict(
            Counter(e["signal"] for e in edges if e["merged_components"])
        ),
        "edges": edges,
        "per_id": [
            {
                "id": r["id"],
                "original_split": r["split"],
                "component": union.find(r["id"]),
                "signals": [e for e in edges if r["id"] in (e["a"], e["b"])],
                "rc2_collection": "archive_v1",
            }
            for r in rows
        ],
    }
