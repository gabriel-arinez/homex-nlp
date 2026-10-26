"""Reconstruct rc.2 from immutable rc.1, historical sources and explicit new scenarios."""

import argparse
import copy
import hashlib
import json
import re
import shutil
from collections import Counter, defaultdict
from pathlib import Path

from training.corpus_v2.build import dump, jsonl, read, table
from training.corpus_v2_rc2.grouping import POLICY, Union, old_graph, pair_risks

DEFAULT = Path("data/candidates/corpus_v2_rc2")
RC1 = Path("data/candidates/corpus_v2_rc1")
FAMILIES = ("muebles_pedido", "sillas", "pisos_flotantes", "otros_productos")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def rc1_records():
    rows = [
        r
        for folder in ("04_CORPUS_DOCUMENTAL_V2", "05_CORPUS_ORAL_V2")
        for p in sorted((RC1 / folder).glob("*.jsonl"))
        for r in read(p)
    ]
    refs = {
        r["id"]: r for p in (RC1 / "06_EXPECTED_ESTRUCTURADOS_V2").glob("*.jsonl") for r in read(p)
    }
    return rows, refs


def render(recipe):
    recipe = copy.deepcopy(recipe)
    marked = recipe["annotated"]
    text = ""
    entities = []
    cursor = 0
    for m in re.finditer(r"\[\[([A-Z_]+)\|(.+?)\]\]", marked):
        text += marked[cursor : m.start()]
        a = len(text)
        text += m[2]
        entities.append([a, len(text), m[1]])
        cursor = m.end()
    text += marked[cursor:]
    ref = recipe["expected"]
    facts = []
    for assertion in recipe["assertions"]:
        literal = assertion["literal"]
        pattern = (
            r"(?<![\d.,])" + re.escape(literal) + r"(?!\d|[.,]\d)"
            if re.fullmatch(r"\d[\d.,]*", literal)
            else re.escape(literal)
        )
        matches = list(re.finditer(pattern, text))
        m = matches[assertion.get("occurrence", 0)]
        facts.append(
            {k: v for k, v in assertion.items() if k not in {"literal", "occurrence"}}
            | {"evidence": {"start": m.start(), "end": m.end(), "text": literal}}
        )
    row = {
        k: recipe[k]
        for k in (
            "id",
            "source_case_id",
            "scenario_family_id",
            "paraphrase_group_id",
            "template_id",
            "category",
            "requested_split",
            "style",
            "phenomena",
            "example_kind",
            "status",
            "origin",
            "independence",
        )
    }
    row.update(
        text=text,
        text_sha256=sha(text.encode()),
        entities=entities,
        supervised=True,
        human_reviewed=False,
        source_ref={
            "kind": "RECETA_SINTETICA",
            "path": "training/corpus_v2_rc2/recipes.json",
            "id": recipe["id"],
        },
        reference_quality="TECHNICAL_CODEX_NOT_HUMAN_GOLD",
    )
    if row["category"] == "muebles_pedido":
        ref["especificacion"]["datos_tecnicos"]["descripcion_original"] = text
    ref.update(
        id=row["id"],
        text_sha256=row["text_sha256"],
        facts=facts,
        reference_method="EXPLICIT_AUTHORED_REFERENCE_NOT_FROM_NER",
    )
    return row, ref


def build(out=DEFAULT):
    rows1, refs1 = rc1_records()
    archive = [r for r in rows1 if r.get("v1_id")]
    rows = []
    refs = {}
    for r in rows1:
        if r.get("v1_id"):
            continue
        r = copy.deepcopy(r)
        rid = r["id"]
        base = r.get("parent_id") or rid
        r.update(
            source_case_id="rc1-case-" + base,
            paraphrase_group_id="rc1-case-" + base,
            template_id="rc1-specific-" + base,
            scenario_family_id="rc1-authored-" + r["category"],
            independence="RC1_AUTHORED_NOT_DOCUMENTARY_NO_V1_PARENT",
            previous_split=r["split"],
        )
        if base.startswith("V2-REC-D"):
            n = int(base[-2:])
            r["requested_split"] = "train" if n % 2 else "dev"
        else:
            r["requested_split"] = "train" if int(sha(base.encode())[:8], 16) % 3 else "dev"
        rows.append(r)
        refs[rid] = copy.deepcopy(refs1[rid])
    for recipe in read_recipes():
        row, ref = render(recipe)
        rows.append(row)
        refs[row["id"]] = ref
    risks = pair_risks(rows, refs)
    groups = Union([r["id"] for r in rows])
    for risk in risks:
        if risk["severity"] == "HIGH":
            groups.join(risk["a"], risk["b"])
    assignments = {}
    members = defaultdict(list)
    for r in rows:
        members[groups.find(r["id"])].append(r)
    for group, items in sorted(members.items()):
        # Authored groups have a predeclared allocation; merged groups use deterministic oldest ID.
        chosen = sorted(items, key=lambda r: r["id"])[0]["requested_split"]
        assignments[group] = chosen
        for r in items:
            r.update(
                split=chosen,
                collection="development_" + chosen,
                leakage_group=group,
                human_gold=False,
            )
    by_id = {r["id"]: r for r in rows}
    for risk in risks:
        risk["cross_partition"] = by_id[risk["a"]]["split"] != by_id[risk["b"]]["split"]
    for family in FAMILIES:
        for split in ("train", "dev"):
            selected = [r for r in rows if r["category"] == family and r["split"] == split]
            jsonl(out / "development_v2" / split / f"{family}.jsonl", selected)
            jsonl(out / "expected" / split / f"{family}.jsonl", [refs[r["id"]] for r in selected])
        for folder in ("corpus", "expected", "splits"):
            src = (
                Path("data")
                / folder
                / (f"{family}.json" if folder == "splits" else f"{family}.jsonl")
            )
            dest = out / "archive_v1" / folder / src.name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dest)
    jsonl(
        out / "archive_v1/rc1_technical_sidecar.jsonl",
        [
            {
                "id": r["id"],
                "v1_id": r["v1_id"],
                "historical_split": next(
                    x["split"]
                    for x in read(Path("data/corpus") / f"{r['category']}.jsonl")
                    if x["id"] == r["v1_id"]
                ),
                "rc1_record": r,
                "rc1_expected": refs1[r["id"]],
                "human_gold": False,
            }
            for r in archive
        ],
    )
    jsonl(out / "internal_holdout_v2/records.jsonl", [])
    jsonl(out / "external_human_gold/records.jsonl", [])
    original = [r for family in FAMILIES for r in read(Path("data/corpus") / f"{family}.jsonl")]
    graph = old_graph(original)
    dump(out / "analysis/rc1_graph.json", graph)
    dump(
        out / "analysis/rc2_groups.json",
        [
            {
                "group": g,
                "split": assignments[g],
                "ids": [r["id"] for r in rs],
                "source_cases": sorted({r["source_case_id"] for r in rs}),
                "policy": POLICY,
            }
            for g, rs in sorted(members.items())
        ],
    )
    dump(out / "analysis/pair_risks.json", risks)
    # Compare every development record against the historical archive with all strong detectors.
    archive_compare = []
    from training.corpus_v2_rc2.grouping import normalized, semantic_key

    archive_norm = {r["id"]: normalized(r["text"]) for r in archive}
    archive_semantics = {r["id"]: semantic_key(refs1[r["id"]]) for r in archive}
    archive_grams = {
        r["id"]: {
            tuple(archive_norm[r["id"]].split()[i : i + 4])
            for i in range(len(archive_norm[r["id"]].split()) - 3)
        }
        for r in archive
    }
    for r in rows:
        words = set(normalized(r["text"]).split())
        best = (0, None)
        norm = normalized(r["text"])
        tokens = norm.split()
        grams = {tuple(tokens[i : i + 4]) for i in range(len(tokens) - 3)}
        semkey = semantic_key(refs[r["id"]])
        for a in archive:
            other = set(archive_norm[a["id"]].split())
            score = len(words & other) / len(words | other)
            if score > best[0]:
                best = (score, a["id"])
            other_grams = archive_grams[a["id"]]
            near = len(grams & other_grams) / len(grams | other_grams) if grams | other_grams else 0
            if (
                r["text"] == a["text"]
                or norm == archive_norm[a["id"]]
                or semkey == archive_semantics[a["id"]]
                or near >= 0.50
            ):
                archive_compare.append(
                    {
                        "development_id": r["id"],
                        "archive_id": a["id"],
                        "severity": "HIGH",
                        "decision": "PENDING",
                        "reason": "exact/number-template/structured-claims identity",
                    }
                )
        archive_compare.append(
            {
                "development_id": r["id"],
                "archive_id": best[1],
                "word_jaccard": round(best[0], 6),
                "severity": "LOW",
                "decision": "DOMAIN_VOCABULARY_NOT_SOURCE_IDENTITY",
                "reason": "No explicit V1 parent or matching full fingerprint; common terminology alone is not same commercial case.",
            }
        )
    dump(out / "analysis/archive_risks.json", archive_compare)
    manifest = {
        "version": "2.0.0-rc.2",
        "base_commit": "0154ecba0a53d1a7f3cca4ef10a6cf78cc2ef317",
        "active": False,
        "policy": POLICY,
        "seed": "20261025",
        "allocation": "predeclared scenario allocation; connected group oldest ID wins",
        "collections": {
            "archive_v1": 675,
            "development_train": sum(r["split"] == "train" for r in rows),
            "development_dev": sum(r["split"] == "dev" for r in rows),
            "internal_holdout_v2": 0,
            "external_human_gold": 0,
        },
        "human_gold": "NO",
        "external_voice_benchmark": "NO",
        "families": list(FAMILIES),
        "labels": json.loads(Path("data/manifests/prf04_labels.json").read_text())["labels"],
    }
    dump(out / "manifest.json", manifest)
    coverage = []
    for split in ("train", "dev"):
        for family in FAMILIES:
            selected = [r for r in rows if r["split"] == split and r["category"] == family]
            for label in manifest["labels"]:
                carrying = [r for r in selected if any(e[2] == label for e in r["entities"])]
                coverage.append(
                    {
                        "split": split,
                        "family": family,
                        "label": label,
                        "examples": len(carrying),
                        "spans": sum(e[2] == label for r in carrying for e in r["entities"]),
                        "source_cases": len({r["source_case_id"] for r in carrying}),
                        "effective_groups": len({r["leakage_group"] for r in carrying}),
                        "styles": dict(Counter(r["style"] for r in carrying)),
                    }
                )
    table(out / "coverage_by_label_family.csv", coverage)
    table(
        out / "traceability.csv",
        [
            {
                "id": r["id"],
                "source_case_id": r["source_case_id"],
                "scenario_family_id": r["scenario_family_id"],
                "paraphrase_group_id": r["paraphrase_group_id"],
                "template_id": r["template_id"],
                "group": r["leakage_group"],
                "family": r["category"],
                "style": r["style"],
                "collection": r["collection"],
                "labels": sorted({e[2] for e in r["entities"]}),
                "source_ref": r["source_ref"],
                "text_sha256": r["text_sha256"],
            }
            for r in rows
        ],
    )
    migration = []
    for r in rows1:
        after = by_id.get(r["id"])
        migration.append(
            {
                "id": r["id"],
                "operation": "ARCHIVE_V1_RETROSPECTIVE" if r.get("v1_id") else "RETAIN_AND_REGROUP",
                "before_split": r["split"],
                "after_collection": "archive_v1" if r.get("v1_id") else after["collection"],
                "text_unchanged": True,
                "reason": "Retrospective historical source"
                if r.get("v1_id")
                else "Specific case graph replaces broad commercial-family union",
            }
        )
    for r in rows:
        if r["id"] not in refs1:
            migration.append(
                {
                    "id": r["id"],
                    "operation": "NEW_SCENARIO",
                    "before_split": None,
                    "after_collection": r["collection"],
                    "text_unchanged": None,
                    "reason": "Verified label/family diversity gaps in rc1; distinct authored design task",
                }
            )
    table(out / "migration_rc1_rc2.csv", migration)
    protected = json.loads(Path("training/corpus_v2_rc2/protected_baseline.json").read_text())
    dump(out / "protected_sha256.json", protected)
    from training.corpus_v2_rc2.review import make_kit

    make_kit(out, rows, refs, rows1, refs1)
    write_reports(out, manifest, rows)
    from training.corpus_v2_rc2.reports import write

    write(out, rows, refs)
    refresh(out)
    print(json.dumps(manifest["collections"], sort_keys=True))


def read_recipes():
    return json.loads(Path("training/corpus_v2_rc2/recipes.json").read_text())


def write_reports(out, manifest, rows):
    (out / "README.md").write_text(
        """# HOMEX Corpus 2.0.0-rc.2 — candidato experimental pasivo\n\nArchivo histórico y desarrollo separados. No es gold humano ni benchmark de voz.\n\nReconstruir: `uv run --locked --extra dev python -m training.corpus_v2_rc2.build --output /tmp/homex-rc2-a`.\nValidar: `uv run --locked --extra dev python -m training.corpus_v2_rc2.validate /tmp/homex-rc2-a`.\nGate CI: `uv run --locked --extra dev python -m training.corpus_v2_rc2.ci_gate --evidence /tmp/homex-rc2-ci`.\nNo entrenar ni copiar sobre las rutas V1. Desactivar el candidato constituye rollback; V1 no cambia.\n\n## Política de independencia\n\n`source_case_id` = diseño comercial concreto; `paraphrase_group_id` = transformaciones del caso;\n`template_id` = plantilla específica, no familia de mobiliario; `scenario_family_id` = contexto descriptivo, solo alerta.\nUna coincidencia de fuente/caso/paráfrasis/plantilla, huella con números/unidades/acentos normalizados,\no referencia estructurada equivalente impone una partición. Prefijos y vocabulario común solos no.\nLos pares de lenguaje parcial se reportan como alertas de baja confianza con decisión explícita;\nno se proclama independencia universal frente a paráfrasis que estos detectores no reconozcan.\n\nLos 675 V1 se conservan byte por byte con sus splits 483/94/98 en archive_v1; sidecar rc1 separado.\nSe retienen 52 casos rc1 sin padres V1 explícitos; su independencia es técnica, no certificación humana.\nNuevas recetas cubren únicamente brechas comprobadas de etiquetas y tareas distintas.\nNo se reserva holdout sintético: escenarios escasos se destinan a train/dev.\nexternal_human_gold tiene cero muestras; adquirir fuentes y hablantes consentidos independientes.\n\n## Límites\n\nTamaño efectivo por etiqueta se mide en grupos, no en número de paráfrasis. EXPERIMENTAL_READY\nsolo significa que puede diseñarse un experimento offline limitado; no precisión predictiva,\nhomologación comercial ni permiso para entrenar en este encargo.\nEstados separados: integridad de formato, coherencia técnica inferida y revisión humana independiente.\n\nLas 24 etiquetas permanecen intactas. APOYABRAZOS/CABECERA/ERGONOMIA/SOPORTE_LUMBAR se aplican\na sillas; CLASE_RESISTENCIA a pisos. No se obliga a esas etiquetas en familias inadecuadas.\nCantidad interna/capacidad siguen como relaciones, nunca nuevas clases NER. Precios se validan\ncon Decimal; moneda de Condiciones no se inventa; no convertir precios ni metros a barras.\nLos 120 ítems privados y cuatro referencias parciales no entran en supervisión.\n\n## Revisión real\n\nreview/kit.csv y kit.jsonl permiten adjudicación por campo con texto sintético, evidencia,\nalternativa, prioridad y campos vacíos de revisor/fecha/decisión. Usar el importador explícito;\nningún generador asigna HUMAN_REVIEWED o GOLD_ELIGIBLE. Véase review/GUIDE.md.\n"""
    )
    dump(
        out / "collection_summary.json",
        {
            "collections": manifest["collections"],
            "families": {
                s: dict(Counter(r["category"] for r in rows if r["split"] == s))
                for s in ("train", "dev")
            },
            "styles": {
                s: dict(Counter(r["style"] for r in rows if r["split"] == s))
                for s in ("train", "dev")
            },
            "kinds": dict(Counter(r["example_kind"] for r in rows)),
        },
    )


def refresh(out):
    dump(
        out / "sha256.json",
        {
            str(p.relative_to(out)): sha(p.read_bytes())
            for p in sorted(out.rglob("*"))
            if p.is_file() and p.name != "sha256.json"
        },
    )


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--output", type=Path, default=DEFAULT)
    a = p.parse_args()
    build(a.output)


if __name__ == "__main__":
    main()
