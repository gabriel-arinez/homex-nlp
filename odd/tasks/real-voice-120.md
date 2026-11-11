# Audit real-voice ASR/NLP quality across 120 recordings
Tracker: feat/real-voice-120. Delivery: auto-chain; chain_strategy: feature-branch-chain (user approved). No main merge, production or remote operations without explicit authorization.
Runner: existing Python 3.11 venv, pytest; artifacts in corpus evaluaciones/ and logs/. Initial authored-code forecast: 350 lines; corrections sized after baseline.

## Specs
- S1: "Antes de modificar cualquier archivo:" inspect all three repositories, contracts, installed versions, source-to-form flow and corpus. Record exact baseline commits.
- S2: "Ejecuta los 120 casos con la implementación actual antes de introducir correcciones." Preserve full ASR and paired reference/ASR NLP results, hashes, timings, versions and failures. "**No modifiques las reglas durante esta primera evaluación.**"
- S3: "Corregir su clasificación comercial a `OTRO`" while preserving all audio and IDs. User confirmed all seven including office sillones on 2026-11-11: "si, continua"; also the three poltronas MP-0004/0062/0067: "si, tambien deben clasificarse como OTRO".
- S4: "No clasifiques un problema basándote únicamente en su apariencia." Compare reference-input and ASR-input extraction; distinguish unsupported fields, ambiguity and source defects.
- S5: "Resolver las causas raíz, no únicamente los ejemplos individuales." Maintain public contracts, avoid invented information; use deterministic RED/GREEN when applicable.
- S6: "Si los 120 casos se utilizan para diagnosticar y corregir el sistema, informa explícitamente que sus métricas posteriores corresponden al corpus de desarrollo y no representan una evaluación independiente."
- S7: "Audio → ASR → NLP → Backend → Propuesta → Frontend." Test all four form categories without production data; disclose unavailable proof.
- S8: "Guarda todos los resultados en la carpeta:" `~/Descargas/HOMEX_Guiones_Evaluacion_Voz/evaluaciones/` and full console in `~/Descargas/HOMEX_Guiones_Evaluacion_Voz/logs/`.
- S9: "Una vez que las correcciones estén verificadas, crea y sube los commits correspondientes." No destructive Git; remote destination and credential require explicit authorization.

## Tasks
- T1 [S1,S3,S8] inline (mapping worker completed read-only reconnaissance); complete: ten commercial corrections plus three canonical labels;73/27/7/13=120, independent verifier confirmed240 hashes and all noncategory fields unchanged; commit pending.
- T2 [S2,S4,S8] inline tooling, delegated long execution (per-action rule); complete: 120/120 baseline cases COMPLETE; frozen ASR/source hashes and corrected routing retained; evaluator/tests/usage guide in chore/real-voice-120-01-evaluation, commit identity recorded by the next child. WER1495/6627,CER7758/42777 are script-relative, not audio-adjudicated accuracy.
- T3 [S4,S5] inline unless independent bounded units justify writers; partial: six bounded root-cause classes fixed and independently verified; full supported-field annotation and remaining semantic defects pending; commit pending.
- T4 [S5,S6,S7] verification delegated only for named high-risk items or long suites; partial: before/after120 pairs, final799 NLP tests,99 backend,306 frontend; prior4-form and latest3-poltrona real browser/audio probes PASS; independent audio-generalization evaluation pending; commit pending.
- T5 [S8,S9] inline; partial: initial diagnosis,120-case aggregate, root matrix and progress report saved; commits/remote release/CI pending; commit pending.

## Log
### L1 Original request (verbatim)
# HOMEX — Auditoría, evaluación y perfeccionamiento integral del sistema ASR/NLP mediante 120 grabaciones reales

Actúa como un equipo de ingeniería senior especializado en reconocimiento automático del habla (ASR), procesamiento de lenguaje natural (NLP), arquitectura de software, integración full-stack, pruebas automatizadas y evaluación de calidad.

## OBJETIVO PRINCIPAL

Tu responsabilidad es **evaluar exhaustivamente el funcionamiento real del sistema de dictado de especificaciones de HOMEX, identificar todos los defectos detectables, investigar sus causas raíz, implementar las correcciones necesarias y verificar los resultados mediante pruebas reproducibles**.

No debes limitarte a producir un diagnóstico ni un informe de recomendaciones. Debes ejecutar el ciclo completo de análisis, intervención, verificación e integración de las correcciones que puedan implementarse con seguridad.

El objetivo no es conseguir artificialmente un 100 % de coincidencias con los guiones, sino mejorar la precisión, robustez, consistencia y capacidad de generalización del sistema.

## 1. CONTEXTO Y DATOS DISPONIBLES

Disponemos de un corpus de 120 grabaciones reales de especificaciones comerciales, organizadas en:

- 79 muebles a pedido.
- 31 sillas.
- 7 pisos flotantes.
- 3 productos de la categoría Otros.

Ubicación:

`~/Descargas/HOMEX_Guiones_Evaluacion_Voz/`

La auditoría previa confirmó:

- 120 archivos AAC originales válidos.
- 120 WAV convertidos correctamente a PCM16, mono, 16 kHz.
- 120 referencias textuales.
- 0 archivos faltantes.
- 0 errores de integridad.

Los archivos relevantes incluyen:

- `manifiesto.csv`
- `referencias/guiones_referencia_pregrabacion.jsonl`
- `referencias/trazabilidad_fuentes.jsonl`
- `evaluaciones/conversiones.csv`
- Carpetas de audios de cada categoría.
- Registro de inconsistencias de las fuentes comerciales.

Los audios corresponden a dictados naturales de especificaciones. **No son conversaciones entre el vendedor y el sistema.**

No se introdujeron errores ni rectificaciones deliberadas en los guiones.

## 2. INVESTIGACIÓN INICIAL OBLIGATORIA

Antes de modificar cualquier archivo:

1. Inspecciona el estado real y actualizado de los repositorios `homex-nlp`, `homex-backend` y `homex-frontend`.
2. Identifica ramas activas, HEAD, dependencias, versiones instaladas y contratos vigentes.
3. Estudia exhaustivamente el recorrido de los audios desde su recepción hasta la presentación de los campos interpretados.
4. Investiga la implementación actual del ASR, modelo Whisper, configuración, parámetros, segmentación y normalización.
5. Analiza los extractores NLP de muebles a pedido, sillas, pisos flotantes y otros.
6. Revisa los adaptadores, contratos, serializadores, validaciones, mapeos y estructuras de datos.
7. Examina la integración frontend/backend, los formularios, los campos admitidos y las reglas comerciales.
8. Examina las pruebas unitarias, contractuales, de integración, E2E y los procesos CI disponibles.
9. Audita el corpus, sus referencias, duplicados, inconsistencias comerciales y correspondencias entre IDs.

No hagas suposiciones sobre rutas, arquitectura ni comportamientos. Comprueba cada aspecto mediante código, contratos, pruebas o ejecución real.

Documenta las versiones y commits exactos que constituyen la línea base.

## 3. ESTABLECER LA LÍNEA BASE

Ejecuta los 120 casos con la implementación actual antes de introducir correcciones.

Cada audio debe relacionarse inequívocamente con su guion mediante el identificador del manifiesto.

Para cada caso, conserva:

- Identificador y categoría.
- Ruta y hash del audio original.
- Referencia textual esperada.
- Transcripción obtenida por ASR.
- Resultado original del extractor NLP.
- Campos interpretados y sus valores.
- Advertencias, ambigüedades y campos no reconocidos.
- Tiempos de procesamiento.
- Versiones efectivas de ASR, NLP y consumidores.
- Estado final de la evaluación.

El procesamiento deberá realizarse sin sobrescribir ni eliminar los audios originales.

No entregues directamente los archivos originales al CLI de ASR si este elimina el archivo recibido. Utiliza copias temporales seguras.

**No modifiques las reglas durante esta primera evaluación.**

## 4. EVALUACIÓN EXHAUSTIVA DEL ASR

Compara cada transcripción con su referencia.

Calcula y reporta, cuando corresponda:

- WER y CER, por caso y por categoría.
- Sustituciones, inserciones y omisiones.
- Reconocimiento de números enteros y decimales.
- Reconocimiento de medidas, dimensiones y unidades.
- Espesores y cantidades.
- Precios y expresiones monetarias.
- Códigos alfanuméricos y modelos.
- Nombres comerciales, materiales, colores y accesorios.
- Fragmentos omitidos y alucinaciones.
- Errores de segmentación y normalización.
- Latencia, rendimiento y consumo de recursos.

Distingue diferencias superficiales de escritura de errores que cambian el significado comercial.

Un número, medida, precio o modelo interpretado incorrectamente debe considerarse especialmente importante.

Verifica que el texto de referencia coincida con lo efectivamente pronunciado. Cuando existan dudas sobre la grabación, clasifica el caso como pendiente de revisión y evita atribuir automáticamente el error al ASR.

## 5. EVALUACIÓN EXHAUSTIVA DEL NLP

Evalúa independientemente las cuatro categorías comerciales.

Compara los datos esperados contra los resultados reales de los extractores, teniendo en cuenta los contratos y campos realmente soportados.

Analiza:

- Identificación del producto.
- Nombres y denominaciones naturales.
- Materiales, espesores y componentes.
- Dimensiones y sus ejes.
- Colores principales y secundarios.
- Accesorios y cantidades asociadas.
- Modelos, códigos, marcas y referencias.
- Precios unitarios, totales y moneda.
- Unidades comerciales.
- Características técnicas y descripciones.
- Datos omitidos, inventados o asignados incorrectamente.
- Ambigüedades y abstenciones.
- Contradicciones entre valores.
- Compatibilidad de los resultados con los formularios correspondientes.

Ten especial cuidado con las diferencias entre el extractor de muebles a pedido y el extractor de catálogo.

No presupongas que ambos deben devolver los mismos campos.

No atribuyas al NLP responsabilidades comerciales que corresponden al backend, como el cálculo autoritativo de totales, las existencias o los movimientos de stock.

Comprueba que una extracción correcta produzca una propuesta utilizable en la interfaz.

## 6. AISLAMIENTO Y CLASIFICACIÓN DE DEFECTOS

Cada problema debe clasificarse según su causa raíz:

- Error del ASR.
- Error de normalización.
- Error de reglas NLP.
- Error de extracción o asociación semántica.
- Error de contrato o transformación de datos.
- Error del backend.
- Error de aplicación frontend.
- Defecto del corpus o de la referencia.
- Ambigüedad legítima.
- Funcionalidad no soportada.

Realiza pruebas controladas para diferenciar los errores encadenados.

Por ejemplo, si una extracción falla con la transcripción ASR, repite la extracción utilizando directamente el guion de referencia. Si con el guion correcto funciona, investiga primero el reconocimiento de voz y la normalización.

No clasifiques un problema basándote únicamente en su apariencia.

Prioriza según impacto comercial, frecuencia y gravedad.

## 7. CORRECCIONES E IMPLEMENTACIÓN

Una vez documentada la línea base y las causas raíz, procede a implementar las mejoras necesarias.

Las correcciones deben:

1. Resolver las causas raíz, no únicamente los ejemplos individuales.
2. Mantener compatibilidad con los contratos públicos vigentes.
3. Conservar los permisos, validaciones y reglas comerciales autoritativas.
4. Mejorar el reconocimiento de lenguaje natural sin exigir frases artificiales al vendedor.
5. Manejar adecuadamente variantes lingüísticas, números, medidas, precios, modelos y especificaciones.
6. Evitar generar información que no fue pronunciada.
7. Conservar evidencias y abstenerse ante ambigüedades no resolubles.
8. Respetar la separación de responsabilidades entre ASR, NLP, backend y frontend.
9. No introducir regresiones en funcionalidades existentes.

Investiga alternativas técnicamente justificadas cuando las reglas actuales sean insuficientes. No presupongas que añadir más expresiones regulares siempre sea la mejor solución.

No cambies el modelo ASR, las dependencias principales o los contratos públicos sin demostrar la necesidad, evaluar sus consecuencias y realizar las pruebas pertinentes.

No alteres los guiones para hacer que las métricas mejoren.

## 8. VALIDACIÓN Y GENERALIZACIÓN

Después de cada conjunto de correcciones:

- Ejecuta pruebas unitarias y contractuales.
- Ejecuta las regresiones existentes.
- Reprocesa los casos relevantes.
- Comprueba que los defectos identificados realmente desaparecieron.
- Detecta nuevas regresiones.
- Evalúa el rendimiento y las latencias.

Diseña una evaluación independiente con dictados y variantes que no hayan determinado directamente las nuevas reglas.

Evita que descripciones prácticamente idénticas de un mismo producto queden repartidas entre entrenamiento o ajuste y evaluación independiente.

Si los 120 casos se utilizan para diagnosticar y corregir el sistema, informa explícitamente que sus métricas posteriores corresponden al corpus de desarrollo y no representan una evaluación independiente.

No declares generalización demostrada sin evidencia independiente.

## 9. INTEGRACIÓN END-TO-END

Verifica el recorrido real:

Audio → ASR → NLP → Backend → Propuesta → Frontend.

Comprueba la correcta representación y aplicación de los campos en:

- Formulario de muebles a pedido.
- Formulario de sillas.
- Formulario de pisos flotantes.
- Formulario de otros productos.

Revisa valores normalizados, unidades, estados, advertencias, campos opcionales y manejo de errores.

No basta con que el extractor devuelva un JSON técnicamente válido.

## 10. REPORTES Y EVIDENCIA

Guarda todos los resultados en la carpeta:

`~/Descargas/HOMEX_Guiones_Evaluacion_Voz/evaluaciones/`

Guarda las salidas completas de consola en:

`~/Descargas/HOMEX_Guiones_Evaluacion_Voz/logs/`

Entrega como mínimo:

- Informe de diagnóstico inicial.
- Resultados por cada uno de los 120 audios.
- Transcripciones ASR originales.
- Comparaciones contra referencias.
- Campos esperados y obtenidos.
- Clasificación de errores.
- Matriz de causas raíz.
- Cambios implementados.
- Métricas antes y después.
- Regresiones y pruebas nuevas.
- Resultados de integración.
- Limitaciones y defectos no resueltos.

No ocultes errores, no inventes porcentajes y no sustituyas resultados de consola por afirmaciones generales.

### ACLARACIÓN IMPORTANTE — Clasificación comercial de sillones

Se ha identificado una inconsistencia en la clasificación utilizada para preparar el corpus de evaluación.

**En HOMEX, los sillones no pertenecen a la categoría «Muebles a pedido», sino a la categoría «Otros» del catálogo comercial.**

Esto incluye, entre otros, los sillones y conjuntos de sala de espera que anteriormente fueron agrupados como muebles a pedido.

Por tanto, debes:

1. Identificar todos los registros afectados, examinando los guiones, las proformas originales, el manifiesto y las referencias JSONL.
2. Corregir su clasificación comercial a `OTRO`, respetando el funcionamiento real del sistema HOMEX.
3. Actualizar de forma consistente el manifiesto, las referencias, los reportes y las agrupaciones estadísticas.
4. Conservar los audios AAC y WAV originales, sus identificadores y las correspondencias existentes. No exigir nuevas grabaciones ni renombrar archivos sin necesidad.
5. Evaluar estos productos mediante el extractor correspondiente a la categoría `OTRO`, no mediante el extractor de muebles a pedido.
6. No forzar al extractor `OTRO` a producir campos exclusivos del configurador de muebles a pedido.
7. Verificar que la reclasificación no provoque pérdidas de información ni errores de integración con el backend y frontend.

**Importante:** esta corrección corresponde a un error de clasificación del corpus, no necesariamente a un defecto del NLP.

Los totales por categoría deberán recalcularse después de identificar los registros afectados. El corpus deberá seguir conteniendo exactamente **120 grabaciones**, sin duplicaciones ni omisiones.

Aplica esta clasificación antes de establecer las métricas definitivas de referencia y conserva evidencia de los cambios realizados.

## 11. GIT, CALIDAD Y CIERRE

Trabaja únicamente en los repositorios que realmente necesiten cambios.

Antes de modificar, inspecciona `git status`, el historial y los cambios existentes.

No sobrescribas trabajo ajeno ni utilices comandos Git destructivos.

Utiliza ramas apropiadas cuando corresponda.

Ejecuta las comprobaciones de calidad, lint, formato, tests, build, contratos e integración que apliquen.

Una vez que las correcciones estén verificadas, crea y sube los commits correspondientes. Respeta los controles CI y las políticas de integración existentes.

No modifiques despliegues productivos ni datos comerciales reales.

Si una corrección no puede realizarse con seguridad o existe un bloqueo externo, conserva la evidencia y explica claramente la limitación.

## 12. CRITERIOS DE FINALIZACIÓN

No declares completada la intervención hasta que:

1. Los 120 casos tengan resultados individuales auditables.
2. Se hayan identificado y clasificado todos los defectos observados.
3. Las correcciones factibles estén implementadas.
4. Las pruebas de regresión correspondientes hayan aprobado.
5. La compatibilidad entre repositorios haya sido verificada.
6. Las métricas finales estén comparadas contra la línea base.
7. Se hayan documentado los problemas pendientes y sus motivos.
8. Los cambios verificados estén publicados en los repositorios correspondientes.

### ENTREGA FINAL

Proporciona un resumen ejecutivo acompañado de los resultados completos de consola.

Incluye:

- Rendimiento inicial y final por categoría.
- Exactitud ASR y NLP.
- Defectos identificados y corregidos.
- Casos que continúan fallando.
- Mejoras realizadas en cada repositorio.
- Commits publicados.
- Estado CI.
- Rutas de informes y logs.
- Comandos exactos para reproducir la evaluación localmente.

**Prioridad principal: conseguir un sistema capaz de interpretar especificaciones comerciales reales con la máxima fiabilidad posible, sin memorizar el corpus ni comprometer la estabilidad de HOMEX.**

No te detengas tras el diagnóstico. Completa las fases de análisis, corrección y verificación de forma autónoma hasta alcanzar los criterios de finalización, documentando cualquier limitación demostrable.

### L2 Clarification (2026-11-11)
Assistant: "¿Tu indicación de clasificar los sillones como `OTRO` incluye también esos cuatro sillones de oficina?"
User: "si, continua"
Accepted: MP-0005, MP-0063, MP-0068, SIL-0010, SIL-0019, SIL-0020, SIL-0029 → OTRO.
### L3 Initial evidence
NLP main c94e7a89995a7157bd113a03bb8304321d30b0b1, existing untracked .atl/ preserved.
Backend main ee6c80f13ff76e23c4c572c81042a0b9760db033 clean.
Frontend main ecb7f23b4d7f25317ae1501733cc8c915bed63c1 clean.
NLP 0.1.21, faster-whisper 1.2.1, CTranslate2 4.8.2; local model small CPU/int8.
AsrService and CLI unlink input; disposable copies mandatory.
RDD global OFF: no review lifecycle. No source changes or evaluation at baseline.


### L4 Baseline and first bounded correction batch
Baseline artifacts: corpus evaluaciones/audit-120/baseline, logs/audit-120-baseline.log and audit-120-integrity.log. No inference errors.
Three reproduced root causes: explicit commercial price-per-unit phrases omitted, conjunction consumed at measurement start, previous seat context suppresses explicit backrest. RED 8 failed/3 passed; GREEN 55 passed with existing catalog tests. One test expectation corrected to retain pre-existing seat literal (espuma inyectada). Model/dependencies/contracts unchanged. RDD remains OFF.
Risk: item 3 (shared price parser and catalog extraction serve existing consumers); independent verifier required before acceptance.

### L5 Bounded integration and expanded defect fixes
Independent first-batch verification: 780 NLP tests; 99 backend tests with isolated UTF8 PostgreSQL and real candidate NLP; 306 frontend tests, contracts/typecheck/build pass. Actual Chromium uploads through real Whisper and Django passed selected field application in all four forms (MP0001, SIL0001, PIS0001, MP0005). Inventory unchanged; no commercial writes. Not full corpus semantic coverage.
Second diagnosis: missing storage nouns armario/casillero and accented clóset cause NO_PRODUCT; HDF gauge without espesor label omitted. RED 9 failed/12 passed; GREEN65 focused tests. Added bounded lexical/board-gauge handling, preserving axis/negation/alternatives. Final verifier pending.
New product-classification uncertainty: MP-0004, MP-0062, MP-0067 are called poltronas fijas, not sillones; user classification confirmation required before definitive category metrics. No reclassification by synonym assumed.

### L6 Regression discovered and corrected
Second-batch full suite found existing `test_secondary_out_of_scope_words_do_not_reject_furniture[Un mueble con casilleros]` failure: newly recognized casilleros became an independent product. Extended the existing subordinate-cajonera filter to casillero (same con-context), preserving original test. Final full suite: 790 passed; schemas/lint/format pass. Batch2 evaluator output v2 is retained, latest corrected snapshot is after-nlp-v3. Vocabulary recognizes standalone casillero but MP0057 remains multiple-product/compartment ambiguity and is not silently collapsed.

### L7 Verified checkpoint / unresolved business decision
Reports and complete result/console paths under corpus evaluaciones/audit-120/ and logs/. Latest after snapshot after-nlp-v3. Partial manual financial oracle independently checked:85 explicit-unit amounts, ASR59→62 matches/reference64→67; no wrong extracted explicit amounts,23 ASR omissions remain. Floor reference3→7 of7,ASR3→6 of7. NOT complete NLP accuracy; human listening/full field annotation pending. Final real integration rerun4/4 and backend99 pass exact24 source hashes; source snapshots preserved, known scratch cleaned.
No model/dependency/public schema changes, no production data/remote credentials used, no commit/push/CI run yet. Installed backend still old0.1.21; candidate source integration is not a packaged deployment. Current authored change exceeds400 lines incl reusable evaluation tooling/tests and verbatim task log: delivery-strategy decision required before commits. New question required: whether poltronas MP-0004/0062/0067 also route OTRO (current76/27/7/10 provisional; yes would73/27/7/13). Do not infer this from earlier confirmation of seven named sillones.

### L8 Additional category authorization (2026-11-11, verbatim)
User: "si, tambien deben clasificarse como OTRO"
Accepted: MP-0004, MP-0062, MP-0067 → OTRO. Target totals73 muebles_pedido/27 sillas/7 pisos/13 OTRO,120 total. Reopen T1 for metadata correction, T2/T4 for original-code category rerouting and current-code replay; retain the entire frozen original baseline as historical evidence. No need to change/retranscribe audio or modify extraction rules for this corpus correction. Risk:item1(existing corpus metadata); independent losslessness verifier required.

### L9 Post-reclassification extraction defect (authorized original audit scope)
After routing the three poltronas to OTRO with ORIGINAL code, MP-0004/0062 ASR input starts numeric `2 poltronas...` and omitted both nombre and observaciones; spelled-out Dos input did not. Root cause: initial noun-phrase recognizer required an alphabetic first character. Added bounded positive-integer prefix preserving literal name/evidence and full observations, no quantity/stock inference, excluding standalone amounts/units and zero/negative fragments. New rule RED3failed/27passed; GREEN74 focused/catalog; full suite799passed, schema/lint/format pass. Corrected baseline-routing-v2 uses original c94e7a8 source verified against24 hashes and immutable ASR; after-nlp-v5 replays current code on120 paired inputs. Only two additional case/input field outputs changed relative v4. Risk:item3(shared catalog parser); independent verifier pending.

### L10 Poltrona classification and numeric-name batch verified
T1 confirmed73 furniture/27chairs/7floor/13OTRO,120 total; all240 hashes unchanged and backups before-poltronas/before-numeric-name retained. Original-code baseline rerouted in external archive after verifying all24 original source hashes, only3 NLP cases changed category, all120 raw ASR objects preserved; snapshot baseline-routing-v2. Current after-nlp-v5 replays120 pairs; onlyMP0004/0062 ASR gain name+observations vs v4, no invented quantity/stock. Independent verifier and latest99backend tests pass; actualChromium/Whisper/Django OTRO application3/3 passes for poltronas, literaldescription/5500 preserved.799 NLP tests plus schemas/lint/format passed, parent focused74passed. All24 latest source hashes match results; services stopped and knownscratch cleaned.
Current reports/aggregates now follow latest-evaluation.json (baseline-routing-v2,after-nlp-v5); oldfrozen snapshots intentionally historical. Partial-price counts85 explicit:ASR62→65,reference67→70; +3 baseline matches from reclassification are NOT an NLP gain. Fullsemanticannotation/listening, independent audio study and versionedpublication/CI remain open. No commits/push yet. Forecast exceeds400 authored lines: before next commit, resolve ask-on-risk chain strategy. Recommend feature-branch-chain to review separate units without integrating into main until feature is ready. Remote credentials/destination remain unapproved, do not discover ambient auth.

### L11 Delivery strategy authorized (2026-11-11)
User: "si, procede"
Accepted previous explicit proposal: feature-branch-chain; draft/no-merge tracker feat/real-voice-120, based on c94e7a8. Original audit/real-voice-120 branch remains intact.
Review slices: tracker audit specification/evidence; chore/real-voice-120-01-evaluation (safe evaluator, tests and usage guide); fix/real-voice-120-02-extraction (six bounded fixes, regressions and grammar docs). Later release/integration work remains separate and pending.
Each child targets its immediate parent. Local commits are authorized; remote credential/session and publication must still be explicitly authorized before any remote lookup, push or PR call.

### L12 First local review slice
Tracker ff4df9220665d026bce42ba48bfc8c3954576c42 contains only this specification/evidence (397 authored lines); passive structural readback and diff check passed. Evaluation child includes the safe runner,3 deterministic metric tests and usage guide; no extraction-rule changes staged in this slice. Existing source corrections remain untouched for the next child. Functional proof: original120case run and metric tests3passed; branch-isolated full checks follow after commit. Rollback boundary: tools/evaluate_real_voice.py,tests/evaluation/test_real_voice.py,docs/real-voice-evaluation.md only, preserving corpus and extractor behavior. RDD is disabled/unmanaged; no remote actions.
