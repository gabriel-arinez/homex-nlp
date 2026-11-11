# Improve commercial interpretation of the120 real-voice cases
Branch: feat/real-voice-120-results; start b851b5aa15a04e5ab1046271f124cc05c3135da8. Delivery: single branch, no PR/merge/deploy; preserve all history.
Artifacts: corpus evaluaciones/semantic-120-v1 and logs/semantic-120-v1. Runner: existing Python3.11/pytest/offline Whisper Small. Forecast ~1600 authored lines across coherent units; no code-golf or size-only split.

## Specs
- S0: "Inspecciona el estado actualizado de los repositorios HOMEX, las ramas, los commits, las versiones, los contratos y el estado de GitHub Actions." Preserve original120AAC/WAV/hashes/references/IDs/history and73/27/7/13 classification.
- S1: "Construye un conjunto de referencia estructurado para los 120 casos." Record per-field document/script/ASR provenance, evidence offsets, values/units/modality/ambiguity; acoustic human validation remains PENDIENTE without reliable listening; generate timestamped replay clips.
- S2: "Mantén como referencia el Whisper Small CPU/int8 original y sus transcripciones congeladas." Investigate MP-0017,MP-0045,PIS-0006/models; controlled available decode parameters, exact hashes/config/text/resources; no full scripts or hidden original codes in prompts.
- S3: "Conserva el texto original, los offsets, la evidencia y los motivos de cada transformación." Distinguish format/equivalence/uncertain reconstruction; no missing facts invented.
- S4: "Para cada defecto, escribe primero una prueba de regresión que reproduzca el problema." Generalizable fixes for product/component references, dimensions, price modalities, names, materials/thicknesses, accessories/codes; preserve contracts/category differences/abstentions; never match corpus IDs.
- S5: "Esta comparación es obligatoria para atribuir las mejoras a su componente correcto." Evaluate all120 in four combinations original/candidate ASR × original/corrected NLP; per-category/field/case/version numerators, denominators, recoveries, FP, regressions, abstentions and no-proposal.
- S6: "Los 120 audios utilizados para diseñar las correcciones constituyen datos de desarrollo." Group family leakage; new linguistic probes and independent-audio protocol, no invented generalization.
- S7: "La aplicación de datos debe evaluarse semánticamente." Test Audio→ASR→normalization→NLP→proposal→backend→four forms on effective versions, no stock/permission/approvedprice/state mutation.
- S8: "Verifica que el paquete consumidor utilice el nuevo wheel, no solamente las fuentes locales mediante PYTHONPATH." New version/reproducible artifacts and real consumer; preserve old artifacts; minimum exact Gitleaks false-positive correction, CI green, no disabled gates.
- S9: "Una vez aprobadas las verificaciones, crea y sube los commits correspondientes. No fusiones a main ni despliegues producción sin revisión final." Safe controlled branch, no other changes overwritten; sanitized publication only, no recordings/credentials/productive data/unneeded files.

## Tasks
- T0 [S0] inline + bounded explorer only when mapping budget exceeded; active: refreshed state/contracts/CI and preservation ledger; commit pending.
- T1 [S1,S6] delegated writer: independent reference-annotation unit in parallel with parent ASR tooling, disjoint files; proposals produced,25tests; acoustic/semantic association pending; commit pending.
- T2 [S2,S5] inline ASR experiment tooling + delegated long execution when useful; pending.
- T3 [S3,S4] inline furniture relation/dimension/price/accessory fixes;871tests green; independent verification pending; catalog writer only when independent parallel unit has disjoint surface.
- T4 [S3,S4] catalog spoken-code/name normalization unit;107focused tests and18unchanged differential probes; independent verification pending; route determined after evidence.
- T5 [S5,S6] four-cell120-case evaluation + independent bounded verifier(item3shared behavior); pending.
- T6 [S7,S8] new version/offline distribution/real installed backend wheel + four-form integration; pending; own worktree for backend changes, no root checkout writes.
- T7 [S8,S9] minimum Gitleaks fingerprints/CI fixes, current reports/sanitized evidence/commits/push; pending.

## Log
### L1 User request (verbatim)
Tu tarea consiste en continuar y completar el trabajo iniciado en `homex-nlp`, rama `feat/real-voice-120-results`, auditada en el commit `b851b5a`.

**El objetivo es mejorar de manera sustancial y demostrable la interpretación de los 120 audios reales, corregir los defectos semánticos pendientes y obtener una evaluación rigurosa antes de integrar los cambios.**

No busques únicamente elevar porcentajes. La prioridad es recuperar correctamente los datos comerciales, evitar información inventada y reducir la necesidad de corrección manual.

## FASE 0 — Contextualización y preservación

Inspecciona el estado actualizado de los repositorios HOMEX, las ramas, los commits, las versiones, los contratos y el estado de GitHub Actions.

Revisa especialmente:

`audit/real-voice-120/`

`audit/real-voice-120/evaluaciones/audit-120/latest-evaluation.json`

`audit/real-voice-120/evaluaciones/audit-120/root-cause-matrix.json`

`audit/real-voice-120/evaluaciones/audit-120/case-matrix.csv`

El corpus original está en:

`~/Descargas/HOMEX_Guiones_Evaluacion_Voz/`

Conserva intactos los 120 AAC, sus WAV, hashes, referencias, identificadores y resultados históricos. Usa directorios nuevos para cada evaluación.

La clasificación comercial vigente es:

- Muebles a pedido: 73.
- Sillas: 27.
- Pisos flotantes: 7.
- Otros: 13.

Los sillones y las poltronas pertenecen a OTRO. No reviertas esta clasificación.

## FASE 1 — Construcción de referencias verificables

El principal déficit de la intervención anterior es la ausencia de referencias completas para todos los campos comerciales.

Construye un conjunto de referencia estructurado para los 120 casos.

Utiliza los guiones, proformas originales, transcripciones y audios. Diferencia expresamente los datos que aparecen en el documento original de aquellos que realmente fueron pronunciados.

Genera propuestas de anotación para cada campo y verifica su procedencia. Cuando sea posible revisar la grabación directamente, comprueba el contenido acústico. Si la herramienta no dispone de capacidad de escucha fiable, genera fragmentos de reproducción con marcas de tiempo para revisión humana y conserva el estado PENDIENTE.

Nunca conviertas una transcripción automática en verdad humana validada.

Registra valores esperados, evidencia textual, categoría, unidad, modalidad comercial, ambigüedad y estado de verificación.

No alteres los originales para hacer coincidir los resultados.

## FASE 2 — Diagnóstico ASR exhaustivo

Mantén como referencia el Whisper Small CPU/int8 original y sus transcripciones congeladas.

Analiza individualmente los 120 audios utilizando la señal acústica, duración, silencios, segmentos y diferencias de transcripción.

Investiga especialmente MP-0017, MP-0045, PIS-0006 y los casos de modelos deletreados.

Diseña experimentos controlados con parámetros disponibles en la versión instalada de faster-whisper, incluyendo, cuando corresponda, `condition_on_previous_text`, VAD, `beam_size`, temperaturas y vocabulario de contexto.

Prueba cada configuración de manera reproducible. Registra configuración exacta, hashes del modelo, texto resultante, métricas, tiempo y recursos.

No introduzcas guiones completos como prompts ni utilices códigos originales ocultos para reconstruir respuestas.

Si un modelo alternativo mejora significativamente los resultados, compara su costo operativo. No cambies el modelo productivo sin una justificación cuantitativa y contractual.

Conserva tanto el WER original como una métrica normalizada con equivalencias numéricas y comerciales verificadas.

## FASE 3 — Normalización y corrección de errores de reconocimiento

Investiga e implementa, cuando sea seguro, una normalización lingüística contextual para:

- Números en palabras y cifras.
- Decimales y agrupadores numéricos.
- Medidas orales compuestas.
- Unidades comerciales.
- Expresiones monetarias.
- Códigos alfanuméricos deletreados.
- Abreviaturas técnicas.
- Variantes fonéticas recurrentes del ASR.
- Términos del vocabulario comercial HOMEX.

Distingue corrección de formato, equivalencia semántica y reconstrucción incierta.

Conserva el texto original, los offsets, la evidencia y los motivos de cada transformación.

No infieras datos ausentes ni conviertas expresiones ambiguas en hechos confirmados.

## FASE 4 — Refactorización focalizada del NLP

Estudia y corrige las causas raíz identificadas en `RulesEngine`, `catalog.py`, `rules.py` y los consumidores correspondientes.

Prioriza los problemas siguientes.

**Relaciones entre productos y componentes:** resolver falsas detecciones de múltiples productos, repeticiones referenciales, escritorios con cajoneras, conjuntos, módulos y componentes internos. Respetar las abstenciones legítimas y los contratos vigentes.

**Dimensiones:** evitar duplicación o asociación incorrecta de ejes; corregir medidas orales, alturas, profundidades, dimensiones compuestas y unidades. Investigar MP-0036 y MP-0045.

**Precios:** reconocer modalidades comerciales explícitas y expresiones deterioradas por ASR, incluyendo MP-0045. Mantener diferenciados precio unitario, total negociado e importes ambiguos.

**Nombres comerciales:** delimitar el nombre sin absorber materiales, medidas ni características técnicas. Investigar MP-0067 y los casos de catálogo identificados en la auditoría.

**Materiales y espesores:** mejorar su extracción y asociación al componente correcto, evitando asignaciones globales injustificadas.

**Accesorios:** revisar USB, HDMI, conectores, cerraduras, herrajes, tiradores, rieles, tomacorrientes y cantidades por componente.

**Modelos:** interpretar códigos hablados cuando existe evidencia suficiente, conservando ambiguos los códigos incompletos.

**Catálogo:** respetar las diferencias entre SILLA, PISO_FLOTANTE, OTRO y MUEBLE_MEDIDA, así como los campos comerciales realmente soportados.

Para cada defecto, escribe primero una prueba de regresión que reproduzca el problema. Implementa una corrección generalizable y comprueba que no afecta las reglas existentes.

No soluciones problemas mediante excepciones atadas a los identificadores MP, SIL, PIS u OTR.

No introduzcas un modelo adicional de NLP sin demostrar por qué no bastan las alternativas menos complejas.

## FASE 5 — Evaluación iterativa

Después de cada grupo de correcciones, reejecuta las pruebas relevantes y el análisis sobre las 120 transcripciones ASR originales.

Cuando cambie el ASR, ejecuta además el análisis completo sobre las nuevas transcripciones.

La comparación deberá permitir separar:

ASR original + NLP original.

ASR original + NLP corregido.

ASR candidato + NLP original.

ASR candidato + NLP corregido.

Esta comparación es obligatoria para atribuir las mejoras a su componente correcto.

Calcula métricas por categoría, campo, caso y versión.

Informa recuperaciones, falsos positivos, regresiones, abstenciones y casos sin propuesta.

No ocultes los casos difíciles ni excluyas ejemplos para aumentar artificialmente los porcentajes.

## FASE 6 — Verificación independiente y generalización

Los 120 audios utilizados para diseñar las correcciones constituyen datos de desarrollo.

Agrupa las familias comerciales repetidas y evita utilizarlas como supuesta validación independiente.

Ejecuta regresiones lingüísticas nuevas y variantes controladas.

Si existen grabaciones independientes de otros hablantes, entornos o dispositivos, utilízalas como evaluación final sin ajustar reglas posteriormente sobre esos mismos ejemplos.

Si todavía no existen esas grabaciones, no inventes métricas de generalización. Deja preparado un protocolo reproducible de evaluación independiente.

## FASE 7 — Integración real HOMEX

Verifica los resultados con las versiones efectivas de homex-backend y homex-frontend.

Comprueba el recorrido:

Audio → ASR → normalización → NLP → propuesta → backend → formulario.

Evalúa los cuatro formularios y los casos representativos de alto riesgo.

Comprueba que los valores aparezcan en sus campos correctos y que ninguna propuesta modifique automáticamente stock, permisos, precios comerciales aprobados o estados autoritativos.

No consideres suficiente recibir un HTTP 200 o completar la transcripción.

La aplicación de datos debe evaluarse semánticamente.

## FASE 8 — Calidad, seguridad y distribución

Corrige los problemas pendientes de GitHub Actions.

Para el fallo de identidad del wheel, conserva los hashes y distribuciones históricos, prepara una versión nueva cuando las modificaciones estén estabilizadas y valida su identidad, reproducibilidad y consumo real desde el backend.

Para Gitleaks, investiga las dos coincidencias del tokenizador y aplica únicamente la corrección o excepción mínima demostrablemente segura. No desactives los controles.

Verifica que el paquete consumidor utilice el nuevo wheel, no solamente las fuentes locales mediante PYTHONPATH.

Ejecuta todos los tests, validaciones de esquemas, Ruff, contratos, build, integración, E2E y CI aplicables.

Revisa la información comercial publicada en GitHub, las trazas y su saneamiento. No subas audios originales, credenciales, datos productivos ni archivos innecesarios.

No elimines evidencia histórica sin autorización.

## FASE 9 — Publicación y cierre

Trabaja sobre una rama controlada a partir del estado real encontrado.

No sobrescribas cambios ajenos y no utilices comandos Git destructivos.

Resuelve todos los defectos verificables que puedan corregirse sin comprometer la seguridad o los contratos. Si existe una limitación genuina, documenta su causa y evidencia; no la presentes como éxito.

Una vez aprobadas las verificaciones, crea y sube los commits correspondientes. No fusiones a main ni despliegues producción sin revisión final.

## ENTREGABLES OBLIGATORIOS

Produce una matriz exhaustiva con resultados de los 120 casos, referencias verificadas, transcripciones originales y candidatas, resultados NLP, campos esperados y obtenidos, errores y causas raíz.

Entrega métricas ASR y NLP iniciales y finales, discriminadas por categoría y campo, con numeradores, denominadores y definición de cada indicador.

Incluye un registro completo de experimentos ASR: parámetros, modelo, recursos, latencias y resultados.

Incluye los cambios realizados, las pruebas nuevas, las regresiones detectadas y la evidencia de integración.

Guarda los informes y resultados en la carpeta `evaluaciones/` del corpus local, y los logs completos de consola en `logs/`.

Actualiza la documentación vigente para que no contradiga el estado real de la rama, los commits y CI.

Proporciona los hashes, commits, estado de workflows y comandos exactos para reproducir localmente las verificaciones.

## CRITERIOS DE ÉXITO

La intervención se considerará terminada únicamente cuando exista evidencia reproducible de una mejora real en los campos comerciales, se hayan corregido los defectos factibles de alta prioridad, no existan regresiones relevantes, la integración sea compatible y los controles CI estén verdes.

Un porcentaje mayor obtenido exclusivamente mediante cambios en la normalización de la métrica no cuenta como mejora del reconocimiento.

Una mayor cantidad de campos extraídos tampoco cuenta como éxito si aumenta la información comercial incorrecta.

**Prioridad definitiva: maximizar la precisión comercial verificable de HOMEX, aprovechando integralmente los 120 audios reales, sin sobreajustar las reglas ni degradar la seguridad del sistema.**

No te detengas después del diagnóstico. Ejecuta la intervención completa, las iteraciones necesarias y las verificaciones pertinentes, conservando evidencia de cada decisión y de los problemas que no puedan resolverse con seguridad.

### L2 Initial observed state
NLP clean except existing untracked.atl, HEADb851b5aa15a04e5ab1046271f124cc05c3135da8 on requested branch.
Backend main ee6c80f13ff76e23c4c572c81042a0b9760db033 clean. Frontend main has advanced to feece0a99689c9a73c601f249ea1af3bf11e1b6e clean; do not roll it back to older integration snapshot.
GitHub Actions43053260266 failed release-wheel identity and2Gitleaks tokenizer-file SHA256 false positives; package/dependency-audit jobs passed. RDD preference must stay user-owned.
No independent audio listening capability is available to this tool session; direct acoustic assertions remain pending; signal analysis/alternate ASR are not human truth.


### L3 Semantic checkpoint
Reference-v2 preserves all240audio hashes and5381exact spans;1115literal/scalar proposals are script-verified,1688semantic entries pending, acoustic denominator0. ASR five controlled all120configurations running. First full source regression871cases caught3new regressions; unsafe unit inheritance and ambiguous truncation were corrected without weakening historical tests. Final871passed. RDD remains off.
