"""Single canonical dataset; private documentary bytes never enter the checkout.

Recovered RC2 is deduplicated history (includes RC1's 12 bases and 40 oral cases).
V1 remains an immutable diagnostic baseline, never silently relabelled documentary.
"""

import argparse
import json
import re
from collections import Counter
from copy import deepcopy
from pathlib import Path

from training.canonical_v2.io import digest, dump, jsonl, private_path, protect, read
from training.canonical_v2.literal_v1 import audit_literal
from training.canonical_v2.patches_v1 import patches
from training.canonical_v2.private_ingest import ingest
from training.canonical_v2.validate import ROOT, normalized, validate

FAMILIES = ("muebles_pedido", "sillas", "pisos_flotantes", "otros_productos")
VERSION = "2.0.0-offline.2"


def family(item):
    if item["source_file"] == "inventario de sillas.txt":
        return "sillas"
    if item["source_file"] == "PROFORMAS.txt":
        return "muebles_pedido"
    t = item["item_text"].casefold()
    return (
        "pisos_flotantes"
        if "piso flotante" in t
        else "sillas"
        if re.search(r"sill[aoó]n?|sillas", t)
        else "otros_productos"
    )


def documentary(items, excluded):
    """Closed-scope literal excerpts: no incomplete full-item NER negatives.

    Extract only explicitly bounded title, quantity/unit, price or local technical
    clauses with exhaustive annotations for that clause. Full originals remain
    in the item ledger; a fragment is never a complete manufacturing reference.
    """
    rows, refs = [], []
    for item in items:
        if item["id"] in excluded:
            continue
        text = item["item_text"]
        found = []
        title = re.match(r"[^\n\t]+", text)
        if (
            title
            and len(title[0].split()) <= 12
            and not re.match(r"\d", title[0])
            and not re.search(
                r"precio|tamaño|características|materiales|\d+\s*mm\b", title[0], re.I
            )
        ):
            literal = title[0].strip()
            if len(literal) > 3:
                found.append(
                    (
                        text.index(literal),
                        text.index(literal) + len(literal),
                        [[0, len(literal), "PRODUCTO"]],
                        "title",
                    )
                )
        # Quantity must be at the beginning of a physical source line, with a commercial unit.
        for m in re.finditer(
            r"(?m)^\s*(\d+[,.]\d+)\s+(Pza[s.]?|Pzas\.?|PIEZAS|Unidad|Juego|Mts\.2|barras?)\b",
            text,
            re.I,
        ):
            a, b = m.start(1), m.end(2)
            found.append(
                (
                    a,
                    b,
                    [[0, m.end(1) - a, "CANTIDAD"], [m.start(2) - a, b - a, "UNIDAD_MEDIDA"]],
                    "quantity_unit",
                )
            )
        for m in re.finditer(r"\b(precio unitario|total)\s+(\d+(?:[.,]\d+)*)", text, re.I):
            a, b = m.span()
            # A sentence-final dot is outside the number and source excerpt.
            found.append(
                (
                    a,
                    b,
                    [
                        [
                            m.start(2) - a,
                            b - a,
                            "PRECIO_UNITARIO"
                            if m[1].casefold().startswith("precio")
                            else "PRECIO_TOTAL",
                        ]
                    ],
                    "price",
                )
            )
        # Explicit local component relation; never infer another component's material.
        tech = r"\b(?:(Mesón|Tablero|Patas|Estructura)\s+(?:de\s+)?)?(melamina|MDF|MDP|vidrio templado|Aglomerado HDF)\s+de\s+(\d+(?:[.,]\d+)?\s*mm)\b"
        for m in re.finditer(tech, text, re.I):
            a, b = m.span()
            es = []
            if m[1]:
                es.append([m.start(1) - a, m.end(1) - a, "COMPONENTE"])
            es += [
                [m.start(2) - a, m.end(2) - a, "MATERIAL"],
                [m.start(3) - a, m.end(3) - a, "ESPESOR"],
            ]
            found.append((a, b, es, "local_material_thickness"))
        for m in re.finditer(r"\b(Mesón) engrosado a (\d+\s*mm)\b", text, re.I):
            a, b = m.span()
            found.append(
                (
                    a,
                    b,
                    [[0, m.end(1) - a, "COMPONENTE"], [m.start(2) - a, b - a, "ESPESOR"]],
                    "local_thickness",
                )
            )
        for m in re.finditer(r"\b(Clase)\s+(AC[45])\b", text, re.I):
            a, b = m.span()
            found.append((a, b, [[m.start(2) - a, b - a, "CLASE_RESISTENCIA"]], "resistance"))
        if item["document_level"] == "CATALOGO":
            for m in re.finditer(r"Bs\s*\d[\d.,]*\d|\d[\d.,]*\d\s*Bs\.?", text):
                a, b = m.span()
                found.append((a, b, [[0, b - a, "PRECIO_UNITARIO"]], "catalog_price"))
            for pattern, label in [
                (r"(?:apoya brazos|reposa brazos|Brazos|Reposa brazos) [^;.*\t]+", "APOYABRAZOS"),
                (
                    r"(?:parte lumbar|apoyo lumbar|reposa lumbar|soporte lumbar) [^;.*\t]+",
                    "SOPORTE_LUMBAR",
                ),
                (r"(?:reposa cabeza|reposacabezas) [^;.*\t]+", "CABECERA"),
                (r"(?:Soporte de peso hasta|alta resistencia hasta) \d+\s*kg", "OBSERVACION"),
            ]:
                for m in re.finditer(pattern, text, re.I):
                    a, b = m.span()
                    literal = m[0].rstrip(" ,")
                    b = a + len(literal)
                    found.append((a, b, [[0, b - a, label]], "catalog_attribute"))
        for n, (a, b, es, kind) in enumerate(found):
            literal = text[a:b]
            rid = item["id"] + f"-extract-{n:02d}"
            source = {
                k: item[k]
                for k in ("source_sha256", "source_file", "line_start", "line_end", "proforma_id")
            }
            source.update(
                source_item_id=item["id"],
                char_start=item["char_start"] + a,
                char_end=item["char_start"] + b,
                item_offset=[a, b],
                certainty="CONFIRMADA",
            )
            row = dict(
                id=rid,
                text=literal,
                text_sha256=digest(literal),
                entities=es,
                category=family(item),
                split="train",
                origin="DOCUMENTO_HOMEX_LITERAL",
                style="documental",
                leakage_group="original-documents-private-batch",
                source_ref=source,
                human_reviewed=False,
                annotation_version=VERSION,
                annotation_scope="EXTRACTO_LITERAL_CERRADO",
                transformation="EXTRACCION_SIN_REESCRITURA",
                review="TECNICA_AUTOMATIZADA_NO_HUMANA",
                supervised=True,
                phenomena=[kind],
            )
            c = {
                k: None
                for k in (
                    "nombre",
                    "cantidad",
                    "unidad_codigo",
                    "precio_unitario",
                    "precio_total_explicito",
                    "descuento_linea",
                    "moneda_codigo",
                )
            }
            components = []
            facts = []
            for x, y, label in es:
                raw = literal[x:y]
                key = {
                    "PRODUCTO": "nombre",
                    "CANTIDAD": "cantidad",
                    "PRECIO_UNITARIO": "precio_unitario",
                    "PRECIO_TOTAL": "precio_total_explicito",
                }.get(label)
                if key and kind != "catalog_price":
                    c[key] = raw if label == "PRODUCTO" else raw.replace(",", ".")
                if label == "UNIDAD_MEDIDA":
                    c["unidad_codigo"] = (
                        "M2"
                        if "Mts" in raw
                        else "JUEGO"
                        if raw.casefold() == "juego"
                        else "BARRA"
                        if raw.casefold().startswith("barra")
                        else "PIEZA"
                    )
                if label == "COMPONENTE":
                    components.append({"uid": "c1", "nombre": raw})
                if components and label in {"MATERIAL", "ESPESOR"}:
                    components[0][label.lower()] = raw
                facts.append(
                    {
                        "path": "fragment." + label.lower(),
                        "value": raw,
                        "evidence": {"start": x, "end": y, "text": raw},
                        "rule": "LITERAL_CLOSED_SCOPE",
                    }
                )
            ref = dict(
                id=rid,
                text_sha256=row["text_sha256"],
                comercial=c,
                especificacion={
                    "datos_tecnicos": {
                        "componentes": components,
                        "conjuntos": [],
                        "accesorios": [],
                        "caracteristicas_generales": {},
                        "advertencias": [],
                        "descripcion_original": literal,
                    }
                },
                facts=facts,
                partial=True,
                status="FRAGMENT_NOT_COMMERCIAL_LINE",
                human_reviewed=False,
            )
            if kind == "catalog_price":
                raw = re.sub(r"[^\d.,]", "", literal)
                ref["catalog_price"] = raw.replace(".", "").replace(",", ".") if "," in raw else raw
                ref["price_context"] = "CATALOGO_NO_NEGOCIADO"
            rows.append(row)
            refs.append(ref)
    # Identical excerpts are one training observation with every authentic source link.
    unique, unique_refs = {}, {}
    for row, ref in zip(rows, refs):
        key = row["text_sha256"]
        if key in unique:
            unique[key]["additional_source_refs"].append(row["source_ref"])
        else:
            row["additional_source_refs"] = []
            unique[key] = row
            unique_refs[key] = ref
    return list(unique.values()), list(unique_refs.values()), len(rows)


def build(output, sources):
    output = private_path(output)
    if output.exists():
        raise ValueError("OUTPUT_EXISTS")
    ingest(sources, output / "sources")
    items = read(output / "sources/document_items.jsonl")
    excluded = {r["id"] for r in read(output / "sources/document_quarantine.jsonl")}
    # Additional literal anomalies: unknown units are preserved, never repaired.
    for item in items:
        if re.search(
            r"(?<![\d.,])80\s*mts\b|Altura\s*=\s*40\s*m\b|0[.,]50\s*cm|0,3\.6",
            item["item_text"],
            re.I,
        ):
            excluded.add(item["id"])
    docs, doc_refs, raw_fragments = documentary(items, excluded)
    rows = read(ROOT / "data/canonical_v2/synthetic.jsonl")
    refs = read(ROOT / "data/canonical_v2/synthetic_expected.jsonl")
    synthetic_ids = {r["id"] for r in rows}
    for r in rows:
        r.update(
            annotation_version=VERSION,
            transformation="RC2_PRESERVED",
            annotation_scope="CASE",
            review="TECHNICAL_NOT_HUMAN",
        )
    # All private-source fragments stay train; exact/numeric equivalents cannot cross to dev.
    fingerprints = {normalized(r["text"]) for r in docs}
    tainted_groups = {r["leakage_group"] for r in rows if normalized(r["text"]) in fingerprints}
    for r in rows:
        if r["leakage_group"] in tainted_groups:
            r["split"] = "train"
    rows += docs
    refs += doc_refs
    matrix, overlays, baseline = [], [], {}
    for f in FAMILIES:
        for folder, extension in [("corpus", "jsonl"), ("expected", "jsonl"), ("splits", "json")]:
            path = ROOT / "data" / folder / (f + "." + extension)
            baseline[str(path.relative_to(ROOT))] = digest(path.read_bytes())
        for r in read(ROOT / "data/corpus" / (f + ".jsonl")):
            # Test text/spans are never curated or used to construct any new example.
            m = dict(
                id=r["id"],
                family=f,
                historical_split=r["split"],
                text_sha256=r["text_sha256"],
                correspondence="NO_IDENTIFICADA",
                destination="FROZEN_BASELINE",
                decision="PENDIENTE",
                reason="Historical test protected"
                if r["split"] == "test"
                else "Synthetic source unlinked; not promoted to documentary",
                human_reviewed=False,
            )
            if r["split"] != "test":
                p = patches(deepcopy(r))
                audit = audit_literal(r["text"], f)
                p["semantic_audit"] = audit
                overlays.append(p)
                m.update(
                    correction_operations=len(p["operations"]), semantic_errors=audit["errors"]
                )
                if p["operations"]:
                    m["decision"] = "CORREGIDO"
                    m["reason"] = "Reversible ACCESORIO overlay only; V1 untouched"
            matrix.append(m)
    jsonl(output / "records.jsonl", sorted(rows, key=lambda r: r["id"]))
    jsonl(output / "expected.jsonl", sorted(refs, key=lambda r: r["id"]))
    jsonl(output / "v1_reconciliation.jsonl", matrix)
    jsonl(output / "v1_reversible_overlays.jsonl", overlays)
    dump(output / "baseline_sha256.json", baseline)
    jsonl(
        output / "source_review.jsonl",
        [
            dict(
                id=i["id"],
                origin="DOCUMENTO_HOMEX",
                certainty="CONFIRMADA",
                proforma_id=None,
                status="PENDIENTE" if i["id"] in excluded else "APROBADO_EXTRACTOS",
                full_item_status="NOT_GOLD",
                reason="ANOMALIA_LITERAL"
                if i["id"] in excluded
                else "Conservative closed-scope extraction; full item preserved privately",
                source_sha256=i["source_sha256"],
                line_start=i["line_start"],
                line_end=i["line_end"],
            )
            for i in items
        ],
    )
    report = validate(
        read(output / "records.jsonl"), read(output / "expected.jsonl"), docbin=output / "docbin"
    )
    dump(output / "validation.json", report)
    if not report["valid"]:
        raise ValueError("CORPUS_VALIDATION_FAILED: " + str(report["errors"][:5]))
    manifest = dict(
        version=VERSION,
        records=len(rows),
        families=dict(Counter(r["category"] for r in rows)),
        origin=dict(Counter(r["origin"] for r in rows)),
        style=dict(Counter(r["style"] for r in rows)),
        split=dict(Counter(r["split"] for r in rows)),
        labels=report["labels"],
        phenomena=dict(Counter(p for r in rows for p in r.get("phenomena", []))),
        source_items=len(items),
        source_anomalies=len(excluded),
        documentary_excerpts=len(docs),
        raw_documentary_excerpts=raw_fragments,
        synthetic_records=len(synthetic_ids),
        historical_records=len(matrix),
        historical_entity_corrections=sum(bool(p["operations"]) for p in overlays),
        rc1_proposed_corrections=375,
        rc1_proposals_status="Historical proposals, not 375 additional records; baseline excluded from canonical V2",
        historical_pilot_48="NOT_FOUND; RC1 oral 40 are a different artifact",
        independent_internal_test=0,
        external_test=0,
        human_gold=False,
        private_documents_train_only=True,
        evaluation_policy="Synthetic dev diagnostic only; no documentary or voice generalization claim",
        source_commits={
            "main": "81d70395d2bb6cfa4757eaaacb95c6179feae332",
            "rc2": "b27edfa",
            "pr24": "4c94a75",
            "pr31": "fb1ad97",
        },
    )
    dump(output / "manifest.json", manifest)
    dump(
        output / "sha256.json",
        {
            str(p.relative_to(output)): digest(p.read_bytes())
            for p in sorted(output.rglob("*"))
            if p.is_file()
        },
    )
    protect(output)
    return manifest


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--sources", type=Path, nargs="+", required=True)
    a = p.parse_args()
    print(json.dumps(build(a.output, a.sources)))


if __name__ == "__main__":
    main()
