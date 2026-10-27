# HOMEX — Auditoría independiente B1–B4 de Corpus V2
**Fecha:** 2026-10-27 · **Rama aislada:** `audit/corpus-v2-b1-b4-20261027`
**Base fijada:** NLP PR #31, `fb1ad97b15c0616721609a375c179a4d2b7ce080` (no es runtime v14).  
**Naturaleza:** revisión técnica remota de artefactos versionados. **No** representa ejecución local, homologación humana, nuevos resultados de campo, ni autorización para promover modelos.  
**Independencia:** no modificar corpus, split, expected, runtime, wheel, audio o trabajos de Codex v14.

## B1 — Auditoría y dictamen técnico
Fuentes inspeccionadas: `docs/closure_v2/README.md`, `MATRIZ_8_ETAPAS.md`, `audit.json`, `development_overlay.json` (estructura y muestras), `oral_intake/PROCEDIMIENTO.md`, `dev_experiment.json` (estructura y métricas), metadata y lista de 22 archivos cambiados del NLP PR #31; PRs NLP #31/#32, backend #39 y frontend #42; plan maestro y continuidad histórica.

- Base V1: **675** registros, **483 train / 94 dev / 98 test**; `SINTETICO=675`; preanotación sintética, no GOLD. `audit.json` incluye 12 hashes de corpus/split/expected, sin errores formales declarados.
- `development_overlay.json`: **577** train/dev inspeccionados mecánicamente, **49** propuestas reversibles de entidades, **277** registros con hechos adicionales. `active=false`, `human_gold=false`, `test_records_emitted=0`. Cada entrada consultada mantiene `source_document_id=null`, `human_reviewed=false`; no adjudicar por conjetura.
- Similitud entre splits: **79 grupos** de prefijo de 65 caracteres y **1 source_id** transversal. No confundir grupos con pares ni declarar fuga semántica probada. El conteo histórico **80** tenía otro denominador.
- PR #31 abierto y draft, con gates de dependencia/CI reconocidos por el autor; la suite local documentada (137) no implica PR íntegramente verde. Documenta alertas `uv audit` preexistentes de filelock/setuptools y pin histórico de backend en package CI. **No** corregir silenciosamente el lock en esta rama.
- Riesgo crítico: V2 candidato no tiene procedencia ítem→cotización conciliada, especialistas revisores ni referencias humanas aprobadas.
- Riesgo metodológico: referencia sintética y elección de época mediante `dev`; no utilizar `test` para decisiones, listas de errores o curación.

**Gate B1:** auditoría documental remota completada; auditoría exhaustiva local por registro, revisión línea a línea de todas las implementaciones y ejecución de suites siguen pendientes. No declarar B1 cerrado integralmente.

## B2 — Plan ejecutable de curación documental, sin alteración de V1
**Decisión:** conservar PR #31 como fuente de auditoría y overlay reversible; no crear otra copia de los 675 ni aceptar mecánicamente 49 reparaciones.

Flujo requerido por lote:
1. Congelar archivos de entrada por SHA256 y comprobar que corresponden a la fuente autorizada. Se documentan dos hashes TXT en el README del PR #31; **hash de archivo no establece correspondencia por ítem**.
2. Elaborar matriz privada `parent_record_id, parent_sha256, source_document_id, source_item_id, source_locator, relation_state, observation, proposed_operation, evidence_literal, ambiguity, reviewer, decision, review_date`. `relation_state` permitido: `CONFIRMADA/POSIBLE/NO_IDENTIFICADA/INCONSISTENTE`; `decision`: `APROBADO/CORREGIDO/DESCARTADO/PENDIENTE`.
3. Priorizar revisión de **49** cambios propuestos de ACCESORIO; **35** menciones de cantidades internas, **12** menciones de capacidad, **247** descuentos explícitos (las categorías pueden solaparse); y alertas por prefijo/`source_id`. No asignar cantidad interna a componentes sin evidencia.
4. Reconciliar el material auténtico y los candidatos rc.1/rc.2 (#20/#22) mediante fuentes privadas. Exigir valor/documento y adjudicación comercial cuando exista discrepancia. No inferir total/unitario, cantidad de muebles, moneda, ejes, unidades o color.
5. Preservar y aislar los **98 test**: solo verificaciones agregadas mecánicas por custodio; no exportar textos, IDs o expected de test para iteración.
6. Solo crear overlay curado V2 con `human_reviewed=true` cuando conste revisión real; incluir antes/después, hash, justificación, autoría, y posibilidad de rollback; validar `char_span`, UTF-8, Unicode, relaciones y splits.

**Gate B2:** infraestructura existente identificada; homologación comercial y corpus V2 utilizable **BLOQUEADOS** por datos/revisores autorizados. No falsear revisiones ni reetiquetar sintéticos como documentos reales.

## B3 — Especialización oral y melamina
La carpeta `oral_intake` del PR #31 ya tiene manifiesto, esquema estricto, registros vacíos y un procedimiento de privacidad. **No sembrar el conjunto con frases nuevas solo para aparentar evidencia**.

Matriz de cobertura a revisar con el piloto sintético de 48 frases (sin convertirlo en GOLD): 
- producto comercial único vs varios; cantidad comercial vs capacidad (p. ej. personas) y vs cantidad interna (cajones/tomacorrientes);
- dimensiones simples/compuestas y unidad explícita/omitida; expresiones orales `un metro veinte`, `dos cuarenta`; negación y rectificación;
- componentes `tapa/mesón/estante/estructura/repisas/cajones`, espesores por pieza y ámbitos ambiguos (incluye `etapa` ASR que **no** autoriza alias a `tapa`);
- materiales/color/acabado, `melamina/melamine/melanina` con revisión del audio, herrajes, accesorios y catálogos, términos regionales de Bolivia;
- precio total vs unitario, descuentos, moneda contextual, cifras orales ambiguas; silencios, puntuación ausente, ruido;
- casos de abstención seguros y campos pendientes, verificación de propuesta en PRF-03.

Por cada ejemplo: `origin, parent, template_group, paraphrase_family, phenomenon_ids, spans, structured_expected, reviewer, adjudication, train/dev/diagnostic`. Usar el esquema vigente solo para los campos admitidos; no inventar etiquetas NER. Las 48 frases son **piloto propuesto** hasta cotejo exacto de los archivos del estudio.

Para audio real: no copiar audios a Git ni ejecutar transcriptor que pueda eliminar originales; controles de consentimiento, retención, hash, doble escucha independiente del ASR y adjudicación comercial (instrumento #28).

**Gate B3:** esquema de ingesta y metodología existentes; material oral homologado, transcripciones humanas y cobertura auditada **PENDIENTES**. No convertir ejemplos artificiales en casos de campo.

## B4 — Revisión experimental y decisión técnica
El `dev_experiment.json` documenta comparación histórica sobre **62 muebles dev sintéticos**, con **1.368 entidades**. Referencias = preanotación sintética. Motor A reglas **v6**: precisión micro 0.6640, exhaustividad micro 0.2442, F1 micro 0.3570, p50 0.377 ms/p95 1.969 ms; motor B NER+ensamblador experimental: métricas micro 1.0000 en el mismo dev, p50 13.389 ms/p95 16.835 ms. Es una señal **no independiente**, con probable similitud de plantillas; no medir éxito comercial, ni afirmar superioridad de B en campo. No comparar directamente con v14, ni promover modelo.
Instrumentación declarada: 5 warmups/motor, 3 pasadas, 186 mediciones temporales/motor (solo 62 frases distintas); CPU, concurrencia 1, sin ASR ni E2E. `WER=null`, `holdout externo=0`.

Diseño obligatorio para próxima evaluación:
1. Congelar candidato runtime v14 + checksum de wheel, dependencia y hardware; y comparadores A=RULES_ONLY v14, B=NER, C=híbrido con veto y abstención. Exigir *mismos* audios/ASR e inputs.
2. Separar métricas `NER span` de `JSON/relaciones`: exactitud comercial, ejes/unidades, espesor↔pieza, materiales↔pieza, cantidad comercial vs capacidad/cantidad interna, precios, conflicto, tasas de abstención/falsas propuestas y de corrección humana.
3. Hacer ablations por señales y medir p50/p95 cold/warm ASR/cola/NLP/proyección/frontend y E2E; latencia de extracción aislada no sustituye UX.
4. Sólo computar WER con transcripción humana aprobada del **mismo audio**, referencias no contaminadas, normalización publicada y conteos S/D/I/N; modelos no pueden mirar el holdout externo antes de la decisión.
5. Predeclarar gates de integridad comercial, privacidad, reproducibilidad y no regresión, con denominadores y revisión de errores. Sin humanos/gold y holdout, decisión = `NO_PROMOVER`.

**Gate B4:** baseline diagnóstico histórico interpretado; experimento nuevo con V14, referencias humanas y decisión cuantitativa **PENDIENTES**. No inventar resultados.

## Dependencias de los cuatro bloques
- B2 y B3 dependen de custodio de TXT/piloto, criterios comerciales y revisiones humanas.
- B4 final depende de referencias comerciales/ASR independientes y dataset externo.
- La línea Codex NLP #32 / backend #39 / frontend #42 avanza en paralelo y no se modifica desde esta rama.
- Cualquier propuesta de actualización de dependencias debe coordinarse con el frente de integración; no desactivar vulnerabilidades ni gates para obtener CI verde.

## Verificación y siguientes acciones con evidencia
- Inspección remota fijada a SHA del PR #31 y sus manifiestos: realizada.
- Cambios en corpus V1, expected, splits, `src`, lock, contratos, audio, modelo: **ninguno en esta rama** (solo documentación nueva).
- Suites Python, reconstrucción del overlay, comparación byte a byte, escucha humana, mediciones sobre hardware del usuario: **no ejecutadas en esta revisión remota**.
- Próximo trabajo habilitado: matriz de casos comerciales desde documentación con permisos, adjudicación de 49 reparaciones y de candidatos rc.1/rc.2; repetir validadores en un worktree aislado antes de autorizar contenido V2.

**Criterio de cierre:** solo declarar B2/B3/B4 cerrados cuando exista revisión, dataset reproducible, métricas independientes y aprobación. El avance de infraestructura no equivale a promoción de un nuevo corpus ni release.
