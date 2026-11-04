"""Fail closed on span, reference, leakage and frozen-baseline mutations."""

import json
import re
from collections import Counter
from decimal import Decimal
from pathlib import Path

import spacy
from spacy.tokens import DocBin

from training.canonical_v2.io import digest, dump, read

ROOT = Path(__file__).resolve().parents[2]
LABELS = json.loads((ROOT / "data/manifests/prf04_labels.json").read_text())["labels"]


def normalized(text):
    text = text.casefold()
    text = re.sub(r"\b(?:un[ao]?|dos|tres|cuatro|cinco|seis|siete|ocho|diez)\b", " NUM ", text)
    return " ".join(re.findall(r"\w+", re.sub(r"\d+(?:[.,]\d+)*", " NUM ", text)))


def validate(rows, refs, *, docbin=None):
    errors = []
    ids = set()
    nlp = spacy.blank("es")
    by_id = {r["id"]: r for r in refs}
    groups, exact, fingerprints = {}, {}, {}
    bins = {s: DocBin(store_user_data=True) for s in ("train", "dev", "test")}
    for r in rows:
        rid = r["id"]

        def fail(code):
            errors.append({"id": rid, "code": code})

        if rid in ids:
            fail("DUPLICATE_ID")
        ids.add(rid)
        if r["split"] not in bins:
            fail("UNKNOWN_SPLIT")
            continue
        if digest(r["text"]) != r["text_sha256"]:
            fail("TEXT_HASH")
        if r.get("human_reviewed") is not False:
            fail("FALSE_HUMAN_REVIEW")
        doc = nlp.make_doc(r["text"])
        spans = []
        last = 0
        for a, b, label in r["entities"]:
            if (
                type(a) is not int
                or type(b) is not int
                or not 0 <= a < b <= len(r["text"])
                or a < last
            ):
                fail("BOUNDS_OVERLAP")
                continue
            last = b
            if label not in LABELS:
                fail("UNKNOWN_LABEL")
            span = doc.char_span(a, b, label=label, alignment_mode="strict")
            if span is None:
                fail("TOKEN_ALIGNMENT")
            else:
                spans.append(span)
        doc.ents = spans
        doc.user_data["id"] = rid
        bins[r["split"]].add(doc)
        for values, key in (
            (groups, r["leakage_group"]),
            (exact, r["text_sha256"]),
            (fingerprints, normalized(r["text"])),
        ):
            if key in values and values[key] != r["split"]:
                fail("CROSS_SPLIT_GROUP_OR_DUPLICATE")
            values[key] = r["split"]
        ref = by_id.get(rid)
        if ref is None or ref.get("text_sha256") != r["text_sha256"]:
            fail("REFERENCE_HASH_OR_MISSING")
            continue
        for fact in ref.get("facts", []):
            e = fact["evidence"]
            if (
                not 0 <= e["start"] < e["end"] <= len(r["text"])
                or r["text"][e["start"] : e["end"]] != e["text"]
            ):
                fail("FACT_EVIDENCE")
        # NER and semantic facts must agree on explicit commercial evidence.
        commercial_ref = ref.get("comercial", {})
        word_values = {
            "un": "1",
            "una": "1",
            "uno": "1",
            "dos": "2",
            "tres": "3",
            "cuatro": "4",
            "cinco": "5",
            "seis": "6",
            "siete": "7",
            "ocho": "8",
            "nueve": "9",
            "diez": "10",
            "cero": "0",
        }
        for key, label in [
            ("cantidad", "CANTIDAD"),
            ("precio_unitario", "PRECIO_UNITARIO"),
            ("precio_total_explicito", "PRECIO_TOTAL"),
            ("descuento_linea", "DESCUENTO"),
        ]:
            expected_value = commercial_ref.get(key)
            if expected_value is None:
                continue
            literals = [
                r["text"][a:b].casefold()
                for a, b, entity_label in r["entities"]
                if entity_label == label
            ]
            values = []
            for literal in literals:
                raw = word_values.get(literal, literal)
                if re.fullmatch(r"\d+(?:[.,]\d+)*", raw):
                    try:
                        values.append(
                            Decimal(raw.replace(".", "").replace(",", ".") if "," in raw else raw)
                        )
                    except Exception:
                        pass
            if values and Decimal(str(expected_value)) not in values:
                fail("NER_EXPECTED_NUMBER_CONFLICT")
        for fact in ref.get("facts", []):
            path = fact.get("path", "").split(".")
            if path[0] not in {"comercial", "especificacion"}:
                continue
            value = ref
            try:
                for part in path:
                    value = value[int(part)] if isinstance(value, list) else value[part]
            except (KeyError, IndexError, ValueError, TypeError):
                fail("FACT_RELATION_PATH")
                continue
            if value != fact["value"]:
                fail("FACT_EXPECTED_VALUE_CONFLICT")
        c = ref.get("comercial", {})
        for key in ("cantidad", "precio_unitario", "precio_total_explicito", "descuento_linea"):
            if c.get(key) is not None:
                try:
                    v = Decimal(str(c[key]))
                    if not v.is_finite() or v < 0 or (v == 0 and key != "descuento_linea"):
                        fail("NEGATIVE_OR_ZERO_VALUE")
                    if "precio" in key and v != v.quantize(Decimal(".01")):
                        fail("PRICE_PRECISION")
                except Exception:
                    fail("NON_DECIMAL_VALUE")
        if all(
            c.get(k) is not None for k in ("cantidad", "precio_unitario", "precio_total_explicito")
        ):
            if Decimal(str(c["cantidad"])) * Decimal(str(c["precio_unitario"])) - Decimal(
                str(c.get("descuento_linea") or 0)
            ) != Decimal(str(c["precio_total_explicito"])):
                fail("PRICE_ARITHMETIC")
        comps = ref.get("especificacion", {}).get("datos_tecnicos", {}).get("componentes", [])
        if len({x["uid"] for x in comps}) != len(comps):
            fail("DUPLICATE_COMPONENT_UID")
        technical = ref.get("especificacion", {}).get("datos_tecnicos", {})
        conjuntos = technical.get("conjuntos", [])
        group_ids = {g["uid"] for g in conjuntos}
        if len(group_ids) != len(conjuntos) or len(conjuntos) > 10 or len(comps) > 40:
            fail("TECHNICAL_GROUP_LIMIT_OR_DUPLICATE")
        for comp in comps:
            if comp.get("conjunto_uid") is not None and comp["conjunto_uid"] not in group_ids:
                fail("ORPHAN_COMPONENT_GROUP")
        for scope in [technical.get("caracteristicas_generales", {}), *comps]:
            dimensions = scope.get("dimensiones", {})
            if isinstance(dimensions, dict):
                for axis, measurement in dimensions.items():
                    if isinstance(measurement, str):
                        parsed = re.fullmatch(r"([\d.,]+)\s*(mm|cm|m)", measurement)
                        if not parsed:
                            fail("DIMENSION_NOT_EXPLICIT")
                            continue
                        measurement = {"valor": parsed[1], "unidad": parsed[2]}
                    if not isinstance(measurement, dict):
                        fail("DIMENSION_TYPE")
                        continue
                    if axis not in {
                        "alto",
                        "ancho",
                        "largo",
                        "profundidad",
                        "diametro",
                    } or measurement.get("unidad") not in {"m", "cm", "mm"}:
                        fail("DIMENSION_AXIS_OR_UNIT")
                    try:
                        val = Decimal(str(measurement["valor"]))
                        if not val.is_finite() or val <= 0:
                            fail("DIMENSION_NON_POSITIVE")
                    except Exception:
                        fail("DIMENSION_NOT_DECIMAL")
        if r["category"] != "pisos_flotantes" and commercial_ref.get("cantidad") is not None:
            q = Decimal(str(commercial_ref["cantidad"]))
            if q != q.to_integral_value():
                fail("FRACTIONAL_PIECE_QUANTITY")
        for comp in comps:
            if (
                comp.get("cantidad_interna") is not None
                and Decimal(str(comp["cantidad_interna"])) <= 0
            ):
                fail("INTERNAL_QUANTITY")
    if set(by_id) != ids:
        errors.append({"id": "*", "code": "REFERENCE_MEMBERSHIP"})
    if docbin and not errors:
        docbin.mkdir(parents=True, exist_ok=True)
        for split, db in bins.items():
            db.to_disk(docbin / f"{split}.spacy")
            docs = list(DocBin().from_disk(docbin / f"{split}.spacy").get_docs(nlp.vocab))
            expected = [r for r in rows if r["split"] == split]
            if [
                (d.user_data["id"], d.text, [(e.start_char, e.end_char, e.label_) for e in d.ents])
                for d in docs
            ] != [(r["id"], r["text"], [tuple(e) for e in r["entities"]]) for r in expected]:
                errors.append({"id": "*", "code": "DOCBIN_ROUNDTRIP"})
    return {
        "valid": not errors,
        "records": len(rows),
        "splits": dict(Counter(r["split"] for r in rows)),
        "labels": dict(Counter(e[2] for r in rows for e in r["entities"])),
        "errors": errors,
    }


def main():
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("bundle", type=Path)
    a = p.parse_args()
    report = validate(
        read(a.bundle / "records.jsonl"),
        read(a.bundle / "expected.jsonl"),
        docbin=a.bundle / "docbin",
    )
    dump(a.bundle / "validation.json", report)
    print(json.dumps(report))
    if not report["valid"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
