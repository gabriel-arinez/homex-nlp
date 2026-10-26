"""Private-only documentary inventory. Never point --output inside a Git checkout.

Preserves original bytes and line/byte boundaries. Blocks are item candidates,
not invented proformas. No commercial text is emitted on stdout.
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
from decimal import Decimal
from pathlib import Path

from training.corpus_v2.build import dump, jsonl, table


def ingest(sources, output, review_recipes=None):
    output = output.resolve()
    probe = output
    while not probe.exists():
        probe = probe.parent
    if (
        subprocess.run(
            ["git", "-C", str(probe), "rev-parse", "--is-inside-work-tree"], capture_output=True
        ).returncode
        == 0
    ):
        raise ValueError("Private output cannot be inside a Git checkout")
    output.mkdir(parents=True, exist_ok=True)
    os.chmod(output, 0o700)
    source_manifest = []
    items = []
    quarantine = []
    for source in sources:
        raw = source.read_bytes()
        text = raw.decode("utf-8-sig")
        sha = hashlib.sha256(raw).hexdigest()
        target = output / "originals" / source.name
        target.parent.mkdir(exist_ok=True)
        if target.exists() and target.read_bytes() != raw:
            raise ValueError("Refusing to overwrite different original")
        if not target.exists():
            shutil.copyfile(source, target)
        os.chmod(target, 0o600)
        source_manifest.append(
            {
                "file": source.name,
                "sha256": sha,
                "bytes": len(raw),
                "lines": len(text.splitlines()),
                "publication": "PRIVATE_ONLY",
                "original_path": str(source),
            }
        )
        # Catalogue has one item per nonblank line; quotation files use blank separators.
        segments = (
            list(re.finditer(r"[^\r\n]+", text))
            if source.name == "inventario de sillas.txt"
            else list(re.finditer(r"\S[^\n]*(?:\n(?!\s*\n)[^\n]+)*", text))
        )
        joined = []
        pos = 0
        while pos < len(segments):
            m = segments[pos]
            start, end = m.span()
            block_ids = [pos + 1]
            if (
                source.name != "inventario de sillas.txt"
                and "\n" not in m[0]
                and pos + 1 < len(segments)
                and re.match(r"\d+[,.]\d+\s+(?:Juego|Pza|PIEZAS)", segments[pos + 1][0])
            ):
                end = segments[pos + 1].end()
                block_ids.append(pos + 2)
                pos += 1
            joined.append((start, end, block_ids))
            pos += 1
        for idx, (start, end, block_ids) in enumerate(joined, 1):
            literal = text[start:end]
            if not literal.strip():
                continue
            item = {
                "id": sha[:12] + f"-item-{idx:03d}",
                "source_file": source.name,
                "source_sha256": sha,
                "block": idx,
                "raw_blocks": block_ids,
                "line_start": text[:start].count("\n") + 1,
                "line_end": text[:end].count("\n") + 1,
                "char_start": start,
                "char_end": end,
                "byte_start": len(text[:start].encode())
                + (3 if raw.startswith(b"\xef\xbb\xbf") else 0),
                "byte_end": len(text[:end].encode())
                + (3 if raw.startswith(b"\xef\xbb\xbf") else 0),
                "proforma_id": None,
                "item_text": literal,
                "item_sha256": hashlib.sha256(literal.encode()).hexdigest(),
                "document_level": "CATALOGO"
                if source.name == "inventario de sillas.txt"
                else "COTIZACION_SIN_ID_PROFORMA",
                "origin": "DOCUMENTO_HOMEX",
                "status": "REQUIERE_REVISION_HUMANA",
                "supervised": False,
                "note": "Bloque candidato a ítem; no es una proforma identificada.",
            }
            items.append(item)
            reasons = []
            for pattern, reason in [
                (r"Altura=40m", "UNIDAD_SOSPECHOSA_40M"),
                (r"80mts", "UNIDAD_SOSPECHOSA_80M"),
                (r"0\.50 Cm", "MEDIDA_MESON_0_50CM"),
                (r"0,3\.6", "NUMERO_MALFORMADO"),
            ]:
                for hit in re.finditer(pattern, literal, re.I):
                    reasons.append(
                        {
                            "code": reason,
                            "literal": hit[0],
                            "item_start": hit.start(),
                            "item_end": hit.end(),
                        }
                    )
            unit_match = re.search(r"unitario\s+(\d(?:[\d.,]*\d)?)", literal, re.I)
            total_match = re.search(r"total\s+(\d(?:[\d.,]*\d)?)", literal, re.I)
            if unit_match and total_match:

                def money(v):
                    return Decimal(v.replace(".", "").replace(",", ".")) if "," in v else Decimal(v)

                if money(total_match[1]) < money(unit_match[1]) and not re.search(
                    r"\d+[,.]\d+\s+(?:Pza|Unidad|PIEZA)", literal, re.I
                ):
                    reasons.append(
                        {
                            "code": "IMPORTES_DISCREPANTES_CANTIDAD_AUSENTE",
                            "literal": unit_match[0] + "; " + total_match[0],
                            "note": "Sin cantidad no se demuestra ecuación; no sustituir ningún importe.",
                        }
                    )
            if reasons:
                quarantine.append(
                    {
                        "id": item["id"],
                        "source_ref": {
                            k: item[k]
                            for k in (
                                "source_file",
                                "block",
                                "line_start",
                                "line_end",
                                "source_sha256",
                            )
                        },
                        "issues": reasons,
                        "text": literal,
                        "supervised": False,
                        "decision": "PRESERVAR_LITERAL_REQUIERE_REVISION_HUMANA",
                    }
                )
    jsonl(output / "document_items.jsonl", items)
    dump(output / "source_manifest.json", source_manifest)
    jsonl(output / "document_quarantine.jsonl", quarantine)
    # Four literal technical examples, with authored semantic expectations. Not human gold.
    picks = json.loads(review_recipes.read_text()) if review_recipes else []
    documentary = []
    expected = []
    for n, recipe in enumerate(picks, 1):
        family, file, title, qty, unit, price, total = [
            recipe[k] for k in ("family", "file", "title", "quantity", "unit", "price", "total")
        ]
        item = next(
            i for i in items if i["source_file"] == file and i["item_text"].startswith(title)
        )
        text = item["item_text"]
        rid = f"V2-PRIVATE-DOC-{n:02d}"
        assertions = []
        entities = []

        def claim(path, value, literal, label=None):
            a = text.index(literal)
            b = a + len(literal)
            assertions.append(
                {
                    "path": path,
                    "value": value,
                    "evidence": {"start": a, "end": b, "text": literal},
                    "rule": "REFERENCIA_LITERAL_REVISADA_CODEX_NO_HUMANA",
                }
            )
            if label:
                entities.append([a, b, label])

        claim("comercial.nombre", title, title, "PRODUCTO")
        qty_lit = qty.replace(".", ",")
        claim("comercial.cantidad", qty, qty_lit, "CANTIDAD")
        unit_lit = {"PIEZA": "Pza", "M2": "Mts.2", "BARRA": "barra"}[unit]
        claim("comercial.unidad_codigo", unit, unit_lit, "UNIDAD_MEDIDA")
        price_lit = price.replace(".", ",")
        total_lit = total.replace(".", ",")
        # Repeated equal unit/total literals require distinct offsets.
        a = text.lower().index("precio unitario") + len("precio unitario")
        hit = re.search(re.escape(price_lit), text[a:])
        pa = a + hit.start()
        assertions.append(
            {
                "path": "comercial.precio_unitario",
                "value": price,
                "evidence": {"start": pa, "end": pa + len(price_lit), "text": price_lit},
                "rule": "DECIMAL_LITERAL",
            }
        )
        entities.append([pa, pa + len(price_lit), "PRECIO_UNITARIO"])
        a = text.lower().index("total", pa) + len("total")
        hit = re.search(re.escape(total_lit), text[a:])
        ta = a + hit.start()
        assertions.append(
            {
                "path": "comercial.precio_total_explicito",
                "value": total,
                "evidence": {"start": ta, "end": ta + len(total_lit), "text": total_lit},
                "rule": "DECIMAL_LITERAL",
            }
        )
        entities.append([ta, ta + len(total_lit), "PRECIO_TOTAL"])
        tech = {
            "descripcion_original": text,
            "componentes": [],
            "conjuntos": [],
            "accesorios": [],
            "caracteristicas_generales": {},
            "advertencias": [
                "Referencia comercial parcial; demás atributos conservados en literal y pendientes de anotación."
            ],
        }
        if family == "muebles_pedido":
            # Hand-specified two component scopes, supported by the circular table source.
            for idx, component in enumerate(recipe["components"]):
                name, thickness = component["name"], component["thickness"]
                tech["componentes"].append(
                    {
                        "uid": f"c{idx + 1}",
                        "nombre": name,
                        "material": "melamina",
                        "espesor": thickness,
                    }
                )
                claim(f"componentes.c{idx + 1}.nombre", name, name, "COMPONENTE")
                # Locate local repeated material in its own clause, not first global match.
                start = text.index(name)
                mat = text.index("melamina", start)
                assertions.append(
                    {
                        "path": f"componentes.c{idx + 1}.material",
                        "value": "melamina",
                        "evidence": {"start": mat, "end": mat + 8, "text": "melamina"},
                        "rule": "AMBITO_LOCAL",
                    }
                )
                entities.append([mat, mat + 8, "MATERIAL"])
                claim(f"componentes.c{idx + 1}.espesor", thickness, thickness, "ESPESOR")
        row = {
            "id": rid,
            "category": family,
            "text": text,
            "text_sha256": hashlib.sha256(text.encode()).hexdigest(),
            "entities": sorted(entities),
            "origin": "DOCUMENTO_HOMEX",
            "style": "documental",
            "source_ref": {
                k: item[k]
                for k in ("source_file", "source_sha256", "block", "line_start", "line_end", "id")
            },
            "human_reviewed": False,
            "status": "REQUIRES_REVIEW",
            "supervised": False,
            "split": "quarantine",
            "reason": "Original comercial privado; anotación parcial técnica, homologación comercial pendiente.",
        }
        documentary.append(row)
        expected.append(
            {
                "id": rid,
                "text_sha256": row["text_sha256"],
                "comercial": {
                    "nombre": title,
                    "cantidad": qty,
                    "unidad_codigo": unit,
                    "precio_unitario": price,
                    "precio_total_explicito": total,
                    "moneda_codigo": None,
                    "descuento_linea": None,
                },
                "especificacion": {"datos_tecnicos": tech}
                if family == "muebles_pedido"
                else {"atributos_catalogo": []},
                "facts": assertions,
                "human_reviewed": False,
                "partial": True,
            }
        )
        assert Decimal(qty) * Decimal(price) == Decimal(total)
    for family in ("muebles_pedido", "sillas", "pisos_flotantes", "otros_productos"):
        jsonl(
            output / "04_CORPUS_DOCUMENTAL_V2" / f"{family}.jsonl",
            [r for r in documentary if r["category"] == family],
        )
        jsonl(
            output / "06_EXPECTED_ESTRUCTURADOS_V2" / f"{family}.jsonl",
            [
                r
                for r in expected
                if any(d["id"] == r["id"] and d["category"] == family for d in documentary)
            ],
        )
    # Catalogue versus quotation: independent documented contexts, no price replacement.
    comparisons = []
    for code in ("B15b", "D43", "NF-810"):
        catalog = [
            i
            for i in items
            if i["document_level"] == "CATALOGO"
            and re.search(r"(?<![\w-])" + re.escape(code) + r"(?![\w-])", i["item_text"])
        ]
        quotes = [
            i
            for i in items
            if i["source_file"] == "SILLAS-PISOS-OTROS.txt" and code in i["item_text"]
        ]
        for a in catalog:
            for b in quotes:
                comparisons.append(
                    {
                        "code": code,
                        "catalog_item": a["id"],
                        "quotation_item": b["id"],
                        "catalog_literal": a["item_text"],
                        "quotation_literal": b["item_text"],
                        "decision": "CONTEXTOS_DIFERENTES_NO_ERROR_AUTOMATICO",
                        "date": "NO_CONSTA",
                        "review": "HUMANA_PENDIENTE",
                    }
                )
    table(output / "catalog_quotation_comparisons.csv", comparisons)
    dump(
        output / "summary.json",
        {
            "source_files": len(source_manifest),
            "item_candidates": len(items),
            "anomalous_items": len(quarantine),
            "private_partial_examples": len(documentary),
            "supervised_authentic": 0,
            "proformas_identified": 0,
            "prices_catalog_vs_negotiated": "PRESERVADOS_SEPARADAMENTE",
            "human_review": False,
        },
    )
    for p in output.rglob("*"):
        os.chmod(p, 0o700 if p.is_dir() else 0o600)
    print(
        json.dumps(
            {
                "private_sources": len(source_manifest),
                "private_item_candidates": len(items),
                "private_anomalies": len(quarantine),
                "private_partial_examples": len(documentary),
            }
        )
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sources", type=Path, nargs="+", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--review-recipes", type=Path)
    a = parser.parse_args()
    ingest(a.sources, a.output, a.review_recipes)


if __name__ == "__main__":
    main()
