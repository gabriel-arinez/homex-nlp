"""Independent constraints, coverage and noncontamination checks for rc.2."""

import argparse
import copy
import hashlib
import itertools
import json
import re
from decimal import Decimal
from pathlib import Path

from training.corpus_v2.validate import field_value, load_lines, validate_record

FAMILIES = {"muebles_pedido", "sillas", "pisos_flotantes", "otros_productos"}


def validate_rows(rows, refs, labels, tokenizer=None):
    errors = []

    def fail(code, **data):
        errors.append({"code": code} | data)

    ids = [r["id"] for r in rows]
    if len(ids) != len(set(ids)):
        fail("DUPLICATE_ID")
    if set(ids) != set(refs):
        fail("REFERENCE_SET")
    for r in rows:
        rid = r["id"]
        ref = refs.get(rid)
        if not ref:
            continue
        # rc1 constraint validator remains unchanged. Component dimension dicts
        # are additionally checked here, not coerced into string annotations.
        checked = copy.deepcopy(ref)
        checked["facts"] = [
            f
            for f in checked["facts"]
            if not ("componentes." in f["path"] and f["path"].endswith(".dimensiones"))
        ]
        base_errors = validate_record(r, checked, labels, tokenizer)
        for error in base_errors:
            if (
                error["code"] == "SKIRTING_UNIT"
                and r["category"] == "pisos_flotantes"
                and ref["comercial"].get("unidad_codigo") == "M2"
                and re.search(r"no presupuestar zócalos", r["text"], re.I)
            ):
                continue  # rc1 helper misclassified negated mentions outside commercial product.
            errors.append(error)
        if r.get("human_gold") is not False or r.get("human_reviewed") is not False:
            fail("FALSE_GOLD", id=rid)
        for key in (
            "source_case_id",
            "scenario_family_id",
            "template_id",
            "paraphrase_group_id",
            "leakage_group",
        ):
            if not isinstance(r.get(key), str) or not r[key]:
                fail("MISSING_CASE_KEY", id=rid, key=key)
        if r.get("collection") != "development_" + r["split"]:
            fail("COLLECTION", id=rid)
        for fact in ref.get("facts", []):
            try:
                e = fact["evidence"]
                a, b = e["start"], e["end"]
                path = fact["path"]
                if r["text"][a:b] != e["text"] or not 0 <= a < b <= len(r["text"]):
                    fail("FACT_EVIDENCE_RC2", id=rid)
                if field_value(ref, path) != fact["value"]:
                    fail("FACT_VALUE_RC2", id=rid)
                if path == "comercial.cantidad":
                    suffix = r["text"][b : b + 30]
                    if not re.match(
                        r"\s+(?:piezas?|unidades?|pzas?|juegos?|barras?|m²|metros cuadrados)\b",
                        suffix,
                        re.I,
                    ):
                        fail("COMMERCIAL_VS_INTERNAL_CAPACITY", id=rid)
                if path.endswith(".dimensiones") and "componentes." in path:
                    if not isinstance(fact["value"], dict):
                        fail("COMPONENT_DIMENSION_TYPE", id=rid)
                    else:
                        prefix = path.rsplit(".", 1)[0]
                        names = [
                            f
                            for f in ref["facts"]
                            if "componentes." in f["path"] and f["path"].endswith(".nombre")
                        ]
                        own = next((f for f in names if f["path"] == prefix + ".nombre"), None)
                        after = [
                            f["evidence"]["start"]
                            for f in names
                            if own and f["evidence"]["start"] > own["evidence"]["start"]
                        ]
                        if own is None or a < own["evidence"]["end"] or (after and b > min(after)):
                            fail("COMPONENT_DIMENSION_SCOPE", id=rid)
                        for axis, value in fact["value"].items():
                            if (
                                axis not in {"alto", "ancho", "profundidad", "largo", "diametro"}
                                or ("diámetro" if axis == "diametro" else axis) + " " + value
                                not in e["text"]
                            ):
                                fail("COMPONENT_DIMENSION_EVIDENCE", id=rid)
            except (KeyError, ValueError, TypeError):
                fail("REFERENCE_SCHEMA", id=rid)
        if ref["comercial"].get("cantidad") and Decimal(ref["comercial"]["cantidad"]) <= 0:
            fail("QUANTITY", id=rid)
    for split, minimum in [("train", 2), ("dev", 1)]:
        selected = [r for r in rows if r["split"] == split]
        if {r["category"] for r in selected} != FAMILIES:
            fail("FAMILY_COVERAGE", split=split)
        for label in sorted(labels):
            groups = {
                r["leakage_group"] for r in selected if any(e[2] == label for e in r["entities"])
            }
            cases = {
                r["source_case_id"] for r in selected if any(e[2] == label for e in r["entities"])
            }
            if len(groups) < minimum or len(cases) < minimum:
                fail(
                    "LABEL_SCENARIO_COVERAGE",
                    split=split,
                    label=label,
                    groups=len(groups),
                    source_cases=len(cases),
                    required=minimum,
                )
    # Recompute pair evidence; a stale or weakened generated risk report cannot authorize a leak.
    from training.corpus_v2_rc2.grouping import normalized, semantic_key

    for a, b in itertools.combinations(rows, 2):
        if a["split"] == b["split"]:
            continue
        if a["text"] == b["text"]:
            fail("EXACT_LEAK", a=a["id"], b=b["id"])
        if normalized(a["text"]) == normalized(b["text"]):
            fail("NUMBER_TEMPLATE_LEAK", a=a["id"], b=b["id"])
        if semantic_key(refs[a["id"]]) == semantic_key(refs[b["id"]]):
            fail("SEMANTIC_CLAIMS_LEAK", a=a["id"], b=b["id"])
        for key in ("source_case_id", "paraphrase_group_id", "template_id", "leakage_group"):
            if a[key] == b[key]:
                fail("CASE_LEAK", key=key, a=a["id"], b=b["id"])
        tokens = [normalized(r["text"]).split() for r in (a, b)]
        grams = [{tuple(t[i : i + 4]) for i in range(len(t) - 3)} for t in tokens]
        x, y = grams
        if x | y and len(x & y) / len(x | y) >= 0.5:
            fail("NEAR_LEAK", a=a["id"], b=b["id"])
    return errors


def privacy(text):
    return bool(
        re.search(
            r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|ghp_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}|/home/|/media/|(?:teléfono|celular|cliente_nombre|domicilio)\s*:",
            text,
            re.I,
        )
    )


def check_protected(hashes, root=Path(".")):
    return [
        {"code": "PROTECTED_CHANGED", "path": p}
        for p, h in hashes.items()
        if not (root / p).is_file() or hashlib.sha256((root / p).read_bytes()).hexdigest() != h
    ]


def check_risks(risks):
    allowed = {
        "SAME_CASE_GROUP",
        "GENERIC_LANGUAGE_FALSE_POSITIVE",
        "DOMAIN_VOCABULARY_NOT_SOURCE_IDENTITY",
    }
    return [
        {"code": "UNRESOLVED_HIGH_RISK", "pair": r}
        for r in risks
        if (r["severity"] == "HIGH" and (r["decision"] not in allowed or r.get("cross_partition")))
        or r["decision"] not in allowed
    ]


def validate(out, tokenize=True):
    errors = []
    rows = []
    refs = {}
    try:
        for split in ("train", "dev"):
            files = list((out / "development_v2" / split).glob("*.jsonl"))
            if {p.stem for p in files} != FAMILIES:
                errors.append({"code": "FAMILY_FILES"})
            for p in files:
                data = load_lines(p)
                if any(r["category"] != p.stem or r["split"] != split for r in data):
                    errors.append({"code": "FILE_MEMBERSHIP"})
                rows += data
            for p in (out / "expected" / split).glob("*.jsonl"):
                for ref in load_lines(p):
                    if ref["id"] in refs:
                        errors.append({"code": "REFERENCE_DUPLICATE"})
                    refs[ref["id"]] = ref
        labels = set(json.loads(Path("data/manifests/prf04_labels.json").read_text())["labels"])
        tokenizer = None
        if tokenize:
            import spacy

            tokenizer = spacy.blank("es")
        errors += validate_rows(rows, refs, labels, tokenizer)
        hashes = json.loads((out / "sha256.json").read_text())
        actual = {
            str(p.relative_to(out))
            for p in out.rglob("*")
            if p.is_file() and p.name != "sha256.json"
        }
        if set(hashes) != actual:
            errors.append({"code": "MANIFEST_FILES"})
        for p, h in hashes.items():
            if hashlib.sha256((out / p).read_bytes()).hexdigest() != h:
                errors.append({"code": "HASH", "path": p})
        errors += check_protected(json.loads((out / "protected_sha256.json").read_text()))
        for family in FAMILIES:
            for folder in ("corpus", "expected", "splits"):
                name = family + (".json" if folder == "splits" else ".jsonl")
                if (out / "archive_v1" / folder / name).read_bytes() != (
                    Path("data") / folder / name
                ).read_bytes():
                    errors.append({"code": "ARCHIVE_V1_NOT_LITERAL"})
        for p in out.rglob("*"):
            if p.is_file() and privacy(p.read_text()):
                errors.append({"code": "PRIVACY", "path": str(p.relative_to(out))})
        for p in ("analysis/pair_risks.json", "analysis/archive_risks.json"):
            errors += check_risks(json.loads((out / p).read_text()))
        # Independent historical comparison, including normalized ngram near duplicates.
        from training.corpus_v2_rc2.grouping import normalized, semantic_key

        archived = load_lines(out / "archive_v1/rc1_technical_sidecar.jsonl")
        archive_norm = {a["id"]: normalized(a["rc1_record"]["text"]) for a in archived}
        archive_sem = {a["id"]: semantic_key(a["rc1_expected"]) for a in archived}
        archive_grams = {
            i: {tuple(t.split()[j : j + 4]) for j in range(len(t.split()) - 3)}
            for i, t in archive_norm.items()
        }
        for row in rows:
            norm = normalized(row["text"])
            key = semantic_key(refs[row["id"]])
            t = norm.split()
            grams = {tuple(t[j : j + 4]) for j in range(len(t) - 3)}
            for a in archived:
                other = archive_grams[a["id"]]
                if (
                    norm == archive_norm[a["id"]]
                    or key == archive_sem[a["id"]]
                    or (grams | other and len(grams & other) / len(grams | other) >= 0.5)
                ):
                    errors.append(
                        {"code": "ARCHIVE_CONTAMINATION", "id": row["id"], "archive": a["id"]}
                    )
        progress = json.loads((out / "review/progress.json").read_text())
        if progress["human_reviewed"] != 0 or progress["human_gold"] != "NO":
            errors.append({"code": "FALSE_HUMAN_GOLD"})
    except (ValueError, KeyError, TypeError, FileNotFoundError) as exc:
        errors.append({"code": "SCHEMA", "detail": str(exc)})
    return {
        "valid": not errors,
        "development_records": len(rows),
        "archive_v1": 675,
        "expected_records": len(refs),
        "errors": errors,
        "GATE_TRAINING": "EXPERIMENTAL_READY" if not errors else "BLOCKED",
        "HUMAN_GOLD": "NO",
        "EXTERNAL_VOICE_BENCHMARK": "NO",
        "statistical_readiness": "LIMITED_SYNTHETIC_EXPERIMENT_ONLY_NOT_GENERAL_NER_PERFORMANCE",
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("path", type=Path)
    p.add_argument("--report", type=Path)
    a = p.parse_args()
    r = validate(a.path)
    if a.report:
        a.report.write_text(json.dumps(r, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(r, ensure_ascii=False))
    return int(not r["valid"])


if __name__ == "__main__":
    raise SystemExit(main())
