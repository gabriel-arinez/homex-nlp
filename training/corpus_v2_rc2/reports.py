"""Deterministic comparison and public gate definitions, separate from run evidence."""

import json


def write(out, rows, refs):
    graph = json.loads((out / "analysis/rc1_graph.json").read_text())
    groups = json.loads((out / "analysis/rc2_groups.json").read_text())
    summary = json.loads((out / "collection_summary.json").read_text())
    progress = json.loads((out / "review/progress.json").read_text())
    lines = [
        "# rc.1 → rc.2 — análisis y límites",
        "",
        "La auditoría independiente ratificó integridad de rc.1 y bloqueó su aptitud para NER general. Este correctivo conserva esos resultados como históricos, sin atribuirlos a las nuevas ejecuciones.",
        "",
        "## Archivo y particiones",
        "",
        "| Colección | rc.1 | rc.2 |",
        "|---|---:|---:|",
        "| Archivo V1 retrospectivo separado | 0 | 675 |",
        f"| Desarrollo train | 38 | {summary['collections']['development_train']} |",
        f"| Desarrollo dev | 12 | {summary['collections']['development_dev']} |",
        "| Test retrospectivo mezclado | 677 | 0 |",
        "| Holdout interno limpio | 0 | 0 |",
        "| Gold humano externo | 0 | 0 |",
        "",
        "El archivo V1 conserva los splits originales 483/94/98 y no es un benchmark limpio. Los 52 sintéticos rc.1 se auditan y conservan con nuevas claves específicas de caso; se añaden 14 diseños para cerrar brechas. No se copian documentos privados ni se derivan ejemplos de registros V1 reservados.",
        "",
        f"El grafo rc.1 colapsó en {graph['components']} componente de tamaño {graph['component_sizes']}; uniones que realmente redujeron componentes: {graph['actual_merges_by_signal']}. Las 64 uniones por prefijo actuaron como puentes entre grupos amplios. `family_id` es una familia generativa, no una fuente comercial independiente. Proforma sintética tampoco acredita documento auténtico.",
        "",
        f"En desarrollo rc.2 hay {len(groups)} grupos efectivos para {len(rows)} registros. Se conservan fuertes fuente/caso, paráfrasis, plantilla específica, huella con números/unidades/acentos normalizados, equivalencia de referencias y near-duplicates. Familia comercial y frase genérica son alertas; no se elimina el detector.",
        "",
        "## Cobertura por etiqueta y tamaño efectivo",
        "",
        "| Etiqueta | Train ejemplos / spans / casos / grupos | Dev ejemplos / spans / casos / grupos |",
        "|---|---|---|",
    ]
    labels = json.loads((out / "manifest.json").read_text())["labels"]
    for label in labels:
        values = []
        for split in ("train", "dev"):
            rs = [
                r for r in rows if r["split"] == split and any(e[2] == label for e in r["entities"])
            ]
            values.append(
                f"{len(rs)} / {sum(e[2] == label for r in rs for e in r['entities'])} / {len({r['source_case_id'] for r in rs})} / {len({r['leakage_group'] for r in rs})}"
            )
        lines.append("| " + label + " | " + " | ".join(values) + " |")
    lines += [
        "",
        "Las cuatro familias aparecen en train y dev (ver collection_summary.json); las tablas CSV dan cada combinación etiqueta/familia, modalidad y casos. Los mínimos de 2 grupos/casos train y 1 dev se comprueban a nivel de etiqueta aplicable, no se exige cada etiqueta en cada familia. CABECERA y SOPORTE_LUMBAR se contextualizan en sillas; CLASE_RESISTENCIA en pisos. Cero presencia no se presenta como prueba de inaplicabilidad universal: la matriz es descriptiva del alcance actual.",
        "",
        "Los mínimos cierran la brecha estructural de rc.1; no bastan para sostener potencia estadística ni generalización. El tamaño sigue siendo pequeño y sesgado por autor sintético. EXPERIMENTAL_READY significa aptitud para un piloto offline limitado con resultados exploratorios, nunca para comparar precisión de campo ni promover producción.",
        "",
        "## Revisión técnica y humana",
        "",
        f"Auditoría por campo: {progress['populations']}; {progress['fields_pending']} campos pendientes. Las 375 correcciones y 52 casos rc.1 nuevos se censan; los nuevos se censan; la muestra restante se estratifica por familia/etiqueta, con prioridades por coste de error. No se confunde revisión de Codex con adjudicación humana.",
        "",
        "Cambios semánticos de rc.1 detectados durante el correctivo: el validador de unidad del zócalo activaba un falso positivo ante mención negada de zócalos en un piso. La excepción se limita al producto de piso y no cambia el motor. La referencia nueva con unitario y total idénticos usa la segunda aparición del importe para el total; el texto no se altera. Las referencias de dimensiones locales se comprueban sin convertirlas en dimensiones generales.",
        "",
        "Los originales privados: 111 VERIFICABLE a nivel literal, 8 DUDOSO, 1 INCONSISTENTE; los 120 siguen REQUIERE_REVISION_HUMANA y fuera de supervisión. Las cuatro referencias parciales siguen en cuarentena. No corregir unidades ni importes por intuición.",
        "",
        "## Gates y evidencia de ejecución",
        "",
        "| Gate | Prueba / evidencia reproducible |",
        "|---|---|",
        "| G01 | protected_sha256.json fijado al commit rc.1; validación por hash de V1/runtime/rc.1/contratos |",
        "| G02 | analysis/rc1_graph.json; rc2_groups.json; traceability.csv; pruebas de casos opuestos |",
        "| G03 | cobertura de las cuatro familias y 24 etiquetas por grupos/casos; colección histórica separada |",
        "| G04 | pair_risks.json y archive_risks.json; recomputación independiente en validator; riesgo alto pendiente bloquea |",
        "| G05 | validator por registro, Decimal, offsets y roundtrip DocBin; pruebas de mutación |",
        "| G06 | review/kit.csv, kit.jsonl, technical_audit.jsonl, sample_strata.json; importador y tests sin decisiones humanas reales |",
        "| G07 | escaneo de snapshots, staging/blobs y textos privados en evidencia de publicación fuera de Git |",
        "| G08 | workflow corpus-v2-rc2; runner con bloqueo de entrenamiento y cargas; CI histórico preservado para cambios mixtos |",
        "| G09 | ci_gate compara dos rebuilds limpios con candidato; logs fuera del dataset |",
        "| G10 | rama/PR draft nuevos apilados sobre #20; SHA y ejecución remota efectivos en evidencia del bundle |",
        "",
        "Los resultados PASS/FAIL y URLs reales se guardan en el informe consolidado del bundle y el PR después de las ejecuciones; este documento define el gate sin inventar estado remoto. HUMAN_GOLD=NO y TEST_VOZ_REAL=NO son estados independientes de los gates técnicos.",
        "",
        "## CI sin entrenamiento",
        "",
        "El clasificador mantiene los jobs históricos package y prf04-experiment para cambios de producción o mixtos; los omite solo en cambios exclusivos de las rutas rc.2. Secretos y auditoría de dependencias no se silencian. El workflow de datos ejecuta tests completos, integridad rc.1/V1, validadores rc.2, Ruff/formato, exportación de esquemas, DocBin y determinismo; no utiliza [skip ci].",
        "",
        "El runner enumera comandos permitidos y añade una auditoría de subprocess/os.system y bloqueo de spaCy train/load/initialize/update. Las pruebas demuestran que comandos de entrenamiento y carga/inicialización fallan. No hay pesos nuevos. El clasificador no elimina entrenamiento en PRs de producción; aquí la prohibición se cumple mediante el diff exclusivo verificado antes del push.",
        "",
        "## Trabajo externo preciso",
        "",
        "Un responsable HOMEX debe adjudicar el kit y suministrar el registro privado de revisores/actas; las discrepancias necesitan revisión independiente. Adquirir documentos/audio consentidos de casos y hablantes no derivados de estos diseños para gold externo, definiendo retención y transcripción fiel; no fabricar WER ni métricas predictivas. No activar V2 ni entrenar en este encargo.",
    ]
    (out / "COMPARACION_Y_GATES.md").write_text("\n".join(lines) + "\n")
