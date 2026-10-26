"""Independent candidate integrity and semantic-constraint validator.

Does not import generators, reference parser, recipes, or production predictions.
Returns failures (never fixes records). Numeric checks use Decimal.
"""

import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation
from pathlib import Path

FAMILIES = {"muebles_pedido", "sillas", "pisos_flotantes", "otros_productos"}
FOLDERS = ("04_CORPUS_DOCUMENTAL_V2", "05_CORPUS_ORAL_V2")
NUM_WORDS = {
    "un": 1,
    "una": 1,
    "dos": 2,
    "tres": 3,
    "cuatro": 4,
    "cinco": 5,
    "seis": 6,
    "siete": 7,
    "ocho": 8,
    "diez": 10,
    "cero": 0,
}


def hash_bytes(data):
    return hashlib.sha256(data).hexdigest()


def load_lines(path):
    rows = []
    for n, line in enumerate(path.read_text().splitlines(), 1):
        if not line.strip():
            raise ValueError(f"{path.name}:{n}: blank JSONL record")
        obj = json.loads(line)
        if not isinstance(obj, dict):
            raise ValueError(f"{path.name}:{n}: not object")
        rows.append(obj)
    return rows


def decimal_literal(text):
    if text.split()[0] in NUM_WORDS:
        return Decimal(NUM_WORDS[text.split()[0]])
    if text == "sin descuento":
        return Decimal(0)
    m = re.search(r"\d+(?:[.,]\d+)*", text)
    if not m:
        return None
    s = m[0]
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    return Decimal(s)


def field_value(ref, path):
    parts = path.split(".")
    node = ref
    if parts[0] in {"componentes", "dimensiones", "accesorios"}:
        node = ref["especificacion"]["datos_tecnicos"]
        if parts[0] == "dimensiones":
            node = node["caracteristicas_generales"]
    for key in parts:
        if isinstance(node, list):
            node = (
                next((x for x in node if isinstance(x, dict) and x.get("uid") == key), None)
                if key.startswith("c")
                else node[int(key)]
            )
        else:
            node = node[key]
    return node


def validate_record(row, ref, labels, tokenizer=None):
    errors = []
    rid = row.get("id", "?")
    text = row.get("text", "")

    def fail(code):
        errors.append({"id": rid, "code": code})

    if not isinstance(text, str) or not text:
        fail("TEXT")
        return errors
    if row.get("category") not in FAMILIES:
        fail("FAMILY")
    if row.get("origin") not in {"SINTETICO_DOCUMENTAL", "SINTETICO_ORAL"}:
        fail("PUBLIC_ORIGIN")
    if row.get("human_reviewed") is not False or ref.get("human_reviewed") is not False:
        fail("HUMAN_ATTRIBUTION")
    if hash_bytes(text.encode()) != row.get("text_sha256") or ref.get("text_sha256") != row.get(
        "text_sha256"
    ):
        fail("TEXT_HASH")
    if ref.get("id") != rid:
        fail("REFERENCE_ID")
    if row.get("split") not in {"train", "dev", "test"}:
        fail("SPLIT")
    if not row.get("source_ref") or not row.get("leakage_group"):
        fail("PROVENANCE")
    if row.get("status") not in {"REQUIRES_REVIEW", "ABSTAIN"} or ref.get("status") != row.get(
        "status"
    ):
        fail("STATUS")
    end = -1
    doc = tokenizer.make_doc(text) if tokenizer else None
    for entity in row.get("entities", []):
        if not isinstance(entity, list) or len(entity) != 3:
            fail("SPAN_SHAPE")
            continue
        a, b, label = entity
        if type(a) is not int or type(b) is not int or not 0 <= a < b <= len(text):
            fail("SPAN_BOUNDS")
            continue
        if a < end:
            fail("SPAN_OVERLAP")
        end = b
        if label not in labels:
            fail("LABEL")
        if label == "COLOR" and re.search(
            r"elecci[oó]n|confirmar|seg[uú]n dise[nñ]o", text[a:b], re.I
        ):
            fail("PENDING_COLOR")
        if doc is not None and doc.char_span(a, b, alignment_mode="strict") is None:
            fail("TOKEN_ALIGNMENT")
    commercial = ref.get("comercial", {})
    covered = set()
    facts = ref.get("facts", [])
    for fact in facts:
        try:
            evidence = fact["evidence"]
            a = evidence["start"]
            b = evidence["end"]
            literal = evidence["text"]
            path = fact["path"]
            value = fact["value"]
            if (
                type(a) is not int
                or type(b) is not int
                or not 0 <= a < b <= len(text)
                or text[a:b] != literal
            ):
                fail("FACT_EVIDENCE")
                continue
            actual = field_value(ref, path)
            if actual != value:
                fail("FACT_VALUE")
            covered.add(path)
            # Check normalized semantics separately from matching a generated assertion.
            if path.startswith("comercial.") and path.split(".")[-1] in {
                "cantidad",
                "precio_unitario",
                "precio_total_explicito",
                "descuento_linea",
            }:
                if decimal_literal(literal) != Decimal(value):
                    fail("FACT_NUMERIC")
                key = path.split(".")[-1]
                context = text[max(0, a - 70) : a].lower()
                if key == "precio_unitario" and not re.search(
                    r"(?:precio unitario|precio por unidad|valor unitario|precio por pieza|precio por barra|precio por metro cuadrado|unitario)\s*(?:bs|usd)?\s*$",
                    context,
                ):
                    fail("PRICE_MODE_UNIT")
                if key == "precio_total_explicito" and not re.search(
                    r"(?:subtotal neto|importe de línea|total por este producto|total por las dos|total)\s*(?:bs|usd)?\s*$",
                    context,
                ):
                    fail("PRICE_MODE_TOTAL")
            if path.endswith("cantidad_interna"):
                if not isinstance(value, int) or decimal_literal(literal) != Decimal(value):
                    fail("INTERNAL_QUANTITY")
            if path == "comercial.unidad_codigo":
                units = {
                    "PIEZA": r"\b(?:pieza|pza|unidad)",
                    "M2": r"m²|Mts\.2|metros cuadrados",
                    "BARRA": r"barra",
                    "JUEGO": r"juego",
                }
                if value not in units or not re.search(units[value], literal, re.I):
                    fail("UNIT_EVIDENCE")
            if path == "comercial.moneda_codigo" and not (
                (value == "BOB" and literal == "Bs") or value == literal == "USD"
            ):
                fail("CURRENCY_EVIDENCE")
            if "componentes." in path and not path.endswith(".uid"):
                field = path.split(".")[-1]
                if (
                    field not in {"cantidad_interna"}
                    and str(value) != literal
                    and fact.get("rule") != "anafora_explicita"
                ):
                    fail("ATTRIBUTE_LITERAL")
                if field in {"material", "espesor", "color", "acabado"}:
                    prefix = path.rsplit(".", 1)[0]
                    names = [
                        f
                        for f in facts
                        if f["path"].endswith(".nombre") and "componentes." in f["path"]
                    ]
                    own = next((f for f in names if f["path"] == prefix + ".nombre"), None)
                    if not own:
                        fail("ATTRIBUTE_SCOPE")
                    else:
                        after = [
                            f["evidence"]["start"]
                            for f in names
                            if f["evidence"]["start"] > own["evidence"]["start"]
                        ]
                        if a < own["evidence"]["end"] or (after and b > min(after)):
                            fail("ATTRIBUTE_SCOPE")
            if path.startswith("dimensiones.") or ".dimensiones." in path:
                if not isinstance(value, dict) or value.get("unidad") not in {"m", "cm", "mm"}:
                    fail("DIMENSION_UNIT")
                elif fact.get("rule") not in {"dimension_palabras"} and decimal_literal(
                    literal
                ) != Decimal(value["valor"]):
                    fail("DIMENSION_VALUE")
                if fact.get("rule") == "dimension_palabras":
                    allowed = {
                        "alto setenta y cinco centímetros": {"valor": "75", "unidad": "cm"},
                        "ancho un metro": {"valor": "1", "unidad": "m"},
                    }
                    if allowed.get(literal) != value:
                        fail("DIMENSION_WORDS")
        except (KeyError, TypeError, IndexError, InvalidOperation, ValueError):
            fail("FACT_SCHEMA")
    for key, value in commercial.items():
        if value is not None and "comercial." + key not in covered:
            fail("COMMERCIAL_WITHOUT_EVIDENCE:" + key)
    for key in ("cantidad", "precio_unitario", "precio_total_explicito", "descuento_linea"):
        value = commercial.get(key)
        if value is not None:
            try:
                if (
                    not isinstance(value, str)
                    or Decimal(value) < 0
                    or (key == "cantidad" and Decimal(value) == 0)
                ):
                    fail("MONEY_QUANTITY_TYPE")
            except InvalidOperation:
                fail("DECIMAL")
    q, u, t, d = [
        commercial.get(k)
        for k in ("cantidad", "precio_unitario", "precio_total_explicito", "descuento_linea")
    ]
    if all(v is not None for v in (q, u, t)):
        if Decimal(q) * Decimal(u) - Decimal(d or "0") != Decimal(t):
            fail("ARITHMETIC")
    # Derivation only legal with explicit zero discount and exact cents.
    derived = ref.get("derived_unit_price")
    if derived is not None:
        if (
            None in (q, t, d)
            or Decimal(d) != 0
            or Decimal(t) / Decimal(q) != Decimal(derived)
            or Decimal(derived).quantize(Decimal(".01")) != Decimal(derived)
        ):
            fail("UNIT_PRICE_DERIVATION")
    if (
        row["category"] == "pisos_flotantes"
        and commercial.get("cantidad") is not None
        and commercial.get("unidad_codigo") != "M2"
    ):
        fail("FLOOR_UNIT")
    if (
        "zócalo" in text.lower()
        and commercial.get("cantidad") is not None
        and commercial.get("unidad_codigo") != "BARRA"
    ):
        fail("SKIRTING_UNIT")
    if (
        commercial.get("unidad_codigo") in {"PIEZA", "JUEGO", "BARRA"}
        and q is not None
        and Decimal(q) != Decimal(q).to_integral_value()
    ):
        fail("NONINTEGER_PIECE_QUANTITY")
    technical = ref.get("especificacion", {}).get("datos_tecnicos")
    if technical is not None:
        if "schema_version" in technical:
            fail("COMMERCIAL_SCHEMA_VERSION")
        if technical.get("descripcion_original") != text:
            fail("ORIGINAL_DESCRIPTION")
        comps = technical.get("componentes", [])
        sets = technical.get("conjuntos", [])
        if len(comps) > 40 or len(sets) > 10:
            fail("PRF03_LIMIT")
        uids = [c.get("uid") for c in comps]
        if len(set(uids)) != len(uids):
            fail("COMPONENT_UID")
        set_ids = {s["uid"] for s in sets}
        for i, c in enumerate(comps):
            if not c.get("nombre"):
                fail("COMPONENT_NAME")
            if c.get("conjunto_uid") and c["conjunto_uid"] not in set_ids:
                fail("CONJUNTO_REF")
            for key in ("nombre", "material", "espesor", "color", "acabado", "cantidad_interna"):
                if c.get(key) is not None and not any(
                    p in covered
                    for p in [
                        f"componentes.{c['uid']}.{key}",
                        f"especificacion.datos_tecnicos.componentes.{i}.{key}",
                    ]
                ):
                    fail("COMPONENT_WITHOUT_EVIDENCE:" + key)
            if c.get("cantidad_interna") is not None and (
                type(c["cantidad_interna"]) is not int or c["cantidad_interna"] <= 0
            ):
                fail("COMPONENT_QUANTITY")
        if row.get("status") == "ABSTAIN" and (
            comps or any(v is not None for v in commercial.values())
        ):
            fail("ABSTAIN_PROPOSAL")
    for rel in (
        ref.get("cantidades_internas", [])
        + ref.get("capacidades", [])
        + ref.get("research_relations", [])
    ):
        e = rel["evidence"]
        if e["text"] != text[e["start"] : e["end"]] or rel.get("commercial") is not False:
            fail("RELATION_EVIDENCE")
    return errors


def validate(out, root=Path("."), tokenize=True):
    errors = []
    rows = []
    refs = {}
    tokenizer = None
    if tokenize:
        import spacy

        tokenizer = spacy.blank("es")
    from jsonschema import Draft202012Validator

    schema = Draft202012Validator(
        json.loads((root / "training/corpus_v2/record.schema.json").read_text())
    )
    labels = set(json.loads((root / "data/manifests/prf04_labels.json").read_text())["labels"])
    try:
        for folder in FOLDERS:
            paths = list((out / folder).glob("*.jsonl"))
            if {p.stem for p in paths} != FAMILIES:
                errors.append({"code": "FOUR_FAMILIES", "folder": folder})
            for p in paths:
                data = load_lines(p)
                if any(r["category"] != p.stem for r in data):
                    errors.append({"code": "FILE_FAMILY"})
                rows += data
        for p in (out / "06_EXPECTED_ESTRUCTURADOS_V2").glob("*.jsonl"):
            for r in load_lines(p):
                if r["id"] in refs:
                    errors.append({"code": "DUPLICATE_REFERENCE"})
                refs[r["id"]] = r
        ids = {r["id"] for r in rows}
        if len(ids) != len(rows):
            errors.append({"code": "DUPLICATE_ID"})
        if ids != set(refs):
            errors.append({"code": "REFERENCE_SET"})
        for r in rows:
            for issue in schema.iter_errors(r):
                errors.append(
                    {
                        "id": r.get("id"),
                        "code": "JSON_SCHEMA",
                        "path": ".".join(map(str, issue.path)),
                        "detail": issue.message,
                    }
                )
            if r["id"] in refs:
                errors += validate_record(r, refs[r["id"]], labels, tokenizer)
        texts = Counter(r["text"] for r in rows)
        if any(c > 1 for c in texts.values()):
            errors.append({"code": "EXACT_DUPLICATE"})
        groups = defaultdict(set)
        lookup = {r["id"]: r for r in rows}
        for r in rows:
            groups[r["leakage_group"]].add(r["split"])
            if r.get("parent_id"):
                parent = lookup.get(r["parent_id"])
                if (
                    not parent
                    or parent["split"] != r["split"]
                    or parent["leakage_group"] != r["leakage_group"]
                ):
                    errors.append({"id": r["id"], "code": "PARENT_SPLIT"})
            if r.get("v1_id"):
                src = r["source_ref"]
                source = next(x for x in load_lines(root / src["path"]) if x["id"] == r["v1_id"])
                if source["text"] != r["text"]:
                    errors.append({"code": "V1_LITERAL_CHANGED"})
                if source["split"] == "test" and r["split"] != "test":
                    errors.append({"code": "HISTORICAL_TEST_REUSED"})
        if any(len(v) > 1 for v in groups.values()):
            errors.append({"code": "GROUP_LEAKAGE"})
        splits = json.loads((out / "07_SPLITS_Y_MANIFIESTOS_V2/splits.json").read_text())[
            "assignments"
        ]
        split_ids = [i for s in splits.values() for i in s]
        if len(set(split_ids)) != len(split_ids) or set(split_ids) != ids:
            errors.append({"code": "SPLIT_MEMBERSHIP"})
        for split, assigned in splits.items():
            if any(lookup[i]["split"] != split for i in assigned):
                errors.append({"code": "SPLIT_MISMATCH"})
        baseline = json.loads(
            (out / "07_SPLITS_Y_MANIFIESTOS_V2/baseline_v1_sha256.json").read_text()
        )
        for p, h in baseline.items():
            if hash_bytes((root / p).read_bytes()) != h:
                errors.append({"code": "V1_CHANGED", "path": p})
        hashes = json.loads((out / "07_SPLITS_Y_MANIFIESTOS_V2/sha256.json").read_text())
        actual = {
            str(p.relative_to(out))
            for p in out.rglob("*")
            if p.is_file() and p.name != "sha256.json"
        }
        if set(hashes) != actual:
            errors.append({"code": "MANIFEST_FILE_SET"})
        for p, h in hashes.items():
            if not (out / p).is_file() or hash_bytes((out / p).read_bytes()) != h:
                errors.append({"code": "FILE_HASH", "path": p})
        tool_hashes = json.loads(
            (out / "07_SPLITS_Y_MANIFIESTOS_V2/tooling_sha256.json").read_text()
        )
        for path, expected_hash in tool_hashes.items():
            if (
                not (root / path).is_file()
                or hash_bytes((root / path).read_bytes()) != expected_hash
            ):
                errors.append({"code": "TOOLING_HASH", "path": path})
        candidate = json.loads((out / "07_SPLITS_Y_MANIFIESTOS_V2/candidate.json").read_text())
        if (
            candidate.get("active") is not False
            or set(candidate.get("families", [])) != FAMILIES
            or candidate.get("nlp_api_schema_version") != "1.0"
        ):
            errors.append({"code": "CANDIDATE_MANIFEST"})
        audits = json.loads((out / "01_AUDITORIA_V1_675.json").read_text())
        originals = {
            r["id"]
            for family in FAMILIES
            for r in load_lines(root / "data/corpus" / f"{family}.jsonl")
        }
        if len(audits) != 675 or {r["v1_id"] for r in audits} != originals:
            errors.append({"code": "AUDIT_COVERAGE"})
        # Independently recompute near-pairs rather than trusting the builder report.
        ngrams = {}
        for r in rows:
            words = re.findall(r"\w+", r["text"].lower())
            ngrams[r["id"]] = {tuple(words[i : i + 4]) for i in range(len(words) - 3)}
        for i, a in enumerate(rows):
            for b in rows[i + 1 :]:
                if a["split"] == b["split"]:
                    continue
                x, y = ngrams[a["id"]], ngrams[b["id"]]
                if x | y and len(x & y) / len(x | y) >= 0.5:
                    errors.append({"code": "NEAR_LEAKAGE", "a": a["id"], "b": b["id"]})
        for p in out.rglob("*"):
            if p.is_file():
                content = p.read_text()
                if re.search(
                    r"(?i)-----BEGIN .*PRIVATE KEY|ghp_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]+|[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}|/home/|/media/|\b(?:telefono|teléfono|celular|domicilio)\s*:",
                    content,
                ):
                    errors.append(
                        {"code": "PUBLIC_PRIVACY_PATTERN", "path": str(p.relative_to(out))}
                    )
    except (ValueError, KeyError, FileNotFoundError, TypeError) as exc:
        errors.append({"code": "SCHEMA_OR_FILE", "detail": str(exc)})
    return {
        "valid": not errors,
        "records": len(rows),
        "references": len(refs),
        "errors": errors,
        "tokenizer": "spacy-es-strict" if tokenize else "NOT_CHECKED",
        "semantic_review": "TECHNICAL_CONSTRAINTS_NOT_HUMAN_GOLD",
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("path", type=Path)
    p.add_argument("--report", type=Path)
    a = p.parse_args()
    report = validate(a.path)
    if a.report:
        a.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report, ensure_ascii=False))
    return int(not report["valid"])


if __name__ == "__main__":
    raise SystemExit(main())
