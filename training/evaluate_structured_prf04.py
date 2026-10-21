"""Evalúa campos completos, asociaciones y JSON de A/B/C contra referencias técnicas."""

import argparse
import json
from decimal import Decimal
from pathlib import Path

from homex_nlp.contracts import ExtractionRequest, ExtractionResult
from homex_nlp.engine import RulesEngine
from homex_nlp.rules import decimal_from_text
from training.corpus import read_jsonl
from training.experimental_engines import HybridExperimentalEngine, NerExperimentalEngine


def canonical(value):
    if isinstance(value, dict):
        return {k: canonical(v) for k, v in value.items()}
    if isinstance(value, list):
        return [canonical(v) for v in value]
    if isinstance(value, str):
        try:
            return format(Decimal(value).normalize(), "f")
        except Exception:
            return " ".join(value.casefold().split())
    return value


def structured(result, moneda_contexto):
    item = result.item_proposal
    if item is None:
        return None
    components = {
        c.component_id: {"uid": f"c{i}", "nombre": c.name} for i, c in enumerate(item.components, 1)
    }
    generales = {}
    dimensions = {
        d.axis: {"valor": d.value, "unidad": d.unit}
        for d in item.dimensions
        if d.axis and d.unit and not d.component_ref
    }
    if dimensions:
        generales["dimensiones"] = dimensions
    for c in result.candidates:
        if (
            c.decision == "ACCEPTED"
            and c.component_ref in components
            and c.label in {"MATERIAL", "COLOR", "ACABADO"}
        ):
            components[c.component_ref][c.label.lower()] = c.text
    for thickness in item.thicknesses:
        if thickness.component_ref in components:
            components[thickness.component_ref]["espesor"] = thickness.original_text
    units = [
        c.normalized_value
        for c in result.candidates
        if c.label == "UNIDAD_MEDIDA"
        and c.decision == "ACCEPTED"
        and isinstance(c.normalized_value, str)
    ]
    totals = [
        c for c in result.candidates if c.label == "PRECIO_TOTAL" and c.decision == "ACCEPTED"
    ]
    total = None
    if len(totals) == 1:
        import re

        match = re.search(r"[\d.,]+", totals[0].text)
        total = str(decimal_from_text(match.group())) if match else None
    if item.price and item.price.mode == "TOTAL_NEGOCIADO":
        total = item.price.line_total
    return {
        "comercial": {
            "nombre": item.name,
            "cantidad": str(item.quantity) if item.quantity else None,
            "unidad_codigo": units[0] if units else None,
            "precio_unitario": item.price.unit_price_input
            if item.price and item.price.mode == "PRECIO_UNITARIO"
            else None,
            "precio_total_explicito": total,
            "moneda_codigo": moneda_contexto,
        },
        "especificacion": {
            "datos_tecnicos": {
                "descripcion_original": result.text_original,
                "componentes": list(components.values()),
                "conjuntos": [],
                "accesorios": [a.name for a in item.accessories],
                "caracteristicas_generales": generales,
            }
        },
    }


def reference(target):
    target = json.loads(json.dumps(target))
    for i, c in enumerate(target["especificacion"]["datos_tecnicos"]["componentes"], 1):
        c["uid"] = f"c{i}"
    return target


def relations(data):
    return (
        {
            (c["nombre"], field, value)
            for c in data["especificacion"]["datos_tecnicos"]["componentes"]
            for field, value in c.items()
            if field not in {"uid", "nombre"} and isinstance(value, str)
        }
        if data
        else set()
    )


def evaluate(model, output):
    ner = NerExperimentalEngine(model)
    engines = {
        "A_RULES_ONLY": RulesEngine(),
        "B_NER_ASSEMBLER": ner,
        "C_HYBRID_EXPERIMENTAL": HybridExperimentalEngine(ner),
    }
    rows = [
        r for _, r in read_jsonl(Path("data/corpus/muebles_pedido.jsonl")) if r["split"] == "dev"
    ]
    expected = {
        r["id"]: r["expected"] for _, r in read_jsonl(Path("data/expected/muebles_pedido.jsonl"))
    }
    results = {}
    for name, engine in engines.items():
        scores = {
            "contrato_valido": 0,
            "json_exacto": 0,
            "cantidad_exacta": 0,
            "unitario_exacto": 0,
            "relaciones_tp": 0,
            "relaciones_fp": 0,
            "relaciones_fn": 0,
        }
        for row in rows:
            result = engine.extract(
                ExtractionRequest(
                    request_id=row["id"],
                    text=row["text"],
                    currency_context=row["metadata"]["moneda"],
                )
            )
            ExtractionResult.model_validate_json(result.model_dump_json())
            scores["contrato_valido"] += 1
            actual, wanted = (
                canonical(structured(result, row["metadata"]["moneda"])),
                canonical(reference(expected[row["id"]])),
            )
            if actual:
                scores["json_exacto"] += actual == wanted
                scores["cantidad_exacta"] += (
                    actual["comercial"]["cantidad"] == wanted["comercial"]["cantidad"]
                )
                scores["unitario_exacto"] += (
                    actual["comercial"]["precio_unitario"] == wanted["comercial"]["precio_unitario"]
                )
            a, b = relations(wanted), relations(actual)
            scores["relaciones_tp"] += len(a & b)
            scores["relaciones_fp"] += len(b - a)
            scores["relaciones_fn"] += len(a - b)
        tp, fp, fn = (scores[k] for k in ["relaciones_tp", "relaciones_fp", "relaciones_fn"])
        p, r = tp / (tp + fp) if tp + fp else 0, tp / (tp + fn) if tp + fn else 0
        results[name] = {
            "conteos": scores,
            "documentos": len(rows),
            "relaciones": {"precision": p, "recall": r, "f1": 2 * p * r / (p + r) if p + r else 0},
        }
    output.write_text(
        json.dumps(
            {
                "particion": "dev",
                "fuente": "REFERENCIAS_TECNICAS_DESDE_ANOTACIONES_NO_GOLD_HUMANO",
                "variantes": results,
                "promovido": False,
                "decision": "Mantener A; B/C requieren revisión de dominio, negativos/habla natural y productividad humana.",
                "limitaciones": [
                    "No equivale a validación del proyector backend sobre todo el corpus.",
                    "UID se normaliza para comparar contenido; no se infieren asociaciones por índice.",
                    "No ajustar con test; esta evaluación estructurada usa exclusivamente dev.",
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("model", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    evaluate(args.model, args.output)
