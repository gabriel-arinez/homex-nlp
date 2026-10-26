"""Rebuild the opt-in candidate from immutable V1 + explicit synthetic recipes.

No authentic commercial TXT content is written to Git. Private ingest is separate.
"""

import argparse
import csv
import hashlib
import itertools
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from training.corpus_v2.semantic import audit_literal

FAMILIES = ("muebles_pedido", "sillas", "pisos_flotantes", "otros_productos")
DEFAULT = Path("data/candidates/corpus_v2_rc1")
BASE = "45404c6580ae2d488b338c46ba63689feccb3501"
SEED = "20261025"
DOC = "04_CORPUS_DOCUMENTAL_V2"
ORAL = "05_CORPUS_ORAL_V2"
EXPECTED = "06_EXPECTED_ESTRUCTURADOS_V2"
MANIFEST = "07_SPLITS_Y_MANIFIESTOS_V2"


def digest(b):
    return hashlib.sha256(b).hexdigest()


def dump(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=2) + "\n")


def jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows))


def table(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    k: json.dumps(v, ensure_ascii=False, sort_keys=True)
                    if isinstance(v, (dict, list))
                    else v
                    for k, v in row.items()
                }
            )


def read(path):
    return [json.loads(s) for s in path.read_text().splitlines()]


def template(row):
    text = row["text"]
    for a, b, label in sorted(row["entities"], reverse=True):
        text = text[:a] + "<" + label + ">" + text[b:]
    return re.sub(r"\s+", " ", text.lower()).strip()


class Groups:
    def __init__(self, ids):
        self.parent = {i: i for i in ids}

    def find(self, i):
        if self.parent[i] != i:
            self.parent[i] = self.find(self.parent[i])
        return self.parent[i]

    def union(self, a, b):
        x, y = sorted((self.find(a), self.find(b)))
        self.parent[y] = x


def build(root=Path("."), out=DEFAULT):
    all_rows, refs, audits, changes, links, risks, pending = [], {}, [], [], [], [], []
    baseline = {
        str(p.relative_to(root)): digest(p.read_bytes())
        for folder in ("corpus", "expected", "splits", "manifests")
        for p in sorted((root / "data" / folder).rglob("*"))
        if p.is_file()
    }
    old = [r for f in FAMILIES for r in read(root / "data/corpus" / f"{f}.jsonl")]
    reconciliation = json.loads(
        (root / "training/corpus_v2/source_reconciliation.json").read_text()
    )
    reconciled = {entry["v1_id"]: entry for entry in reconciliation["records"]}
    if len(reconciled) != len(old) or any(
        reconciled[r["id"]]["text_sha256"] != r["text_sha256"] for r in old
    ):
        raise ValueError("Reconciliation does not match immutable V1")
    old_refs = {r["id"]: r for f in FAMILIES for r in read(root / "data/expected" / f"{f}.jsonl")}
    for original in old:
        r = dict(original)
        r["entities"] = [list(e) for e in original["entities"]]
        oid = r["id"]
        rid = "V2-" + oid
        r.update(
            id=rid,
            origin="SINTETICO_DOCUMENTAL",
            v1_id=oid,
            style="documental",
            reference_quality="TECNICA_CODEX_NO_GOLD_HUMANO",
            human_reviewed=False,
            source_ref={
                "kind": "V1_SINTETICO",
                "path": f"data/corpus/{r['category']}.jsonl",
                "id": oid,
                "text_sha256": r["text_sha256"],
            },
            phenomena=["documental_tecnico"],
            example_kind="POSITIVO_SINTETICO",
            status="REQUIRES_REVIEW",
            supervised=True,
        )
        sem = audit_literal(r["text"], r["category"])
        issues = list(sem.pop("errors"))
        # Every V1 target is recorded; expected changes have complete before/after.
        before = old_refs[oid]["expected"]
        diffs = []
        for entity in r["entities"]:
            a, b, label = entity
            if label == "ACCESORIO" and r["text"][a:b] == "incluida con el piso":
                head = r["text"].rfind("Membrana protectora ", 0, a)
                if head >= 0 and r["text"][head:a] == "Membrana protectora ":
                    entity[0] = head
                    diffs.append("SPAN_MEMBRANA_INCLUYE_NUCLEO_NOMINAL")
        if sem["comercial"]["descuento_linea"] is not None:
            diffs.append("DESCUENTO_EXPLICITO_AUSENTE_EN_EXPECTED_V1")
        if sem["cantidades_internas"]:
            diffs.append("RELACION_CANTIDAD_INTERNA_EXPLICITA")
        if sem["capacidades"]:
            diffs.append("CAPACIDAD_SEPARADA_DE_CANTIDAD")
        if r["category"] == "muebles_pedido":
            new = sem["especificacion"]["datos_tecnicos"]["componentes"]
            old_c = before["especificacion"]["datos_tecnicos"]["componentes"]
            for a, b in zip(old_c, new):
                for k in ("nombre", "material", "espesor", "color", "acabado"):
                    if a.get(k) != b.get(k):
                        issues.append("DISCREPANCIA_COMPONENTE:" + k)
            if len(old_c) != len(new):
                issues.append("NUMERO_COMPONENTES")
        for k, v in before["comercial"].items():
            if sem["comercial"].get(k) != v:
                issues.append("DISCREPANCIA_COMERCIAL:" + k)
        for a, b, label in r["entities"]:
            if label == "COLOR" and r["text"][a:b].lower() in ("a elección", "según diseño"):
                issues.append("COLOR_PENDIENTE_ETIQUETADO_COMO_COLOR")
        state = (
            "REQUIERE_REVISION_HUMANA"
            if issues
            else "CORREGIDO"
            if diffs
            else "APROBADO_SIN_CAMBIO"
        )
        if issues:
            r.update(supervised=False, split="quarantine")
            pending.append(
                {
                    "id": rid,
                    "v1_id": oid,
                    "reason": issues,
                    "evidence": r["text"],
                    "alternatives": "Revisar evidencia; no imponer valor.",
                }
            )
        sem.update(id=rid, text_sha256=r["text_sha256"], status=r["status"], human_reviewed=False)
        refs[rid] = sem
        all_rows.append(r)
        audits.append(
            {
                "v1_id": oid,
                "v2_id": rid,
                "family": r["category"],
                "source_id": original["source_id"],
                "metadata": original["metadata"],
                "origin_declared": original["origin"],
                "source_line": original["source_line"],
                "proforma_id": r["proforma_id"],
                "item_id": r["item_id"],
                "family_id": r["family_id"],
                "text_sha256": r["text_sha256"],
                "record_sha256": digest(
                    json.dumps(original, sort_keys=True, ensure_ascii=False).encode()
                ),
                "split_v1": original["split"],
                "spans": original["entities"],
                "ner_review": [
                    {
                        "span": e,
                        "literal": r["text"][e[0] : e[1]],
                        "scope": "NER_LITERAL_NO_GARANTIZA_RELACION",
                    }
                    for e in r["entities"]
                ],
                "expected_v1": old_refs[oid],
                "anomalies": issues + diffs,
                "severity": "ALTA" if issues else "MEDIA" if diffs else "INFORMATIVA",
                "state": state,
                "decision": "pendiente"
                if issues
                else "corregir_expected"
                if diffs
                else "conservar",
                "evidence": sem["facts"],
                "document_link": "NO_IDENTIFICADA",
                "human_reviewed": False,
            }
        )
        changes.append(
            {
                "v1_id": oid,
                "v2_id": rid,
                "operation": state,
                "source_ref": r["source_ref"],
                "before": {"expected": before, "entities": original["entities"]},
                "entities_after": r["entities"],
                "after": {
                    k: sem[k]
                    for k in ("comercial", "especificacion", "cantidades_internas", "capacidades")
                },
                "reason": issues + diffs
                or ["Texto sintético útil; controles literales aprobados."],
                "proof": sem["facts"],
                "review": "TECNICA_CODEX_NO_HUMANA",
            }
        )
        links.append(
            {
                "v1_id": oid,
                "source_file": "",
                "block": "",
                "line_start": "",
                "line_end": "",
                "item_id": "",
                "status": "NO_IDENTIFICADA",
                "evidence": f"Comparación literal con {reconciled[oid]['compared_source_items']} ítems privados, resultado {reconciled[oid]['state']}; texto V1 SHA-256 {r['text_sha256']}. Títulos no certifican procedencia.",
                "declared_origin": "SINTETICO_DOCUMENTAL",
            }
        )
    # Reproduce the historical detector without adding a non-manifest NER label.
    signals = []
    for r in old:
        hits = list(
            re.finditer(r"\b(?:dos cajones|tres cajones|tres repisas interiores)\b", r["text"])
        )
        for m in hits:
            signals.append(
                {
                    "id": r["id"],
                    "text": m[0],
                    "start": m.start(),
                    "end": m.end(),
                    "classification": "FALSO_POSITIVO_NER_CON_RELACION_CONFIRMADA",
                    "reason": "CANTIDAD_INTERNA no existe entre las 24 etiquetas NER. Relación literal incluida en V2; no cantidad comercial.",
                }
            )
    prefixes = defaultdict(list)
    for r in old:
        prefixes[r["text"][:65]].append(r)
    prefix_groups = []
    for prefix, rows in sorted(prefixes.items()):
        splits = sorted({r["split"] for r in rows})
        if len(splits) > 1:
            prefix_groups.append(
                {
                    "prefix": prefix,
                    "ids": [r["id"] for r in rows],
                    "splits": splits,
                    "classification": "CONFIRMADO_RIESGO_PLANTILLA_NO_COPIA_INTEGRA",
                    "action": "Unir componentes de partición V2.",
                }
            )
    # Protect proformas, literal templates, original groups, and prefix risks transitively.
    groups = Groups([r["id"] for r in all_rows])
    keys = {}
    for r in all_rows:
        for key in [
            ("proforma", r["proforma_id"]),
            ("family", r["family_id"]),
            ("template", template(r)),
            ("prefix", r["text"][:65]),
        ]:
            if key in keys:
                groups.union(r["id"], keys[key])
            else:
                keys[key] = r["id"]
    members = defaultdict(list)
    for r in all_rows:
        members[groups.find(r["id"])].append(r)
    components = []
    for gid, rows in sorted(members.items()):
        old_splits = {r["split"] for r in rows}
        # Never route historical test to train/dev, nor original dev to train.
        split = "test" if "test" in old_splits else "dev" if "dev" in old_splits else "train"
        for r in rows:
            r["leakage_group"] = gid
            if r["supervised"]:
                r["split"] = split
        components.append(
            {
                "group": gid,
                "size": len(rows),
                "historical_splits": sorted(old_splits),
                "split": split,
            }
        )
    # Hand-authored semantic recipes: reference assertions exist before NER rendering.
    recipes = json.loads((root / "training/corpus_v2/recipes.json").read_text())
    for recipe in recipes:
        markup = recipe["annotated"]
        text = ""
        entities = []
        cursor = 0
        for m in re.finditer(r"\[\[([A-Z_]+)\|(.+?)\]\]", markup):
            text += markup[cursor : m.start()]
            start = len(text)
            text += m[2]
            entities.append([start, len(text), m[1]])
            cursor = m.end()
        text += markup[cursor:]
        rid = recipe["id"]
        source_id = recipe.get("parent_id")
        source = next((r for r in all_rows if r["id"] == source_id), None)
        group = recipe["group"]
        split = {
            "mueble_oral": "train",
            "silla_oral": "dev",
            "piso_oral": "train",
            "otros_oral": "dev",
            "mueble_rectificacion": "dev",
            "mueble_fuera": "test",
        }.get(group, "train")
        if source:
            group, split = source["leakage_group"], source["split"]
        r = {
            "id": rid,
            "v1_id": None,
            "category": recipe["category"],
            "text": text,
            "text_sha256": digest(text.encode()),
            "entities": entities,
            "origin": "SINTETICO_ORAL" if recipe["style"] == "oral" else "SINTETICO_DOCUMENTAL",
            "style": recipe["style"],
            "human_reviewed": False,
            "reference_quality": "RECETA_SEMANTICA_EXPLICITA_CODEX_NO_HUMANA",
            "split": split,
            "family_id": group,
            "leakage_group": group,
            "proforma_id": None,
            "item_id": rid,
            "source_ref": {
                "kind": "RECETA_SINTETICA",
                "path": "training/corpus_v2/recipes.json",
                "id": rid,
            },
            "parent_id": source_id,
            "phenomena": recipe["phenomena"],
            "supervised": True,
            "status": recipe["status"],
            "example_kind": "NEGATIVO"
            if recipe["status"] == "ABSTAIN"
            else "AMBIGUO"
            if set(recipe["phenomena"])
            & {
                "precio_ambiguo",
                "anafora_ambigua",
                "unidad_omitida",
                "unidad_sospechosa",
                "sku_no_verificado",
                "unidad_ambigua",
                "cantidad_ausente",
                "color_pendiente",
                "perturbacion_asr_sintetica",
            }
            else "POSITIVO_PARCIAL",
        }
        if source_id and not source:
            raise ValueError("Parent missing: " + source_id)
        if source and source["split"] == "test" and recipe["style"] == "oral":
            raise ValueError("No generating oral variants of reserved test: " + source_id)
        exp = recipe["expected"]
        facts = []
        for assertion in recipe.get("assertions", []):
            literal = assertion["literal"]
            occurrence = assertion.get("occurrence", 0)
            starts = [m.start() for m in re.finditer(re.escape(literal), text)]
            if occurrence >= len(starts):
                raise ValueError((rid, literal))
            a = starts[occurrence]
            facts.append(
                {k: v for k, v in assertion.items() if k not in ("literal", "occurrence")}
                | {"evidence": {"start": a, "end": a + len(literal), "text": literal}}
            )
        exp = dict(exp)
        relations = []
        for relation in recipe.get("relations", []):
            literal = relation["literal"]
            a = text.index(literal)
            relations.append(
                {k: v for k, v in relation.items() if k != "literal"}
                | {
                    "commercial": False,
                    "evidence": {"start": a, "end": a + len(literal), "text": literal},
                }
            )
        exp["research_relations"] = relations
        tech = exp.get("especificacion", {}).get("datos_tecnicos")
        if tech is not None:
            tech["descripcion_original"] = text
        refs[rid] = exp | {
            "id": rid,
            "text_sha256": r["text_sha256"],
            "status": r["status"],
            "facts": facts,
            "reference_method": "RECETA_SEMANTICA_EXPLICITA_NO_DERIVADA_DE_NER",
            "human_reviewed": False,
        }
        all_rows.append(r)
        changes.append(
            {
                "v1_id": "",
                "v2_id": rid,
                "operation": "NUEVO_SINTETICO",
                "source_ref": r["source_ref"],
                "before": None,
                "entities_after": r["entities"],
                "after": exp,
                "reason": r["phenomena"],
                "proof": facts,
                "review": "TECNICA_CODEX_NO_HUMANA",
            }
        )
    # Pairs across partitions: literal word shingles, conservative threshold, no vector service.
    shingles = {}
    for r in all_rows:
        words = re.findall(r"\w+", r["text"].lower())
        shingles[r["id"]] = {tuple(words[i : i + 4]) for i in range(len(words) - 3)}
    for a, b in itertools.combinations(all_rows, 2):
        sa, sb = shingles[a["id"]], shingles[b["id"]]
        sim = len(sa & sb) / len(sa | sb) if sa | sb else 0
        if sim >= 0.50:
            risks.append(
                {
                    "a": a["id"],
                    "b": b["id"],
                    "jaccard_4gram": round(sim, 6),
                    "cross_split": a["split"] != b["split"],
                    "decision": "MISMO_GRUPO"
                    if a["leakage_group"] == b["leakage_group"]
                    else "REVISAR",
                }
            )
    # No unresolved known cross-split similarity is allowed in supervised sets.
    for risk in risks:
        if risk["cross_split"]:
            raise ValueError("Unhandled near duplicate " + str(risk))
    for family in FAMILIES:
        for folder, style in ((DOC, "documental"), (ORAL, "oral")):
            jsonl(
                out / folder / f"{family}.jsonl",
                [
                    r
                    for r in all_rows
                    if r["category"] == family and r["style"] == style and r["supervised"]
                ],
            )
        jsonl(
            out / EXPECTED / f"{family}.jsonl",
            [refs[r["id"]] for r in all_rows if r["category"] == family and r["supervised"]],
        )
    jsonl(out / "quarantine/records.jsonl", [r for r in all_rows if not r["supervised"]])
    dump(out / "01_AUDITORIA_V1_675.json", audits)
    table(out / "01_AUDITORIA_V1_675.csv", audits)
    table(out / "02_CORRESPONDENCIA_DOCUMENTAL.csv", links)
    table(out / "09_MATRIZ_V1_V2.csv", changes)
    dump(out / "10_PENDIENTES_REVISION_HUMANA.json", pending)
    table(
        out / "10_PENDIENTES_REVISION_HUMANA.csv",
        pending
        or [
            {
                "id": "HOMOLOGACION_GLOBAL",
                "v1_id": "",
                "reason": "Homologación humana no obtenida; todo V2 es candidato técnico.",
                "evidence": "Revisión Codex declarada por registro.",
                "alternatives": "Revisión comercial antes de gold.",
            }
        ],
    )
    dump(out / MANIFEST / "baseline_v1_sha256.json", baseline)
    dump(
        out / MANIFEST / "historical_signals.json",
        {
            "quantity_signals": signals,
            "prefix_groups": prefix_groups,
            "historical_report_available": False,
            "detector": "regex documentada; prefijo literal Unicode 65",
            "note": "No se dispone del JSON 1b original. Los contadores se reconstruyen; no se atribuye identidad exacta al detector histórico.",
        },
    )
    dump(out / MANIFEST / "risk_pairs.json", risks)
    dump(out / MANIFEST / "split_groups.json", components)
    splits = {
        s: [r["id"] for r in all_rows if r["split"] == s and r["supervised"]]
        for s in ("train", "dev", "test")
    }
    dump(
        out / MANIFEST / "splits.json",
        {
            "seed": SEED,
            "algorithm": "union-proforma-family-template-prefix; historical-test-wins; authored-semantic-groups-v1",
            "assignments": splits,
            "test_external_human": [],
            "sealed_for_training": True,
            "blind": False,
            "note": "Test sintético retrospectivo conocido por auditoría; no es externo ciego. No se ejecutó motor sobre test.",
        },
    )
    counts = {
        "total": len(all_rows),
        "included": sum(r["supervised"] for r in all_rows),
        "v1_audited": len(audits),
        "v1_states": dict(Counter(a["state"] for a in audits)),
        "families": dict(Counter(r["category"] for r in all_rows)),
        "origins": dict(Counter(r["origin"] for r in all_rows)),
        "styles": dict(Counter(r["style"] for r in all_rows)),
        "splits": {k: len(v) for k, v in splits.items()},
        "phenomena": dict(Counter(p for r in all_rows for p in r["phenomena"])),
        "example_kinds": dict(Counter(r["example_kind"] for r in all_rows)),
        "labels": dict(Counter(label for r in all_rows for a, b, label in r["entities"])),
        "quantity_signals": len(signals),
        "prefix_groups": len(prefix_groups),
        "risk_pairs": len(risks),
        "traceable_internal": len(all_rows),
        "confirmed_authentic_v1_links": 0,
        "human_audio": 0,
        "external_test": 0,
    }
    dump(out / MANIFEST / "coverage.json", counts)
    dump(
        out / MANIFEST / "candidate.json",
        {
            "candidate_version": "2.0.0-rc.1",
            "active": False,
            "base_commit": BASE,
            "families": list(FAMILIES),
            "schema": "homex-corpus-candidate-2.0",
            "nlp_api_schema_version": "1.0",
            "ner_labels_path": "data/manifests/prf04_labels.json",
            "human_gold": False,
            "private_sources": "Separate private bundle; no authentic commercial contents in Git.",
        },
    )
    dump(
        out / MANIFEST / "tooling_sha256.json",
        {
            str(p.relative_to(root)): digest(p.read_bytes())
            for p in sorted(
                list((root / "training/corpus_v2").glob("*.py"))
                + list((root / "training/corpus_v2").glob("*.json"))
                + [root / "tests/training/test_corpus_v2.py"]
            )
        },
    )
    refresh_hashes(out)
    print(json.dumps(counts, ensure_ascii=False, sort_keys=True))


def refresh_hashes(out):
    hashes = {
        str(p.relative_to(out)): digest(p.read_bytes())
        for p in sorted(out.rglob("*"))
        if p.is_file() and p.name != "sha256.json"
    }
    dump(out / MANIFEST / "sha256.json", hashes)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT)
    args = parser.parse_args()
    build(out=args.output)


if __name__ == "__main__":
    main()
