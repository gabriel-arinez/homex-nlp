# Directed retake NLP corrections
Objective: preserve literal measurements and safe product/component relations. Branch: fix/directed-retakes-dimensions; baseline: 6731115.
Delivery: single local commit requested; no PR/push or consumer edits. Runner: existing .venv Python/pytest/ruff; unchanged ASR for 15 input captures. Forecast: approximately 400 authored lines, cohesive behavior/tests/docs kept together; no PR strategy needed while PR creation is prohibited.

## Specs
- S1: "**Dimensiones incorrectas:** corregir el falso atributo `1` generado por «una altura de 73 cm» (MP-0026)." Verify literal height73 survives and article is not numeric evidence.
- S2: "**Relaciones entre productos y componentes:** mejorar la interpretación de escritorios y cajoneras separados por comas (MP-0022, MP-0023 y MP-0051), sin fusionar pedidos independientes." Preserve independent quantities, conjunctions and ambiguous product composition.
- S3: "**Dimensiones compuestas:** mejorar la extracción y conservación de medidas como `1,40 m × 70 cm` y `33 × 40 × 63 cm`, evitando inventar ejes, unidades o asociaciones." Preserve full ordered evidence with optional axis and explicitly scoped units/owners under existing schema.
- S4: "**Cantidades y precios:** comprobar los resultados de MP-0050 y MP-0022 utilizando las nuevas grabaciones R2. Mantener las cantidades realmente reconocidas y evitar correcciones artificiales basadas en los guiones."
- S5: "**Otros problemas detectados:** corregir cualquier defecto NLP adicional que esté respaldado por evidencia y pueda resolverse sin comprometer la seguridad comercial." Only reproduced related defects; no speculative scope expansion.
- S6: "Mantener las abstenciones justificadas cuando existan ambigüedades sobre juegos de mesas, casilleros o credenzas. No forzar propuestas cuando la información sea insuficiente." "Mantener el contrato público, el modo `RULES_ONLY` y la compatibilidad con Backend."
- S7: "Ejecutar las pruebas unitarias y de integración del NLP." "Reprocesar los 13 casos R1 y los 2 casos R2 para comparar antes y después." "Ejecutar las regresiones sobre los 120 casos históricos." "Verificar cantidades, precios, dimensiones, componentes, asociaciones y abstenciones, no solamente el estado de las propuestas." "Ejecutar lint, validaciones del paquete y comprobaciones de compatibilidad disponibles."
- S8: "No abrir PR ni modificar Backend o Frontend por ahora." "No alterar los audios originales ni los resultados históricos." "Commit correspondiente con los cambios verificados."

## Tasks
- T1 [S1-S3,S5-S6] inline; verified; RED9/GREEN24 retake probes, corrections/tests/docs; commit HEAD (`fix(nlp): preserve retake dimensions and safe drawer references`). Writer trigger absent: shared implementation surface, no independent parallel units. Risk: item 3 (shared parser/reference helpers used beyond the retakes).
- T2 [S4,S6-S8] inline with delegated verification; verified;15 captures +240 historical inputs,1080 tests/lint/schema/package/consumer PASS; commit HEAD (`fix(nlp): preserve retake dimensions and safe drawer references`). RDD status: disabled globally; no native review. Private evidence under a new evaluaciones directory only.

## Log
- L1 (2026-11-15): Original user request follows verbatim.

# HOMEX — Corrección y mejora del motor NLP

Tu tarea es **corregir y mejorar directamente `homex-nlp`**, utilizando la evidencia obtenida de las 13 regrabaciones R1, las 2 regrabaciones R2 y las evaluaciones históricas.

No necesito otra fase dedicada exclusivamente al diagnóstico. Investiga lo necesario, implementa las mejoras justificadas y comprueba sus resultados.

## 1. Correcciones prioritarias

1. **Dimensiones incorrectas:** corregir el falso atributo `1` generado por «una altura de 73 cm» (MP-0026).
2. **Relaciones entre productos y componentes:** mejorar la interpretación de escritorios y cajoneras separados por comas (MP-0022, MP-0023 y MP-0051), sin fusionar pedidos independientes.
3. **Dimensiones compuestas:** mejorar la extracción y conservación de medidas como `1,40 m × 70 cm` y `33 × 40 × 63 cm`, evitando inventar ejes, unidades o asociaciones.
4. **Cantidades y precios:** comprobar los resultados de MP-0050 y MP-0022 utilizando las nuevas grabaciones R2. Mantener las cantidades realmente reconocidas y evitar correcciones artificiales basadas en los guiones.
5. **Otros problemas detectados:** corregir cualquier defecto NLP adicional que esté respaldado por evidencia y pueda resolverse sin comprometer la seguridad comercial.

Mantener las abstenciones justificadas cuando existan ambigüedades sobre juegos de mesas, casilleros o credenzas. No forzar propuestas cuando la información sea insuficiente.

## 2. Implementación

- Inspeccionar primero el estado real del repositorio y sus herramientas.
- Aplicar correcciones directamente al código NLP.
- Incorporar pruebas automatizadas para cada defecto corregido.
- Mantener el contrato público, el modo `RULES_ONLY` y la compatibilidad con Backend.
- No modificar ASR, modelos acústicos ni los otros repositorios, salvo que sea estrictamente necesario y se justifique previamente.
- No alterar los audios originales ni los resultados históricos.

## 3. Verificación obligatoria

Después de implementar:

1. Ejecutar las pruebas unitarias y de integración del NLP.
2. Reprocesar los 13 casos R1 y los 2 casos R2 para comparar antes y después.
3. Ejecutar las regresiones sobre los 120 casos históricos.
4. Verificar cantidades, precios, dimensiones, componentes, asociaciones y abstenciones, no solamente el estado de las propuestas.
5. Confirmar que las correcciones resuelven los defectos identificados sin introducir errores comerciales.
6. Ejecutar lint, validaciones del paquete y comprobaciones de compatibilidad disponibles.

Si alguna corrección produce regresiones, ajustarla o descartarla justificadamente.

## 4. Entrega

Quiero recibir únicamente:

- Mejoras implementadas y problemas resueltos.
- Resultados de pruebas y comparaciones antes/después.
- Regresiones detectadas y su resolución.
- Limitaciones que justificadamente continúan pendientes.
- Commit correspondiente con los cambios verificados.

**Prioridad absoluta: mejorar el NLP de HOMEX de manera comprobable, sin inventar datos comerciales ni sacrificar comportamientos correctos.**

No abrir PR ni modificar Backend o Frontend por ahora.Nuevas grabaciones

MP-0050:

~/Descargas/HOMEX_Guiones_Evaluacion_Voz/regrabaciones-dirigidas-v1/prioridad-2/audios_asr/MP-0050-R2.wav

Duración verificada: 59,350188 segundos.

MP-0022:

~/Descargas/HOMEX_Guiones_Evaluacion_Voz/regrabaciones-dirigidas-v1/prioridad-2/audios_asr/MP-0022-R2.wav

Duración verificada: 64,621125 segundos.

- L2: RED:9 failed/11 passed before correction. GREEN:21 then23 retake regressions; historical comparison caught MP-0037 existing-height re-parenting, pinned RED and fixed by placing chain preservation after explicit association. All240 historical inputs and15 retakes compared; only removed attribute is the known article-height1. Current private evidence: /home/gabriel/Descargas/HOMEX_Guiones_Evaluacion_Voz/evaluaciones/nlp-retakes-fix-20261115-4zygFK.

- L3: Independent verifier found the existing material-only comma ambiguity regression; one correction requires positive dimensional evidence. Targeted recheck12 passed; final full suite1080 passed; final parent spot check60 passed. Ruff/schema/corpus/package/privacy/reproducible installed consumer checks pass. Sole final removed field is false article-height1. Five justified retake abstentions remain. No consumer, ASR, schema, audio or model changes.
- L4: Final delivery remains one cohesive local commit (~500 lines including the verbatim task specification), not a PR; keeping source, regression probes and docs together is more reviewable than a tracking-only slice. No publishing or release identity replacement. Exact commit hash is recorded in the private commit.json and Engram because a commit cannot embed its own hash. Rollback boundary: this single parser/reference unit plus its tests/docs.
