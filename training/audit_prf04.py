"""Inventario reproducible; no certifica revisión humana ni transforma preanotación en gold."""

import argparse
import json
from collections import Counter, defaultdict
from hashlib import sha256
from pathlib import Path

FAMILIAS = ("muebles_pedido", "sillas", "pisos_flotantes", "otros_productos")


def auditar(root=Path("data")):
    fuentes, errores = {}, []
    ids, textos, grupos = set(), {}, defaultdict(set)
    for familia in FAMILIAS:
        path = root / "corpus" / f"{familia}.jsonl"
        rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
        for i, row in enumerate(rows, 1):

            def error(codigo):
                errores.append({"fuente": familia, "linea": i, "codigo": codigo})

            identifier, text = row.get("id"), row.get("text", "")
            if identifier in ids:
                error("ID_DUPLICADO")
            ids.add(identifier)
            digest = sha256(text.encode()).hexdigest()
            if row.get("text_sha256") != digest:
                error("HASH_TEXTO")
            if row.get("category") != familia:
                error("FAMILIA")
            if row.get("split") not in {"train", "dev", "test"}:
                error("SPLIT")
            if text in textos:
                error("TEXTO_DUPLICADO")
            textos[text] = identifier
            grupos[row.get("family_id")].add(row.get("split"))
            if row.get("metadata", {}).get("moneda") not in {"BOB", "USD"}:
                error("MONEDA")
            anterior = 0
            for start, end, label in sorted(row.get("entities", [])):
                if not (type(start) is int and type(end) is int and 0 <= start < end <= len(text)):
                    error("SPAN_INVALIDO")
                if start < anterior:
                    error("SPAN_CRUZADO")
                anterior = end
                if not isinstance(label, str) or not label:
                    error("ETIQUETA")
        fuentes[familia] = {
            "registros": len(rows),
            "sha256": sha256(path.read_bytes()).hexdigest(),
            "origen": dict(Counter(r.get("origin") for r in rows)),
            "calidad": dict(Counter(r.get("metadata", {}).get("calidad") for r in rows)),
            "splits": dict(Counter(r.get("split") for r in rows)),
            "con_expected": sum("expected" in r for r in rows),
        }
    for grupo, splits in grupos.items():
        if len(splits) > 1:
            errores.append({"grupo": grupo, "codigo": "FUGA_ENTRE_PARTICIONES"})
    previas = []
    for path in sorted(root.rglob("*.jsonl")):
        if path.parent.name in {"corpus", "expected"}:
            continue
        rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
        faltantes = [i for i, r in enumerate(rows, 1) if r.get("text") not in textos]
        previas.append(
            {
                "ruta": str(path),
                "sha256": sha256(path.read_bytes()).hexdigest(),
                "registros": len(rows),
                "coincidencias_textuales": len(rows) - len(faltantes),
                "lineas_sin_coincidencia": faltantes,
            }
        )
    return {
        "formato": "PRF04_INVENTARIO_1",
        "fuentes": fuentes,
        "fuentes_anteriores": previas,
        "errores_formales": errores,
        "gates_pendientes": [
            "Reconciliación y revisión humana de fuentes anteriores",
            "Expected estructurados revisados por ejemplo",
            "Muestras reales autorizadas y revisadas",
            "Auditoría semántica de etiquetas y paráfrasis",
        ],
        "permite_eliminar_fuentes_anteriores": False,
        "permite_promover_modelo": False,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = auditar()
    serialized = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(serialized)
    else:
        print(serialized, end="")
    return int(bool(report["errores_formales"]))


if __name__ == "__main__":
    raise SystemExit(main())
