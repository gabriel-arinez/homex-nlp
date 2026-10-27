"""Referencias estructuradas desde anotaciones fuente, independientes del motor operativo.

La revisión técnica no acredita validación comercial humana ni calidad de ASR.
"""

import json
import re
from pathlib import Path

from homex_nlp.rules import decimal_from_text
from training.corpus import read_jsonl


def expected(row):
    text = row["text"]
    spans = [(a, b, label, text[a:b]) for a, b, label in row["entities"]]
    valores = {}
    for _, _, label, literal in spans:
        valores.setdefault(label, []).append(literal)

    def numero(label):
        for literal in valores.get(label, []):
            match = re.search(r"[\d.,]+", literal)
            valor = decimal_from_text(match.group()) if match else None
            if valor is not None:
                return str(valor)
        return None

    comercial = {
        "nombre": valores.get("PRODUCTO", [None])[0],
        "cantidad": numero("CANTIDAD"),
        "unidad_codigo": row["metadata"].get("unidad_comercial"),
        "precio_unitario": numero("PRECIO_UNITARIO"),
        "precio_total_explicito": numero("PRECIO_TOTAL"),
        "moneda_codigo": row["metadata"].get("moneda"),
    }
    datos = {
        "descripcion_original": text,
        "componentes": [],
        "conjuntos": [],
        "accesorios": valores.get("ACCESORIO", []),
        "caracteristicas_generales": {},
    }
    componentes = [(a, b, literal) for a, b, label, literal in spans if label == "COMPONENTE"]
    for indice, (inicio, fin, nombre) in enumerate(componentes):
        limite = componentes[indice + 1][0] if indice + 1 < len(componentes) else len(text)
        # Las anotaciones consecutivas de componente delimitan cada ámbito explícito.
        componente = {"uid": f"{row['id']}-c{indice + 1}", "nombre": nombre}
        for a, b, label, literal in spans:
            if fin <= a < limite and label in {"MATERIAL", "ESPESOR", "COLOR", "ACABADO"}:
                componente[label.lower()] = literal
        datos["componentes"].append(componente)
    dimensiones = {}
    for _, _, label, literal in spans:
        if label in {"ALTO", "ANCHO", "PROFUNDIDAD", "LARGO", "DIAMETRO"}:
            match = re.fullmatch(r"\s*([\d.,]+)\s*(mm|cm|m)\s*", literal, re.I)
            if match:
                dimensiones[label.lower()] = {
                    "valor": str(decimal_from_text(match[1])),
                    "unidad": match[2].lower(),
                }
    if dimensiones:
        datos["caracteristicas_generales"]["dimensiones"] = dimensiones
    especificacion = (
        {"datos_tecnicos": datos}
        if row["category"] == "muebles_pedido"
        else {"atributos_catalogo": valores}
    )
    return {
        "id": row["id"],
        "text_sha256": row["text_sha256"],
        "revision": "TECNICA_DESDE_ANOTACIONES_NO_GOLD_HUMANO",
        "expected": {"comercial": comercial, "especificacion": especificacion},
    }


def main():
    destination = Path("data/expected")
    destination.mkdir(exist_ok=True)
    for source in Path("data/corpus").glob("*.jsonl"):
        rows = [expected(row) for _, row in read_jsonl(source)]
        (destination / source.name).write_text(
            "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows)
        )


if __name__ == "__main__":
    main()
