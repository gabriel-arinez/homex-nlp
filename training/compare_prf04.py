"""Comparación offline de evidencias A/B/C; no habilita un motor en producción."""

import argparse
import json
from collections import defaultdict
from pathlib import Path

import spacy

from homex_nlp.contracts import ExtractionRequest
from homex_nlp.engine import RulesEngine
from training.corpus import read_jsonl


def metricas(gold, predicted):
    labels = sorted({span[2] for docs in (gold, predicted) for spans in docs for span in spans})
    por_etiqueta = {}
    totals = [0, 0, 0]
    for label in labels:
        tp = fp = fn = 0
        for wanted, actual in zip(gold, predicted):
            a, b = {s for s in wanted if s[2] == label}, {s for s in actual if s[2] == label}
            tp += len(a & b)
            fp += len(b - a)
            fn += len(a - b)
        p, r = tp / (tp + fp) if tp + fp else 0, tp / (tp + fn) if tp + fn else 0
        por_etiqueta[label] = {"p": p, "r": r, "f": 2 * p * r / (p + r) if p + r else 0}
        totals = [a + b for a, b in zip(totals, [tp, fp, fn])]
    tp, fp, fn = totals
    p, r = tp / (tp + fp) if tp + fp else 0, tp / (tp + fn) if tp + fn else 0
    return {
        "micro": {"p": p, "r": r, "f": 2 * p * r / (p + r) if p + r else 0},
        "macro": {
            k: sum(v[k] for v in por_etiqueta.values()) / len(labels) if labels else 0
            for k in ("p", "r", "f")
        },
        "por_etiqueta": por_etiqueta,
    }


def comparar(model, output):
    nlp = spacy.load(model)
    rows = [
        r for _, r in read_jsonl(Path("data/corpus/muebles_pedido.jsonl")) if r["split"] == "dev"
    ]
    gold, variants = [], defaultdict(list)
    quantity_correct = price_correct = structural = 0
    for row in rows:
        gold.append({tuple(e) for e in row["entities"]})
        result = RulesEngine().extract(
            ExtractionRequest(
                request_id=row["id"], text=row["text"], currency_context=row["metadata"]["moneda"]
            )
        )
        actual = set()
        for c in result.candidates:
            if c.decision != "ACCEPTED":
                continue
            label = c.label
            if label == "PRECIO" and result.item_proposal and result.item_proposal.price:
                label = (
                    "PRECIO_UNITARIO"
                    if result.item_proposal.price.mode == "PRECIO_UNITARIO"
                    else "PRECIO_TOTAL"
                )
            actual.add((c.start, c.end, label))
        ner = {(e.start_char, e.end_char, e.label_) for e in nlp(row["text"]).ents}
        variants["A_RULES_ONLY"].append(actual)
        variants["B_NER"].append(ner)
        # Unión de evidencia deduplicada; los conflictos se retienen para revisión offline.
        variants["C_UNION_EXPERIMENTAL"].append(actual | ner)
        target = json.loads(
            next(
                line
                for line in Path("data/expected/muebles_pedido.jsonl").read_text().splitlines()
                if json.loads(line)["id"] == row["id"]
            )
        )["expected"]["comercial"]
        item = result.item_proposal
        quantity_correct += bool(item and str(item.quantity) == target["cantidad"])
        price_correct += bool(
            item
            and item.price
            and item.price.mode == "PRECIO_UNITARIO"
            and float(item.price.unit_price_input) == float(target["precio_unitario"] or 0)
        )
        structural += bool(result.model_validate_json(result.model_dump_json()))
    report = {
        "particion": "dev",
        "documentos": len(rows),
        "referencias": "ANOTACIONES_FUENTE_AUTORIZADA_NO_GOLD_HUMANO",
        "variantes_evidencia": {name: metricas(gold, pred) for name, pred in variants.items()},
        "A_campos_completos": {
            "cantidad": quantity_correct / len(rows),
            "precio_unitario": price_correct / len(rows),
            "contrato_valido": structural / len(rows),
        },
        "promocion": False,
        "operativo": "A_RULES_ONLY",
        "pendiente": [
            "Comparación JSON/relaciones de B y C con referencias de dominio revisadas",
            "Productividad y correcciones humanas",
            "WER de vendedores autorizado",
        ],
        "nota": "C es sólo una unión experimental de evidencias; no es un ensamblador híbrido promovible.",
    }
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("model", type=Path)
    p.add_argument("output", type=Path)
    args = p.parse_args()
    comparar(args.model, args.output)


if __name__ == "__main__":
    main()
