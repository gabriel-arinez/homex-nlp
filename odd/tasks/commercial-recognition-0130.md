# Commercial recognition 0.1.30
Objective: improve commercial recognition against frozen 0.1.29 inputs without invented attributes.
Branch: feat/commercial-recognition-0130 (NLP and isolated Backend worktree). Delivery: feature-branch-chain, joint integration; forecast 800–1200 authored lines. Runner: existing Python 3.11 virtual environments, pytest, Ruff, schema/build/integrity tools. Remote publication is not yet authorized.

## Specs
- S1: «reconocer nombres comerciales válidos sin depender de una enumeración cerrada de productos.» Cases: «Espejo decorativo», «Armario metálico», «Librero modular», «Ventana corrediza». «Conserva la capacidad de abstención ante textos que realmente carecen de información comercial.»
- S2: «interpretar correctamente las formas habituales de expresión de un vendedor, sin obligarlo a comenzar siempre con `nombre:` o `producto:`.» Cases: «Quiero registrar producto: Espejo Aurora», «Necesito agregar un producto llamado Librero Atlas», «El nombre comercial es Armario Boreal», «Registra un producto nuevo: Organizador Modular». «Las referencias al producto, correcciones habladas y delimitaciones entre nombre y características deben seguir siendo coherentes.»
- S3: «aceptar propuestas parciales cuando exista información comercial suficiente, aunque no se mencionen dimensiones ni precios.» Cases: «Un mueble de MDF», «Un mueble de vidrio», «Un mueble con ruedas», «Un mueble con iluminación LED», «Un mueble con acabado lacado». «No inventes atributos ausentes.»
- S4: «distinguir, hasta donde la evidencia lo permita, una prueba de micrófono de una declaración comercial auténtica.» Cases: «Hola, probando el micrófono», «Uno, dos, tres, prueba de audio», «Producto: prueba de voz», «Nombre: prueba», «Silla Probando», «Nombre comercial: Micrófono Aurora». «No utilices prohibiciones globales de palabras como «prueba», «hola» o «micrófono».» «Cuando exista ambigüedad real, conserva la posibilidad de revisión humana en lugar de inventar una clasificación segura.»
- S5: «asegurar que los campos propuestos, sus evidencias, advertencias y revisiones humanas sean coherentes con el resultado final validado.» «No elimines la trazabilidad histórica ni conviertas un descarte en una aceptación artificial. Conserva las validaciones de permisos, procedencia e integridad existentes.» Example: «un precio detectado por NLP que posteriormente se descarta por utilizar una moneda incompatible.»
- S6: «Ejecuta NLP 0.1.29 sobre las mismas transcripciones que utilizará 0.1.30.» «Ejecuta la versión candidata 0.1.30 sobre entradas idénticas y bajo las mismas condiciones.» «Compara nombres, cantidades, dimensiones, unidades, materiales, espesores, colores, componentes, accesorios, precios, asociaciones y abstenciones.» Corpus: `/home/gabriel/Descargas/HOMEX_Guiones_Evaluacion_Voz`, 120 dictations (79/31/7/3). «La fuente histórica de guiones de referencia es `referencias/guiones_referencia_pregrabacion.jsonl`». «No supongas que cada guion representa exactamente lo pronunciado.» «No vuelvas a ejecutar Whisper para atribuir diferencias al NLP si ya dispones de una transcripción ASR fija.»
- S7: «Calcula precisión, recall y F1 únicamente donde existan referencias suficientemente completas y verificadas.» «Desglosa resultados por categoría y campo.» «Incluye una tabla por identificador de los casos que mejoraron o empeoraron.» «Los 120 dictados son datos de desarrollo, no una evaluación independiente de generalización.»
- S8: «Reproduce los problemas mediante pruebas que fallen antes de aplicar las correcciones y pasen después.» «Ejecuta las pruebas completas de NLP, incluyendo contratos, esquemas, empaquetado, Ruff y controles de integridad.» «Comprueba el comportamiento real del backend y frontend cuando se propongan cambios en contratos, revisiones o atributos.» «Mantén la extracción de observaciones y los límites actuales del asistente de voz fuera de esta intervención, salvo que exista una dependencia funcional inevitable y documentada.»
- S9: «Proporciona un informe técnico breve y verificable» including causes, comparison, specific cases, checks/integrations/CI, files/commits/PR links and limitations. «No introduzcas un modelo NER ni una dependencia pesada sin justificación técnica y necesidad demostrada.»

## Tasks
- T1 [S1,S2,S4,S8] delegated — verified locally; commit pending; catalog naming/context unit; parallel disjoint writer with T3. Commit pending. Risk: item 3 (shared extraction behavior).
- T2 [S3,S8] inline — verified locally; commit pending; generic-furniture commercial sufficiency. Commit pending. Risk: item 3 (shared rules extraction).
- T3 [S5,S8] delegated — verified locally with final wheel; commit pending; isolated Backend worktree `/tmp/homex-backend-commercial-0130`, parallel disjoint writer with T1. Commit pending. Risk: item 3 (consumed review semantics).
- T4 [S6,S7,S9] inline — verified locally; commit pending; frozen-input differential and audited report. Commit pending.
- T5 [S8,S9] inline + delegated verification — pending; release identity 0.1.30, package/integration proof and independent verifier. Commit pending. Risk: item 5 (package delivery).

## Log
- L1: Original user request, verbatim:

```text
# HOMEX — Corrección y mejora del reconocimiento comercial NLP 0.1.30

## Objetivo general

Realizar una revisión técnica y funcional del NLP de HOMEX para corregir posibles regresiones introducidas durante las últimas actualizaciones y mejorar el reconocimiento de productos, muebles y atributos comerciales.

La meta es desarrollar **homex-nlp 0.1.30**, demostrando mediante una evaluación diferencial que su comportamiento es superior al de la versión 0.1.29, especialmente en el reconocimiento correcto de información comercial y la prevención de propuestas injustificadas.

No se busca simplemente aplicar parches. Primero debes comprender las causas, reproducir los problemas y evaluar alternativas. Implementa las soluciones que ofrezcan el mejor equilibrio entre reconocimiento, precisión, cobertura y seguridad comercial.

## 2. Correcciones funcionales prioritarias

### 2.1. Reconocimiento de nombres comerciales fuera del vocabulario conocido

El nuevo filtro `_PRODUCT_CUE` puede descartar nombres implícitos de productos que no contienen alguna de sus palabras reconocidas.

Investiga casos como:

- Espejo decorativo.
- Armario metálico.
- Librero modular.
- Ventana corrediza.
- Otros nombres legítimos no previstos por las reglas actuales.

**Resultado esperado:** reconocer nombres comerciales válidos sin depender de una enumeración cerrada de productos.

Evalúa una estrategia de identificación comercial basada en estructura, contexto y evidencia positiva. Evita resolverlo simplemente ampliando indefinidamente una lista de palabras.

Conserva la capacidad de abstención ante textos que realmente carecen de información comercial.

### 2.2. Reconocimiento de nombres explícitos dentro de oraciones naturales

Revisa `_EXPLICIT_PRODUCT_NAME` y su interacción con el extractor de nombres.

Actualmente puede existir una discrepancia entre detectar un nombre y considerarlo explícitamente válido cuando aparece después de una frase introductoria.

Evalúa ejemplos como:

- «Quiero registrar producto: Espejo Aurora».
- «Necesito agregar un producto llamado Librero Atlas».
- «El nombre comercial es Armario Boreal».
- «Registra un producto nuevo: Organizador Modular».

**Resultado esperado:** interpretar correctamente las formas habituales de expresión de un vendedor, sin obligarlo a comenzar siempre con `nombre:` o `producto:`.

Las referencias al producto, correcciones habladas y delimitaciones entre nombre y características deben seguir siendo coherentes.

### 2.3. Reconocimiento de muebles genéricos con características comerciales

Analiza la condición incorporada en `RulesEngine` y el patrón `_GENERIC_FURNITURE_DETAIL`.

Comprueba si se rechazan descripciones legítimas como:

- «Un mueble de MDF».
- «Un mueble de vidrio».
- «Un mueble con ruedas».
- «Un mueble con iluminación LED».
- «Un mueble con acabado lacado».

**Resultado esperado:** aceptar propuestas parciales cuando exista información comercial suficiente, aunque no se mencionen dimensiones ni precios.

No inventes atributos ausentes. Determina si corresponde generar una propuesta parcial, solicitar revisión o abstenerse según la evidencia disponible.

Evita reemplazar una restricción rígida por otra similar.

### 2.4. Diferenciación entre pruebas de micrófono y nombres comerciales válidos

La versión 0.1.29 eliminó listas negras de expresiones, lo que permite nombres legítimos poco comunes, pero también puede favorecer propuestas originadas en pruebas de audio.

Evalúa expresiones como:

- «Hola, probando el micrófono».
- «Uno, dos, tres, prueba de audio».
- «Producto: prueba de voz».
- «Nombre: prueba».
- «Silla Probando».
- «Nombre comercial: Micrófono Aurora».

**Resultado esperado:** distinguir, hasta donde la evidencia lo permita, una prueba de micrófono de una declaración comercial auténtica.

No utilices prohibiciones globales de palabras como «prueba», «hola» o «micrófono».

Prioriza contexto, intención expresada y suficiencia comercial. Cuando exista ambigüedad real, conserva la posibilidad de revisión humana en lugar de inventar una clasificación segura.

### 2.5. Coherencia entre campos aceptados, evidencias y revisiones humanas

Revisa el tratamiento de `field_reviews`, `evidence` y `fields` en el backend, especialmente en `apps/capturas/catalogo.py`.

Investiga si, al descartar un atributo por validaciones posteriores del backend, pueden mantenerse revisiones humanas que todavía lo presentan como una sugerencia aceptada.

Ejemplo: un precio detectado por NLP que posteriormente se descarta por utilizar una moneda incompatible.

**Resultado esperado:** asegurar que los campos propuestos, sus evidencias, advertencias y revisiones humanas sean coherentes con el resultado final validado.

No elimines la trazabilidad histórica ni conviertas un descarte en una aceptación artificial. Conserva las validaciones de permisos, procedencia e integridad existentes.

## 3. Evaluación con los audios reales de HOMEX

Utiliza el corpus local disponible en:

`/home/gabriel/Descargas/HOMEX_Guiones_Evaluacion_Voz`

Este corpus contiene 120 dictados organizados por categorías:

- 79 muebles a pedido.
- 31 sillas.
- 7 pisos flotantes.
- 3 productos de otras categorías.

Contiene audios AAC, versiones WAV preparadas para ASR y referencias organizadas por identificador. Inspecciona su estructura real, manifiestos, transcripciones y evaluaciones existentes antes de ejecutar procesos.

La fuente histórica de guiones de referencia es `referencias/guiones_referencia_pregrabacion.jsonl`, según la estructura del corpus. No supongas que cada guion representa exactamente lo pronunciado.

**Procedimiento obligatorio:**

1. Recupera las transcripciones ASR existentes y los resultados de evaluación disponibles.
2. Ejecuta NLP 0.1.29 sobre las mismas transcripciones que utilizará 0.1.30.
3. Ejecuta la versión candidata 0.1.30 sobre entradas idénticas y bajo las mismas condiciones.
4. Compara nombres, cantidades, dimensiones, unidades, materiales, espesores, colores, componentes, accesorios, precios, asociaciones y abstenciones.
5. Identifica los casos en que 0.1.30 recupera información antes perdida, mantiene resultados correctos o introduce nuevas regresiones.
6. Utiliza también guiones de referencia como diagnóstico separado. Si existen transcripciones humanas verificadas, úsalas para distinguir errores ASR de errores NLP.
7. Aprovecha las herramientas existentes, especialmente las evaluaciones semánticas y diferenciales del repositorio. Adáptalas solo cuando sea necesario, sin alterar indebidamente las referencias históricas.

No vuelvas a ejecutar Whisper para atribuir diferencias al NLP si ya dispones de una transcripción ASR fija. Puedes hacer evaluaciones adicionales de ASR, pero sus resultados deben informarse por separado.

Los 120 dictados son datos de desarrollo, no una evaluación independiente de generalización. Si existen conjuntos de prueba realmente aislados, respeta esa separación; no presentes una partición creada después de ajustar reglas como una validación independiente.

## 4. Comparación objetiva 0.1.29 vs. 0.1.30

Prepara una evaluación diferencial reproducible, no una simple comparación del número de tests.

Utiliza una matriz como esta:

| Indicador | NLP 0.1.29 | NLP 0.1.30 | Diferencia |
|---|---|---|---|
| Nombres comerciales correctos | Por medir | Por medir | Por calcular |
| Atributos correctos | Por medir | Por medir | Por calcular |
| Atributos válidos omitidos | Por medir | Por medir | Por calcular |
| Valores incorrectos | Por medir | Por medir | Por calcular |
| Propuestas injustificadas | Por medir | Por medir | Por calcular |
| Abstenciones correctas | Por medir | Por medir | Por calcular |
| Asociaciones correctas entre componentes y atributos | Por medir | Por medir | Por calcular |
| Casos sin propuesta | Por medir | Por medir | Por calcular |

Desglosa resultados por categoría y campo.

Calcula precisión, recall y F1 únicamente donde existan referencias suficientemente completas y verificadas. Donde no existan, reporta las coincidencias, omisiones, discrepancias y limitaciones sin inventar métricas.

Incluye una tabla por identificador de los casos que mejoraron o empeoraron. Investiga cada regresión relevante antes de aceptar la versión candidata.

La condición fundamental es **no sacrificar reconocimiento comercial válido para reducir artificialmente las falsas propuestas**, ni aumentar el reconocimiento a costa de inventar información.

## 5. Implementación y pruebas

Una vez identificadas las causas:

1. Diseña la corrección más adecuada dentro de la arquitectura actual basada en reglas y evidencias. No introduzcas un modelo NER ni una dependencia pesada sin justificación técnica y necesidad demostrada.
2. Reproduce los problemas mediante pruebas que fallen antes de aplicar las correcciones y pasen después.
3. Incluye casos positivos, negativos, ambiguos, dictados naturales y nombres comerciales no contemplados previamente.
4. Ejecuta las pruebas completas de NLP, incluyendo contratos, esquemas, empaquetado, Ruff y controles de integridad.
5. Verifica que los cambios no deterioren la interpretación de precios, cantidades, dimensiones, negaciones, rectificaciones, evidencias ni relaciones entre componentes.
6. Comprueba el comportamiento real del backend y frontend cuando se propongan cambios en contratos, revisiones o atributos.
7. Mantén la extracción de observaciones y los límites actuales del asistente de voz fuera de esta intervención, salvo que exista una dependencia funcional inevitable y documentada.
8. No reduzcas validaciones de seguridad, permisos o auditoría, ni modifiques pruebas únicamente para ocultar una regresión.

Si identificas otras deficiencias pequeñas durante la evaluación, corrígelas cuando estén claramente relacionadas con el alcance y puedas demostrar que la modificación aporta una mejora sin efectos negativos.

## 8. Entrega final

Proporciona un informe técnico breve y verificable que incluya:

1. Causas reales de los cinco hallazgos y correcciones implementadas.
2. Tabla comparativa de resultados 0.1.29 vs. 0.1.30.
3. Casos específicos que mejoraron, permanecieron iguales o empeoraron.
4. Resultados de pruebas, contratos, integraciones y CI.
5. Archivos modificados, commits y enlaces a los PR que correspondan.
6. Limitaciones y riesgos pendientes, si existen.

**Prioridad final:** que el NLP de HOMEX comprenda mejor los dictados comerciales reales, conserve la información útil, reduzca rechazos injustificados y evite atribuir al vendedor información que nunca proporcionó.

El objetivo no es tener más reglas o más pruebas aprobadas, sino **obtener un reconocimiento comercial más confiable y demostrarlo con evidencia comparativa**.
```

- L2: User delivery decision verbatim: “cadena sobre una rama de funcionalidad —integración conjunta al terminar—”. Accepted feature-branch-chain; no push, release, PR creation or merge yet authorized with destination and credentials.
- L3: Baselines: NLP `5fa4ace` has tracked pyproject version 0.1.29; Backend `50a55f9` main, original checkout has pre-existing untracked celerybeat-schedule.db left untouched. Source snapshots, not an unverified release tag, will identify the differential baseline. Existing semantic evaluator defaults to b851b5a and must not be mislabeled 0.1.29. RDD is off by explicit global setting; no native review will start.
- L4: Parallel writers justified by independent catalog context and Backend postvalidation behaviors with disjoint edit surfaces. Parent owns git and evaluation/furniture changes. Configured explorer model unavailable in live tool list; read-only explorer used inherited runtime model. Workers use the available configured gpt-6.1-sol/medium.

- L5: Naming RED 15 failures then focused222 passed; generic furniture RED8 failures then65 passed. Full NLP first exposed three repeated-nonsense regressions; six additional sentence-fragment RED probes led to productive descriptor/proper-name evidence rather than accepting any two words. Final functional suite1266 passed. Reporting predicates add4 tests (no earlier runnable reporter behavior; direct expected-output checks used).
- L6: Existing frozen evaluator ran14 cells (original+5 previously saved ASR variants+script control, two NLP versions): original549/1000 supported matches and7 no proposals unchanged, zero commercial payload deltas/120. Directed development oracle: names4/17→17/17; required ambiguity reviews0/2→2/2; all scoped expectations10/25→25/25; eight negative abstentions retained. No acoustic precision/recall/F1/association accuracy asserted. Evidence: corpus evaluaciones/commercial-0130-v1/.
- L7: Backend RED4 failures, focused16 passed, full758 passed using installed0.1.29; Frontend voice-review8 passed, no tracked edits. Final0.1.30 ordinary installed-wheel consumer uses external venv, original dependency environment read-only; final full suite and independent verification next. RDD off respected. Baseline vendor wheel source members exactly match NLP5fa4ace.

- L8: Independent verification found one new negative-MDF false proposal and natural explicit correction/material/feature boundary errors. Five exact verifier probes observed RED (5fail), one correction batch applied, then257focused passed and1275full NLP passed. Rebuilt ordinary wheel SHA784bf4bac0e0602cb70cdc2410c3e716d27d9fd2f5d02c3c9237603cd3ac3955. Frozen evaluation regenerated at corpus evaluaciones/commercial-0130-v2/, still zero original120deltas and same25probe gains.
- L9: Actual0.1.30 Backend consumer exposed strict0.1.29 package guards (204fail/13errors). T5 includes coordinated dependency/lock/vendor/exact guard/hash and operational identity expectations; old wheel retained. Rejection warning coherence added after actual API probe: one RED failure then5focused passed, removing only replaced review messages, not historical evidence. Final full corrected-consumer run pending.

- L10: Corrected final installed-wheel Backend758passed, nofailures/errors/skips/warnings; all32installedfiles match vendorwheel. Ruff/Django/offlinelockpassed. Independent targeted recheck cleared previouslyreported5cases; actual Backendpayload exercised in scratchFrontend test1passed with noUSDautofill, rejectionmessage and stableIDs/nulloriginalaudit. Frontend remainedunchanged. NLP1275passed; packagefinalproof and localchainedcommits next.
