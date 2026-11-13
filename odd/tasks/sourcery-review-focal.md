# Evidence-led correction of the ten engine review observations
Branches: existing feat/real-voice-120-results, feat/real-voice-120-semantic and fix/real-voice-120-f09. Delivery: existing original PRs only; no auxiliary PR merge, main merge, deployment or historical deletion.
Runners: locked Python3.11/pytest/Ruff, installed wheels and actual three-repository integration. Single-branch delivery is explicitly required; forecast ~1400 authored lines excluding generated evidence. New private evidence: corpus evaluaciones/sourcery-review-v1 and logs/sourcery-review-v1.

## Specs
- S0: "Antes de hacer cambios, consulta el estado actualizado de las ramas, los commits, las diferencias respecto a `main`, los PR, las CI y los archivos locales." Preserve other local work and the latest frontend changes.
- S1: "Cada observación debe reproducirse, analizarse y clasificarse antes de modificar código." Investigate all ten actual PR45 comments, not merely the paraphrases; no runtime changes before the initial classification ledger exists.
- S2: "Comprueba el rendimiento mediante entradas controladas de distintas longitudes y cantidades de accesorios." Context-local scanning and contract bounds only when justified; preserve legitimate commercial input.
- S3: "No suprimas menciones independientes por encontrar una coma o una descripción similar." "Escritorio con casillero" and "Escritorio con una cajonera" must preserve explicit composition without inventing independent lines; independent orders and genuine ambiguity remain reviewable.
- S4: "Ancho 60 cm alto 75 cm"; "Alto 180 cm ancho 80 cm"; "Armario alto de 80 cm de ancho"; "Largo 150 cm, ancho 60 cm y alto 75 cm". Preserve explicit dimensions and units without adjective/axis misassociation.
- S5: "No conviertas importes monetarios en cantidades de accesorios." "Veinte escritorios, no, mejor veinticinco" and the other specified compound corrections must not retain superseded quantities; different products remain ambiguous.
- S6: "No modifiques el versionado si los valores ya son coherentes." Distinguish official distribution identity, stale development environments and auxiliary PR omissions. "No reutilices el número de versión `0.1.23` para un paquete con contenido distinto."
- S7: "Modelo B O dos"; "Código B O 2"; "Modelo B o modelo C"; "Modelo B, o mejor C". Distinguish code letters, alternatives and ordinary prepositions without invented codes.
- S8: "Ejecuta nuevamente las evaluaciones de los 120 audios con el ASR original congelado." Compare per-case/category/field against historical549/1000 and7 abstentions, never overwrite history or claim acoustic/commercial gold or independent generalization.
- S9: "Ejecuta la integración utilizando exactamente los HEAD finales de NLP, backend y frontend." Installed-wheel identity, PostgreSQL/migrations, Redis/Celery, Whisper/audio, proposal/HITL/persistence/BORRADOR, permissions, OpenAPI, E2E/a11y/lint/types/build/security; exact commit-bound evidence, no source substitution.
- S10: "Los PR #44 y #45 son auxiliares de revisión y **nunca deben fusionarse**." Update existing original PR43/60/68 with actual classifications, fixes, tests, metrics, distributions, compatibility, CI, risks and pending decisions. No merge/deploy/force-push/history deletion; preserve .atl untracked.

## Tasks
- T0 [S0,S1,S6] inline Git/remote state + delegated read-only ten-observation reproduction (mapping trigger: unfamiliar flow exceeds bounded evidence batch); COMPLETEinitialclassificationbeforecode; baseline62127a9/9cc380f/ffa2495; officialinstalled.23proof26modules.
- T1 [S2,S4,S5] delegated parallel furniture writer; COMPLETE8d051d5+ff430668; RED/GREEN and independent1053PASS; no uncorrected demonstrated semantic blocker.
- T2 [S3,S7] focal relations/catalogue behavior after classification, test-first and no ID conditions; delegated parallel catalogue01e8986 and furniture8d051d5; source1051PASS, S4reopenedafterfrozencomparison.
- T3 [S8] delegated execution; COMPLETEcomparison-v2/1680outputs/0errors, original520/1000/13 vs549/1000/7, six conservative losses explicitly reviewed; no human-gold claim.
- T4 [S6,S9] new distribution only if code changes, installed backend exact wheel, final-head three-repository integration; delegated long verification and Risk3/5 independent verification; PENDING.
- T5 [S9,S10] sanitized report/index, normal pushes, update original PRs, final branch/PR CI and exact final-head compatibility; PENDING.

## Log
### L1 User request (verbatim)
## Objetivo

Realizar una intervención técnica focalizada para investigar y resolver los hallazgos de la revisión de código del motor NLP, eliminar regresiones comerciales demostradas y comprobar nuevamente la compatibilidad entre los tres repositorios de HOMEX.

Debes completar autónomamente el diagnóstico, implementar las correcciones justificadas, ejecutar las pruebas correspondientes, publicar los commits en las ramas existentes y verificar las CI.

**No fusiones a `main`, no despliegues producción y no modifiques ni elimines las evidencias históricas del corpus.**

## 1. Contexto y referencias

### Repositorios y ramas

**NLP**

- Repositorio: `gabriel-arinez/homex-nlp`
- Rama: `feat/real-voice-120-results`
- Commit inicial de referencia: `62127a92d0b310127feb803e807f28adecee16f8`
- PR original: https://github.com/gabriel-arinez/homex-nlp/pull/43
- PR auxiliar de revisión funcional: https://github.com/gabriel-arinez/homex-nlp/pull/44
- PR auxiliar de revisión del motor: https://github.com/gabriel-arinez/homex-nlp/pull/45

**Backend**

- Repositorio: `gabriel-arinez/homex-backend`
- Rama: `feat/real-voice-120-semantic`
- Commit inicial de referencia: `9cc380f1537f773606ff88c8a435dfeacca5990f`
- PR: https://github.com/gabriel-arinez/homex-backend/pull/60

**Frontend**

- Repositorio: `gabriel-arinez/homex-frontend`
- Rama: `fix/real-voice-120-f09`
- Último commit publicado de referencia: `ffa24959dab98004d004ac60c874d27364c0c84c`
- PR: https://github.com/gabriel-arinez/homex-frontend/pull/68

Antes de hacer cambios, consulta el estado actualizado de las ramas, los commits, las diferencias respecto a `main`, los PR, las CI y los archivos locales.

No presupongas que estas revisiones siguen siendo los HEAD actuales.

## 2. Diagnóstico obligatorio de las observaciones de Sourcery

Consulta los diez comentarios publicados en el PR auxiliar #45.

**Cada observación debe reproducirse, analizarse y clasificarse antes de modificar código.**

Clasificaciones permitidas:

- Defecto confirmado.
- Defecto parcialmente confirmado.
- Falso positivo de la revisión automática.
- Comportamiento conservador intencional.
- Pendiente por falta de evidencia suficiente.

No des por correctas las observaciones únicamente porque las emitió Sourcery.

### Observación 1 — Rendimiento con transcripciones extensas

Archivo: `src/homex_nlp/rules.py`, alrededor de la línea 1012.

Investiga si `find_accessory_quantity` realiza búsquedas repetidas sobre prefijos crecientes y provoca degradación significativa cuando aparecen muchos accesorios.

Comprueba el rendimiento mediante entradas controladas de distintas longitudes y cantidades de accesorios.

Si se confirma, limita el análisis al contexto local necesario y aplica límites de entrada apropiados en la frontera del contrato, sin rechazar transcripciones comerciales legítimas.

Incluye pruebas de comportamiento y rendimiento reproducibles.

### Observación 2 — Fusión incorrecta de productos independientes

Archivo: `src/homex_nlp/product_relations.py`.

Evalúa expresiones como:

- «mesa, mesa de madera»
- «escritorio con cajonera, cajonera de madera»
- «dos mesas, una de madera y otra metálica»

Determina cuándo una segunda mención es una referencia al producto original y cuándo representa otro producto comercial independiente.

No suprimas menciones independientes por encontrar una coma o una descripción similar.

Ante ambigüedad real, conserva la evidencia y solicita revisión en lugar de producir una asociación inventada.

### Observación 3 — Pérdida del componente casillero

Archivos:

- `src/homex_nlp/engine.py`
- `src/homex_nlp/semantics.py`

Reproduce el comportamiento de:

«Escritorio con casillero».

Comprueba si el motor elimina el casillero como producto sin conservarlo como componente.

Si se confirma, corrige la extracción para que el componente permanezca asociado al escritorio, con su evidencia correspondiente.

No debe convertirse automáticamente en una segunda línea comercial.

### Observación 4 — Cajonera tratada como producto independiente

Archivo: `src/homex_nlp/product_relations.py`.

Investiga expresiones como:

- «Escritorio con una cajonera».
- «Escritorio con dos cajoneras».
- «Escritorio y una cajonera independiente».
- «Escritorio con cajonera integrada».

Distingue las relaciones de composición de los productos comerciales independientes.

Corrige las condiciones relacionadas con artículos y determinantes únicamente cuando se demuestre que provocan una clasificación incorrecta.

### Observación 5 — Descarte de dimensiones explícitas

Archivo: `src/homex_nlp/rules.py`, alrededor de la línea 907.

**Prioridad alta.**

Comprueba especialmente:

- «Ancho 60 cm alto 75 cm».
- «Alto 180 cm ancho 80 cm».
- «Armario alto de 80 cm de ancho».
- «Largo 150 cm, ancho 60 cm y alto 75 cm».

Investiga si la regla que evita confundir adjetivos con ejes de medidas elimina dimensiones legítimas.

La corrección debe conservar las medidas explícitas y sus unidades sin reintroducir errores de asociación de ejes.

Añade pruebas de regresión para ambos comportamientos.

### Observación 6 — Precios interpretados como cantidades de accesorios

Archivo: `src/homex_nlp/rules.py`.

Comprueba expresiones como:

- «USB a 20 bolivianos».
- «Dos puertos USB».
- «USB, 2 unidades».
- «USB a 20».
- «Cuatro conectores HDMI a 30 bolivianos cada uno».

No conviertas importes monetarios en cantidades de accesorios.

Cuando el contexto sea ambiguo, conserva el valor sin asignarlo automáticamente.

### Observación 7 — Rectificaciones con números compuestos

Archivos:

- `src/homex_nlp/rules.py`
- `src/homex_nlp/semantics.py`
- `src/homex_nlp/engine.py`

Comprueba expresiones como:

- «Veinte escritorios, no, mejor veinticinco».
- «Treinta cajones, corrijo, mejor treinta y dos».
- «Doce mesas, perdón, mejor quince».
- «Diez mesas, no, veinte escritorios».

Distingue las correcciones inequívocas de las frases que introducen productos diferentes o nuevas ambigüedades.

Evita conservar cantidades anteriores cuando existe una rectificación explícita y válida.

### Observación 8 — Versionado inconsistente

La revisión automática afirmó que el proyecto conservaba la versión `0.1.21`.

Sin embargo, en el PR original se verificó:

`pyproject.toml → version = "0.1.23"`

Por tanto, **esta observación parece un falso positivo derivado del PR auxiliar**, que no contiene todos los archivos del repositorio original.

Verifica la versión instalada, los metadatos del wheel, `__version__`, el manifiesto de publicación y la versión consumida por backend.

No modifiques el versionado si los valores ya son coherentes.

### Observación 9 — Letra O en códigos dictados

Archivo: `src/homex_nlp/catalog.py`.

Comprueba expresiones como:

- «Modelo B O dos».
- «Código B O 2».
- «Modelo B o modelo C».
- «Modelo B, o mejor C».

Distingue la letra O pronunciada de una conjunción disyuntiva.

No conviertas una alternativa entre modelos en un código único ni inventes una interpretación cuando exista ambigüedad.

### Observación 10 — Falsas advertencias de códigos ambiguos

Archivo: `src/homex_nlp/catalog.py`.

Comprueba si las preposiciones «a» y «de» producen falsos intentos de decodificación de códigos hablados.

Evalúa descripciones comerciales ordinarias, códigos genuinamente deletreados y entradas incompletas.

La ausencia de un código debe diferenciarse de un código existente pero ambiguo.

## 3. Reglas para implementar las correcciones

Antes de modificar cada comportamiento:

1. Reproduce el defecto mediante una prueba que falle.
2. Identifica la causa raíz exacta.
3. Comprueba los casos históricos relacionados.
4. Implementa la corrección mínima y generalizable.
5. Ejecuta la nueva prueba y las regresiones existentes.
6. Comprueba que no se hayan introducido falsos positivos.
7. Documenta el resultado y su evidencia.

No añadas reglas basadas en identificadores específicos como `MP-0007`, `MP-0048` o cualquier otro ID del corpus.

No elimines validaciones ni mecanismos de abstención para aumentar las cifras de aciertos.

**Una extracción comercial incorrecta es más perjudicial que una solicitud de revisión humana.**

## 4. Conservación de los resultados anteriores

La evaluación anterior registró:

- Coincidencias escalares contra guion: `549/1000`.
- Casos sin propuesta: `7`.
- Distribución NLP instalada: `0.1.23`.

Estos resultados son referencias históricas, no objetivos que deban mantenerse a cualquier costo.

Después de las correcciones:

- Ejecuta nuevamente las evaluaciones de los 120 audios con el ASR original congelado.
- Compara resultados por caso, categoría y campo.
- Identifica recuperaciones, pérdidas y valores nuevos.
- Investiga cualquier regresión.
- Distingue los cambios legítimos que eliminan falsos positivos de las pérdidas reales.
- Conserva los informes anteriores sin sobrescribirlos.

No declares precisión comercial integral ni generalización a partir del corpus de desarrollo.

## 5. Versionado y distribución del NLP

Si las correcciones modifican los archivos del paquete NLP, genera una nueva distribución siguiendo el procedimiento de publicación real del proyecto.

Verifica:

- Versión del paquete.
- Metadatos de distribución.
- Contenido efectivo del wheel.
- Hash SHA-256.
- Integridad de los archivos.
- Compatibilidad del contrato público.
- Pruebas desde la distribución instalada, no desde las fuentes del repositorio.

Actualiza el backend para consumir exactamente la distribución nueva.

Conserva los wheels anteriores y su evidencia histórica.

No reutilices el número de versión `0.1.23` para un paquete con contenido distinto.

## 6. Backend y frontend

Verifica los cambios del NLP desde sus consumidores reales.

Presta especial atención a:

- Conservación de medidas asociadas a componentes.
- Cantidades y precios explícitos.
- Campos comerciales ambiguos.
- Propuestas con varios productos.
- Confirmación humana.
- Persistencia de la proforma en BORRADOR.
- Contratos OpenAPI.
- Validación de permisos y estados.

No modifiques la interfaz o el backend si no existe un defecto comprobado o un cambio contractual indispensable.

### Estado reciente del frontend

La rama `fix/real-voice-120-f09` incorporó el commit `ffa24959dab98004d004ac60c874d27364c0c84c`.

Esta corrección modifica únicamente una prueba de integración: cuando Whisper no extrae una cantidad conocida de la grabación controlada, el operador simulado completa manualmente el campo antes de confirmar.

Comprueba las CI asociadas a este commit y conserva las validaciones comerciales existentes.

Si las pruebas continúan fallando, investiga sus registros y evidencias reales. No desactives escenarios ni introduzcas esperas arbitrarias para ocultar fallos.

## 7. Compatibilidad cruzada definitiva

Después de publicar las correcciones:

Ejecuta la integración utilizando exactamente los HEAD finales de NLP, backend y frontend.

La comprobación debe abarcar:

- Identidad del wheel instalado.
- Contratos OpenAPI.
- PostgreSQL y migraciones.
- Redis y Celery.
- Procesamiento de audio con Whisper.
- Extracción NLP.
- Revisión de propuestas.
- Confirmación humana.
- Guardado comercial.
- Pruebas E2E.
- Accesibilidad.
- Lint, tipos y build.
- Seguridad de dependencias y secretos.

No utilices únicamente revisiones anteriores que hayan aprobado.

Todos los resultados deben estar asociados a hashes de commit verificables.

## 8. Pull Requests

Los PR originales de integración son:

- NLP #43.
- Backend #60.
- Frontend #68.

Los PR #44 y #45 son auxiliares de revisión y **nunca deben fusionarse**.

Publica las correcciones en las ramas originales correspondientes.

Actualiza los PR con:

- Lista de observaciones investigadas.
- Defectos confirmados y corregidos.
- Falsos positivos descartados con evidencia.
- Pruebas añadidas.
- Métricas anteriores y actuales.
- Versiones y hashes de distribución.
- Compatibilidad cruzada.
- CI definitivas.
- Riesgos y decisiones pendientes.

Si Sourcery produce nuevas observaciones, analízalas con el mismo criterio de reproducción y evidencia.

## 9. Restricciones

- No fusionar a `main`.
- No desplegar producción.
- No borrar ni reescribir el historial Git.
- No eliminar las evidencias históricas.
- No modificar los audios originales.
- No publicar datos comerciales privados adicionales.
- No introducir cambios innecesarios en arquitectura.
- No relajar validaciones comerciales.
- No deshabilitar pruebas para obtener CI verde.
- No usar force-push ni operaciones Git destructivas.
- Mantener las ramas originales de integración.
- Conservar los archivos locales `.atl` sin incorporarlos a producción.

La revisión acústica humana de los 120 audios continúa pendiente.

La política de privacidad, la limpieza de evidencias y la eventual conversión de repositorios a privados quedan expresamente pospuestas para el cierre del sistema.

## 10. Entregables y cierre

Al concluir, proporciona un informe verificable que contenga:

1. Diagnóstico individual de las diez observaciones.
2. Evidencias que confirman o descartan cada defecto.
3. Relación de correcciones implementadas.
4. Pruebas nuevas y regresiones ejecutadas.
5. Comparación actualizada de los 120 casos.
6. Versión y hash del nuevo paquete NLP, si corresponde.
7. Estado de los consumidores backend y frontend.
8. Resultados completos de CI.
9. Verificación cruzada de los HEAD finales.
10. Commits publicados en cada repositorio.
11. Estado de los PR originales.
12. Limitaciones y pendientes reales.

### Criterio de finalización

La intervención técnica podrá considerarse cerrada cuando:

- Las diez observaciones estén investigadas y clasificadas.
- Todos los defectos confirmados estén corregidos.
- No existan regresiones comerciales injustificadas.
- Las distribuciones y contratos sean coherentes.
- Las pruebas cruzadas de los HEAD finales estén aprobadas.
- Las CI de las ramas y PR estén verdes.
- Los cambios estén publicados y documentados.

**No declares cerrada la tarea si queda un fallo técnico confirmado sin resolver.**

Puedes utilizar las herramientas, ejecutar comandos y realizar commits necesarios para completar la intervención de forma autónoma.

No te detengas después del diagnóstico: continúa hasta implementar y verificar las correcciones que estén respaldadas por evidencia.

**Entrega los tres PR preparados para su revisión final, sin fusionarlos ni desplegarlos.**

### L2 Initial verified state
All requested remote original heads match62127a9/9cc380f/ffa2495; original PR43/60/68 are open/mergeable with green checks (push and PR checks both present). Auxiliary44 green, auxiliary45 package/rules-only fail because it is a partial engine-only review, never an integration candidate. Exactly10Sourcery inline comments fetched. LocalNLP clean except .atl; backend controlled clean; frontend controlled fast-forwarded froma8e1656 toffa2495 without overwriting changes: intervening theme/peer-ref updates preserved plus the3line test-only HITL quantity completion. RDD remains globalOFF. Main comparison fullnumstat stored privately; NLP historical huge evidence diff is preserved, no splitting/removal under the explicit original-branch requirement.

### L3 Initial classifications and focal units
AlltenactualSourcerycomments IDs4563997761–4563997856 fetched;41publicreplays+bounded3repeatperformancebaseline savedbeforecode. Confirmed1/2/3/4/5/7/10; partial6(priceexamplesalreadyabstainbutUSBcomma2unidadesmissescount),9(Oletterversusalternatives);8falsepositivecanonical.23coherent. SILLA/PISO modelscupported, OTROdoesnotextractmodel; initialOTROwrongprobeclassificationcorrectedbeforecode. Rooteditablemetadata.22staleenvironmentnotpublishedmismatch; privateordinaryinstalled.23metadata/runtime26modulebytesmatchdebaewheel. Diagnosticwriterinitiallyusedwrongrelativedirs; parentcopiedbyte-identicalscript+JSONtonewcorpusabsoluteeval/logdirs, removedonlyownemptyaccidentalfolders.
Parallelwriters withdisjointsurfaces: catalogue01e8986 (41newtests,related123PASS); furniture8d051d5(32newtests+2contractbounds;16RED16PASS→142focusedPASS,577sharedPASS). Parentseam1051PASS4.3s/Ruffsrc-tests-toolsPASS. Structural20kinputcap<=31xhighest645charcorpusreference; backendHTTPJSON/multipartboundary2RED2PASS→4GREEN, noqueue/persistenceortruncationonreject. Compoundstrictcounts, scopedcomponents, adjective/axisguard andmodelsnoIDconditions. Independentfrozen8dall1051PASS afterrestoringtracked1.8MB/datafixtures; firstscratchomissionfailurepreservednotclaimedruntimefailure. NativeassessreportedhighRisk3withuntrackedinventoryerror; RDDglobalOFF, no reviewlifecycle orloweredtier; independentfunctionalverifycompleted.
### L4 Full comparison catches real dimension regressions
Newcomparison-v1:14x120=1680outputs,0executionerrors, historicaloriginal549/1000/7reproduced; candidate520/1000/13. All29originalscalar-matchlossesfromsixbare-commaabstentions MP0022/0023/0026/0050/0051/0055, noexplicitdefinite/coreferentialcues; scriptcontrols549/1000/7unchanged. Fitsuserconservativecomma-policybutNOautomaticcommercialsafetyclaim/verifiedgold. Rawfull39behavior/evidencepairs,nineIDs retained; full1087=supported1000+87unsupportedunmatchedtuples.
ActualcandidateVADcases reveal2CONFIRMEDS4blockers hiddenbyscalarmatches: Armarioalto80cmdeancho50deprofundidad addswrongalto80/ancho50; Mesa3metros20delargo1metro30deancho addswroonglargo1m. Sourcefurniturecorrectionbatchreopenedonlyrules/tests/doc, REDfirstcompleteexpectedsets; fullcomparison-v2mustfollowbeforepromotion.
### L5 Unpublished release candidate preserved
.24v1preparedbecauseactualruntimefixes, NOTbecausefalsepositiveversion8. Twoepoch0buildsidentical,1051sourcePASS/RuffcanonicalPASS/26installedmodulebytes/privateF10profilesPASS. Wheel730cb3ec98abfa29d9dc0bfc57f9352120107ae98c8f8f585e18759630c452ac, sdist0426b797cba27d832dfd29dcf1059fb64b43f592a6ef6f86b36c11a7704dce43 areUNPUBLISHEDINTERMEDIATEONLY, NOTTOvendor. Allold.23andearlierartifacts preserved. Sourcefixrequires.24v2rebuildwithnewhashes; .24hasneverbeenpublished. BroadRuff338preexistingarchivalerrorspreserved, notedited. PrivateownedPG16+Redisallocatedfortestsat/tmp/homex-sourcery-runtime.R51JcH; randomsecretprivateonly, originalenvnevermutated. Consumer.24pinnotyetupdated; T4/T5remainpending.

### L6 Targeted dimension correction and frozen v2
S4singleboundedcorrection ff430668 addscomplete-setregressionsforbothconfirmedpostfix-prefixleaks, RED2→GREEN248related/parent34focalPASS. Independentff77focused/1053unfilteredPASS, sourceoffsets retained. Runtimeversion.24v2newsource10e551a preparedonlyafterprivate.24v1bytepreservation. FinalUNPUBLISHEDwheel12d1dab78a5e1ea04780e0e3345e1885cc5dc9edf5c7b2aa1b989f8349379ec6,sdist663d06b3043c91853efb919084447d6265020e1476a25634916e9db26450f560, runtime26digestddb222fda63f8d05b4e3bae4abc17e002ef2ad2af293e7417a2071791f49e544. Twoepoch0buildsidentical,1053PASS/RuffcanonicalPASS/26installedsource-wheelbytesPASS; historical.23andearlierunchanged. No .24candidatewaspublishedyet.
Comparison-v2all1680/14cells/0errorsstablesource-wheel; original520/1000/13 vsbaseline549/1000/7,script549/1000/7unchanged. Allseveninputheadlinecountsunchangedvsv1; exactly3pairs remove4incorrectdimensionvalues,0newpredictions: twointroducedVADcasesandwider-beamMP0053preexistingancho1mleak. Initialexpectexactly2changedpairsassertionfailed,preserved; investigatedthirdsameclassoldbugfixratherthanhideit. All840baselineoutputsunchangedexcludelatency. No acousticgold/precision/safetygainclaimforthesixbarecommaabstentions.
### L7 Consumer package and input boundary
Backendboundarycommit6fc7369 adds20ktextvalidationbeforequeue JSON/multipart/OpenAPIand4tests,2RED2PASS→4GREENacceptedrawunchanged/nopersistencereject. Privateordinary.24v2installnowactual26runtimecandidate, operativeadapter/dependencylock/F084wheelguard updatedlocally; old.23vendorandF08guards preserved. New17adapter/runtime+5bodyboundarytests22PASS5.62s; uvlockcheck104packagesPASS. Version.24RED3FAIL14PASSonoldinstalled.23preserved. Sourcebackendfull/independentrelease+consumerverificationrunningonownedPG16/Redis, parentnolongerDBtestsconcurrent. OriginalfrontendFFffa2495theme/CIrefs/manualquantitytestunchanged; onlygeneratedschema/peerupdatesplanned. T4/T5pendingconsumerfull/finalheadlive/remoteCI/PRupdates.

### L8 Final package and consumer candidates
StandaloneNEWbenchmarkCLI initiallyignored--help/unknownflags; parentobservedRED2FAIL1PASS thenstdlibargparse+public3testsGREEN, defaultJSONretained; commit888e1ac. No runtime31packagedfilechanges. Finalpackagingv3wheel remains12d1dab78a5e1ea04780e0e3345e1885cc5dc9edf5c7b2aa1b989f8349379ec6,sdistff74aa3492439ce9a10556c93fc3f099ac78c1e6b4e91cd73196c475cf5bb053;1056fullPASS,doublebuild,privacy/AAC/schema/history/lock/26modulefreshordinaryinstallPASS. V1/v2unpublishedcandidatespreserved. Independentfinalreadbackall31filesmatchsource/wheel/install,42/42historicalhashesPASS; nodefaultconfig/APIboundaryweakening.
Backendcurrent302bbb13246988c433f496d508af48ce84b3c846: source6fc7369inputcap+9c2661a95a142d57782772956a70e7fac382fc64exact.24wheel,CIonlyfinalfrontendc057peer. Independentfullbackend569PASS172.5s/Ruff/format/lock104PASS, parent22focusedPASS. Actualordinary.24privateimport26modulebytes source-wheel-match. Frontcurrentc0578c074f6942aec5758a5dfbab4b0d5d360a01, exact4metadatafilesonlyfromffa2495; other330filesapplication/styles/tests/generatedTSunchanged, manualquantityfallbackpreserved. Static309PASS/types/lint/format/build/codegenPASS. OpenAPIbytecmpmatchesbackend,3maxLengthdeclarationsonly. Frontdefaultbackend9c remainsapplication-identicaltofinal302; finalworkflow_dispatchwilloverridebothpeerHEADsexactly.
Newpublicsanitizedcase-index/classification/metrics/report containsnoextra privateoriginaldictation/proforma/audio, allfullrawprivate. Privateoffline review-v1 regenerated120/categories73-27-7-13/zero decisions/audiohashbeforeafterPASS fromcurrent.24outputs; nothumanlistening. FinalNLPsource/docscandidatewillbepublishedwith originalbranches,thenexact-headlive+CI+PRupdates. T4/T5notclosedbeforethatproof. RDDglobalOFF.
