# Commercial adjudication and focused correction of120 voice cases
Branch: feat/real-voice-120-results; baseline19d16ff0a428d765b7e89d3b695c02e5ce264b50. Delivery: existing single feature branches, no PR creation/merge/deploy/history deletion; PR recommendations only.
Artifacts: corpus evaluaciones/commercial-review-v1 and logs/commercial-review-v1, new directories only. Runners: Python3.11/pytest/Ruff, actual installed wheels, browser probes. Forecast ~1800 authored lines; existing generated evidence excluded; prior single-branch preference retained, no code-golf.

## Specs
- S0: "No presupongas que los HEAD o los resultados de CI siguen siendo los mismos." Inspect all3branch states, contracts, versions, logs and local changes; preserve original120recordings, historicalresults and73/27/7/13classification.
- S1: "Construye una matriz de los 120 casos que permita revisar:" Include all requested source/audio/script/ASR/provenance, commercial fields/associations, warnings, unsupported fields, old/current NLP and per-datum validation states.
- S2: "Debe permitir escuchar cada grabación original, consultar su guion, observar la transcripción del ASR y comparar visualmente los campos comerciales." Local-only utility; prioritized differences, explicit human uncertainty/decisions and structured versionable export separate from originals. "Un dato no debe marcarse como verificado por escucha simplemente porque coincide con el guion o porque varios modelos producen el mismo resultado."
- S3: "MP-0003, MP-0008, MP-0012, MP-0017, MP-0022, MP-0026, MP-0037, MP-0051, MP-0057, MP-0060, MP-0061, MP-0065, MP-0066, MP-0070, MP-0071, MP-0072 y MP-0074." Diagnose each originalASR+script execution, primary product/component/reference evidence, legitimate abstention versus bug; generalizable tests/fixes, no ID conditions.
- S4: "Para cada defecto, conserva el ejemplo original, la causa raíz, la prueba fallida, la corrección y la prueba aprobada." Prioritize commercial money, dimensions, quantity, product/component, catalogue and unrecoverable ASR; no broad refactor without evidence.
- S5: "Conserva la línea base histórica y realiza nuevas evaluaciones sin sobrescribir resultados anteriores." At least originalASR×old/newNLP and script×old/newNLP; candidates only when justified; correct/missing/incorrect/additional/ambiguous/unverifiable separated. "No presentes las coincidencias escalares como precisión comercial integral."
- S6: "Si una decisión humana es indispensable para establecer la verdad de un caso, deja preparada la evidencia, registra el bloqueo y continúa con los defectos independientes que sí puedan corregirse." Human/audio statuses defaultPENDIENTE; no inferred listening or invented generalization;120areDEVELOPMENT. New independent linguistic probes, independent audio only if genuinely available.
- S7: "Comprueba los consumidores reales sin utilizar sustituciones de código fuente que oculten diferencias con la distribución instalada." If NLP changes require newwheel, preserveoldartifacts/hashes, verify all3effectiveconsumers/contracts/unit/lint/build/integration/CI and classify regressions/abstentions.
- S8: "Revisa los 8.293 archivos de la rama NLP y el volumen de evidencias publicadas." Classify necessary/historical/voluminous, verify sanitization, no versioned deletion/history rewrite, unique current-state index; preserve untracked.atl without publishing.
- S9: "Recomendación documentada para los tres PR." Publish only sanitized necessary evidence; report technical fixes/pending/legitimateabstentions/acousticpending/verifiableprecision/PR-readiness separately. "No fusiones a `main`, no despliegues producción y no elimines material histórico sin autorización."

## Tasks
- T0 [S0,S8] inline bounded state verification plus delegated read-only mapping for unfamiliar corpus/17case flow; DONEinitial:3remoteheads/CI unchangedgreen19d16ff/850c250/7b83694;8293trackedfiles/8064audit; root.atl and originalbackendunknowncelerybeat-schedule.db preserved. Commitpending.
- T1 [S1,S2,S6] delegated writer: local review utility/matrix + tests/docs. Reasonparallelism with independentT2NLPbehavior; disjoint tools/review_commercial_voice.py,tools/commercial_review_ui/**,tests/evaluation/test_commercial_review.py,docs/commercial-voice-review.md. No productionconnector or automaticacoustictruth. COMPLETEtool5tests/browser120readonly/240hashes, independentPASS; commitbc75868.
- T2 [S3,S4] delegated writer: independent17caseproductrelationbehavior, baselinefreeze before sourceedits. Reasonparallelism withT1; disjoint engine.py,product_relations.py,rules.py,newunitregression/newdoc. Preserve legitimateabstentions andconservativeevidence. COMPLETE10originalrecoveries/7retained;325reruns+1680fullcomparison,928tests+independentPASS; commit81caa3c.
- T3 [S4,S5,S6] inline focused value fixes in rules.py + new tests/unit/test_commercial_values_v3.py/docs/real-voice-commercial-values.md; confirmed prefixwordquantity and fusedexplicitunitprice misses, independentheightmap pending. REDbeforechange; keepgeneric/ambiguousmoney andmissingunitsunresolved. COMPLETEvalues37newprobes,full965PASSandindependentPASS;commitc7bc2b6.
- T4 [S7] delegated release writer in parallel with independentparentT5publication-inventory/PRdocs: new0.1.23neededforverifiedcorechanges, preserve0.1.22artifacts/hash, deterministicwheel/sdist/installedproof. Exactallowedmetadata/privacychecks only; consumersparentlater afterwheel. NamedRisks2,5. COMPLETEvalues37newprobes,full965PASSandindependentPASS;commitc7bc2b6.
- T5 [S8,S9] publication inventory/privacy review, unique current-state index, quantitative final matrix,3PRrecommendations and safe branch publication. No actualPRcreation/merge/deploy/deletion. Statusrunning.

## Log
### L1 User request (verbatim)
# HOMEX — Auditoría semántica definitiva de 120 audios y cierre de calidad ASR/NLP

## Objetivo

Continuar el perfeccionamiento del sistema de dictado de HOMEX, basándote en las 120 grabaciones reales y en los resultados de las dos intervenciones anteriores.

Tu objetivo es **identificar y resolver todos los defectos comerciales que puedan demostrarse, construir una referencia de evaluación verificable y preparar las ramas para su integración definitiva**, sin sobreajustar el NLP ni alterar los audios originales.

No se requiere otra refactorización general sin evidencia. Prioriza correcciones focalizadas con impacto medible.

## 1. Estado inicial

Las revisiones finales de la intervención anterior son:

- Frontend: `7b83694310239551e45d8a8a30ab96e2724c72c1`, rama `fix/real-voice-120-f09`.
- Backend: `850c250d0e673a296f4f0d772800aae89dd395b1`, rama `feat/real-voice-120-semantic`.
- NLP: `19d16ff0a428d765b7e89d3b695c02e5ce264b50`, rama `feat/real-voice-120-results`.

Los tres CI estaban verdes en esas revisiones.

El backend utiliza `homex-nlp==0.1.22` con wheel verificado.

El corpus está en:

`~/Descargas/HOMEX_Guiones_Evaluacion_Voz/`

Las evidencias están en:

`homex-nlp/audit/real-voice-120/`

Los informes actuales se encuentran en `semantic-120-v1/` y `frontend-f09-v1/`.

Antes de intervenir, inspecciona el estado actualizado de las tres ramas, el código, los contratos, los informes, los logs y los cambios locales.

No presupongas que los HEAD o los resultados de CI siguen siendo los mismos.

## 2. Construcción de la matriz de revisión comercial

El trabajo anterior midió 487 coincidencias sobre 1.000 valores escalares admitidos, pero no completó la validación integral de los campos ni de sus asociaciones.

Construye una matriz de los 120 casos que permita revisar:

- Identificador y categoría comercial.
- Audio AAC y WAV correspondiente.
- Guion original.
- Transcripción ASR original.
- Fragmentos de audio relevantes.
- Producto y cantidad.
- Dimensiones y unidades.
- Componentes y materiales.
- Espesores.
- Colores.
- Accesorios y cantidades.
- Modelos y códigos.
- Precio, moneda y modalidad.
- Campos no soportados.
- Ambigüedades y advertencias.
- Resultado NLP original y actual.
- Diferencias y posibles causas.
- Estado de validación de cada dato.

Distingue las referencias provenientes del guion, del documento comercial, de inferencias automáticas y de una comprobación humana del audio.

Un dato no debe marcarse como verificado por escucha simplemente porque coincide con el guion o porque varios modelos producen el mismo resultado.

## 3. Herramienta práctica de revisión

Prepara una interfaz o reporte local que permita revisar fácilmente los 120 casos.

Debe permitir escuchar cada grabación original, consultar su guion, observar la transcripción del ASR y comparar visualmente los campos comerciales.

Organiza las diferencias por gravedad y ofrece un mecanismo claro para registrar correcciones humanas, incertidumbres y decisiones.

Prioriza los casos que contienen precios incorrectos, medidas dudosas, productos no reconocidos o relaciones incorrectas entre componentes.

Las decisiones confirmadas deben poder exportarse a un formato estructurado y versionable, separado de los audios originales.

No es necesario incorporar esta herramienta a la interfaz productiva de HOMEX. Puede ser una utilidad local de auditoría.

## 4. Resolver los 17 casos sin propuesta

Investiga individualmente los siguientes casos sobre el ASR original:

MP-0003, MP-0008, MP-0012, MP-0017, MP-0022, MP-0026, MP-0037, MP-0051, MP-0057, MP-0060, MP-0061, MP-0065, MP-0066, MP-0070, MP-0071, MP-0072 y MP-0074.

Para cada uno:

1. Examina el audio, el guion, la transcripción y las evidencias NLP.
2. Ejecuta el extractor con la transcripción original y con el guion.
3. Identifica la causa exacta de la ausencia de propuesta.
4. Determina si existe realmente un producto principal inequívoco.
5. Diferencia productos independientes de componentes y referencias repetidas.
6. Corrige los errores verificables mediante reglas generalizables.
7. Conserva la abstención cuando exista una ambigüedad comercial legítima.
8. Añade pruebas de regresión.
9. Vuelve a evaluar el caso con todas las configuraciones pertinentes.

No establezcas como objetivo obligatorio obtener 120 propuestas. Una abstención correcta es preferible a inventar productos, medidas o precios.

## 5. Resolver errores comerciales de alto impacto

Después de los casos sin propuesta, investiga por orden de prioridad:

**Precios:** importes incorrectos, ausentes o asociados a una modalidad equivocada.

**Dimensiones:** ejes confundidos, unidades ausentes, valores duplicados o asociados al componente incorrecto.

**Cantidades:** confusión entre cantidad comercial, cantidad de accesorios y valores numéricos técnicos.

**Productos y componentes:** denominaciones comerciales incorrectas, nombres demasiado extensos y componentes tratados como productos adicionales.

**Catálogo:** modelos deletreados, materiales, colores, espesores y atributos específicos de sillas, pisos y Otros.

**ASR:** errores de reconocimiento que destruyen información comercial esencial y que no pueden recuperarse de forma segura mediante normalización.

Para cada defecto, conserva el ejemplo original, la causa raíz, la prueba fallida, la corrección y la prueba aprobada.

No uses los IDs de los audios como condiciones especiales del código.

## 6. Evaluación antes y después

Conserva la línea base histórica y realiza nuevas evaluaciones sin sobrescribir resultados anteriores.

Como mínimo, compara:

- ASR original + NLP anterior.
- ASR original + NLP corregido.
- ASR candidato + NLP corregido, únicamente cuando exista una configuración candidata justificada.
- Guion original + NLP anterior.
- Guion original + NLP corregido.

Informa precisión y recuperación por campo solamente cuando exista una referencia suficientemente validada.

Registra por separado los valores correctos, ausentes, incorrectos, adicionales, ambiguos y no verificables.

No presentes las coincidencias escalares como precisión comercial integral.

Muestra resultados globales y por categoría, especialmente en muebles a pedido.

## 7. Límites de la validación humana

No sustituyas la revisión humana de audio por una inferencia del ASR.

Cuando no exista confirmación humana suficiente, genera una cola de revisión ordenada y conserva el estado PENDIENTE.

Si una decisión humana es indispensable para establecer la verdad de un caso, deja preparada la evidencia, registra el bloqueo y continúa con los defectos independientes que sí puedan corregirse.

No inventes aprobaciones ni métricas acústicas verificadas.

## 8. Comprobación de regresiones y generalización

Evalúa los 120 casos después de cada conjunto significativo de correcciones.

Comprueba especialmente que:

- No aumenten los valores comerciales incorrectos.
- No se asignen unidades inexistentes.
- No se inventen productos ni accesorios.
- No se conviertan totales ambiguos en precios unitarios.
- No se pierdan campos previamente correctos.
- No se alteren las categorías comerciales, especialmente sillones y poltronas en OTRO.

El corpus de 120 grabaciones sigue siendo un conjunto de desarrollo. No utilices sus resultados como prueba independiente de generalización.

Prepara y ejecuta pruebas nuevas que no dependan de memorizar los guiones. Si existen audios realmente independientes, evalúalos sin utilizarlos previamente para ajustar reglas.

## 9. Integración, documentación y preparación de PR

Verifica la compatibilidad de las correcciones con las ramas frontend y backend actuales.

Si cambia el código NLP, publica una nueva versión del wheel solo cuando corresponda, conservando los artefactos y hashes históricos.

Comprueba los consumidores reales sin utilizar sustituciones de código fuente que oculten diferencias con la distribución instalada.

Ejecuta pruebas unitarias, contratos, lint, build, integración y CI.

Revisa los 8.293 archivos de la rama NLP y el volumen de evidencias publicadas. Clasifica cuáles son resultados necesarios, cuáles son históricos y cuáles son artefactos voluminosos.

No elimines archivos versionados ni reescribas el historial Git sin autorización.

Verifica el saneamiento de los datos publicados.

Actualiza un índice único del estado vigente del trabajo, sin modificar los resultados históricos inmutables.

Los archivos `.atl` generados localmente por Gentle AI no son parte funcional del sistema. Conserva los originales sin subirlos, salvo que exista una necesidad técnica demostrable.

## 10. Entregables

Produce:

1. Matriz de revisión de los 120 casos.
2. Herramienta local de revisión acústica y semántica.
3. Registro de decisiones humanas y pendientes.
4. Diagnóstico detallado de los 17 casos sin propuesta.
5. Lista de errores comerciales demostrados.
6. Correcciones implementadas y sus pruebas.
7. Comparación cuantitativa antes/después.
8. Registro de regresiones y abstenciones.
9. Verificación de backend/frontend.
10. Auditoría del material publicado.
11. Estado CI final.
12. Relación de commits y cambios.
13. Recomendación documentada para los tres PR.

Guarda los resultados nuevos en carpetas diferenciadas dentro del corpus local y publica únicamente evidencias saneadas y necesarias.

## Criterios de cierre

No declares completada la validación comercial integral si todavía existen decisiones humanas sin resolver.

Puedes declarar completada la intervención técnica cuando todas las correcciones demostrables estén verificadas, las regresiones estén controladas, los consumidores sean compatibles y los CI correspondientes estén verdes.

Debes informar por separado:

- Defectos técnicos corregidos.
- Defectos que continúan pendientes.
- Abstenciones legítimas.
- Casos pendientes de revisión acústica.
- Precisión comercial realmente verificable.
- Preparación para PR y merge.

**No fusiones a `main`, no despliegues producción y no elimines material histórico sin autorización.**

Procede autónomamente con todo el trabajo que pueda completarse de manera verificable, sin detenerte únicamente en el diagnóstico.

### L2 Initial verification
All3authorizedremoteheads/CI freshlyread: NLP19d16ff/43163332495success4/4,backend850c250/43160776481success13/13,frontend7b83694/43160479820success13/13. Existinglocalconsumerworktrees match andclean; originalbackendmainunknownuntrackedcelerybeat-schedule.db preserved,originalfrontendmaincleanef0a7f8. NLPcleanexceptpreexistinguntracked.atl.8293trackedfiles,8064underaudit. Projecthomex-nlp matchesruntimecwd; memory lifecycle review hasnonepending. Python3.11.15, NLP0.1.22, rules-only path; no reliable direct listeningtool, so acousticassertionsremainpending. No inference of technicaldefects from scalar misses alone.

### L3 Read-only map and route
References-v2 has120cases/2803scriptproposals,1688semanticpending and acousticdenominator0; playback-onlyHTML cannotrecorddecisions. Comparisonv5 holds14cells/7inputs×b851/current0.1.22 withrawoutputs. The17namedoriginalASRcases allabstain:13MULTIPLE_MAIN_PRODUCTS,4NO_PRODUCT; scriptcontrol10stillmultiple. These are causes toinspect, notproofall17arebugs. Twoindependentunits launchedtogetherwithdisjointedit surfaces; rootownsgit,tracking,publicationinventory,finalseams. UIwillbeofflineHTMLwithoriginalfileplayback, explicitself-reportedhumanprovenanceandexport/import, no networkserver or automaticverifiedflags. Baselinecurrent0.1.22reruns240beforefirstcoreedit; corpusoriginals immutable.

### L4 Frozen newbaseline and narrow component-surface extension
T2 actualfreshbaseline completed beforecoreedits:240originalASR/script executions +85(17×5frozenASRcandidates), categories73/27/7/13 and17no-proposalsunchanged. Initialcatalogwarning-shape harnessfailure preservedin separateincompletedirectory. T2mayadd src/homex_nlp/semantics.py only COMPONENTES grammar/introduced-component/reference matching requiredfor explicitintegratedcredenza/cajonería. Suppressing MULTIPLE alone wouldmisassigncomponentdimensions todesktop; require RED→GREEN associationregressions andnegativeindependent/lateralcredenza cases. No unrelatedprice/unit/accessoryparserchange authorized bythat extension. UIwriterdisjoint.

### L5 Verified local tool and relation fixes
T1offlineHTML actual120casesall14fields,73/27/7/13, zeroannotations/allPENDIENTE; syntheticbrowserattestation/export/import/invalidfingerprint/IDs/intervals/conflicts/XSS/no-networkPASS. ActualWAV/AACreadonlysmokeand240audiohashesbefore/afterPASS. UI5pytestPASS. T2literalcompound/introduceddrawer/integratedcredenzacontext fixes32newsynregressions;928fulltestsPASSincludingtool5; independentfreshsnapshot928PASS+37focused+Ruff+synthetic/actualreadonlybrowserchecksPASS. Declared nativeassessmenthighrisk3;modeOFFnoRDDstarted. Initialuntracked-inventoryassessmentfailurepreserved, declared8intendedpaths/immutableinventoryretryvalid, .atl excluded.
T2full14cells×120=1680outputssuccess:originalsupportedscriptpresence487→548/1000,script501→544/1000; no tuple/proposal/scalar-matchlosses840pairedcomparisons. Addedtuples89originalvs61matchedrecoveries;extrasUNVERIFIED, notprecision. Acoustic/associationdenominators0, whole1087script tuples87unsupported. Original17now7no-proposal,3legitimatesets+4pendingaudio/association; all120development. PrimaryfurniturenouncredenciaverifiedfromofficialCulturatesaurosindexedsource, notASRrepair.
T3triage:37scriptpriceabsencesmostlygenericPrecioamountwithoutcommercialmodality; doNOTinventunitprice. Pareceunitario remainsacousticuncertain. ExplicitfusedPreciunitarioiscurrentlymissed; prefixVeinticincoescritoriosmissesquantitythoughdigit25works. Independentcomma-separated80cmheightaftermalformedpor-chainismissed; narrowread-onlydimensionmaprequested. Dosmetroscincoremainder<10intentionallyambiguous; notforce205cmfromscriptagainstASR2.5withouthearing.

### L6 Focused value and human-review corrections
T3actualpublicAPIRED17FAIL/16PASS→GREEN33 aftercorrectingoneoverstrictprice-label-evidence test(theexistingcontractkeepsnumericspanonly); full961PASS. Prefix/explicit/postposedquantityusesexistingstrictcardinalgrammar withoutglobalNUMBER_WORDSexpansion; rejectsdecimal/alternative/invalidsuffix, accessoriesnotcommercialquantity. Preciunitarioisnarrowexplicitlabel; Pareceunitario/genericPrecioarenotforced. Independentheightafterclausepunctuationrestored; same-clause unmetro5/dosmetroscinco staysunresolved. Extraaliascontextconsistency2RED→37GREEN T3probes, preservingstrictmalformedcontexts.
IndependentT3snapshot961PASS,38focused/Ruff/differential5unaffectedpublicinputssameexceptlatency, syntheticbrowserattestationretention/noautogoldPASS. Sourcealiasguardextensionabove andJSON-key-orderbrowserfixstillrequiresnarrowfinalrecheck.
Humancheckboxattestationnowpersistedaslistening_attested:true; CLI/browserrejectmissing/FalsebeforetreatingHUMAN_AUDIOselfreport; RED1FAIL4PASS→GREEN5; commitec0b600. BrowsersemanticduplicatewithreorderedJSONkeysfailedoldUI, newcanonicalrecursivekeysorting alignsPythonandpasses, changedidentitystillrejects andoneunchangedrecordretained. Publicsyntheticbrowserprobeadded; no fakeactualcorpusannotations.
Publicationbaseline8293Gitpaths/8139uniqueblobs/397010245pathbytes;4historicaltraceZIPsdominate182MB. All3892ZIP/WHL/DOCXmembershashed, noaudionames/magic/mediaURI,262/262authheadersredacted,2212cookiearraysempty,0JWTshapes. Threeinitialunknownbinariesarelegacy0.1.21sdist,Wordguiones, historicaldemonstrationSQLite(13oldcaptures/3manualitems), notcurrent120gold. WOFF2embeddedfontis4nonUTF8traceextras. No archive/historymodified. No fullhumanvisualreviewof3606JPEGframesclaimed. Threecontactregexhitsaredummy70000000unit-tests;emailregexflagsnotleakproof.

### L7 Stable code and release route
T3finalboundedindependent965fulltestsPASS,37values/32relations/5tooltestsPASS, differentialunchangedcasesmatchexceptlatency; extraaliascontext andcanonicalhumanidentitykeyorderprobesPASS. Corevaluescommitc7bc2b6; identityfixc2a2d45; T1bc75868/T281caa3c/attestationec0b600. No realhumanannotations. Newrelease0.1.23required because distributioncodechanged, not newASRmodel/dependencies/contracts. Releasewriterparallel withparentindependent8293classification/PRdocumentationunit; source surfacesversionmetadata/lockedprojectversion/currentrelease+historiccopy/newreleasedoc+AACprivacygaptest. DiscoveryexistingdistributionguardforbidsWAV/etcbutnotAACoutsideaudionameddirs; testfirst addAAC, no actualartifactAAC observed. Do not overwritehistoricalwheels/manifests.

### L8 Final component and distribution evidence
Literal integrated credencia now retains component-local width150cm/height65cm/depth45unitnull inMP0007; malformed mainwidth remainsunresolved. Sixregressions plus independent75focused/976fullPASS. Parent focused11PASS and RuffPASS onresume3; componentcommit29b2f76. Final0.1.23 wheelSHAdebaed671426196adcad9d3dead2a5f0a7a8e2f786013777004c1c85087286ca; sdistSHA137af42a48fc44548b61b3c2ca2fe3ba5c84b4b2d64643423eace111d5d3cf54; twoidenticalbuilds/26installedmodulebytes/historical15distidentities independentlyreadbackPASS. Intermediateunpublishedv1preservedprivately.
Finalcomparison-v2 contains1680successfuloutputs, original487→549/1000 and17→7abstentions, script501→549. Zero matchedtuple/proposallosses; onewrongquantity1corrected61. Humanacoustic/associationgold0; no precision/generalizationclaim. Newprivate review-v2 rendered120/allPENDIENTE/0decisions; browsercheckinprogress.
Resume3 /tmp historicalscratchgone; controlledconsumerworker authorizedcopy originalbackend.venv read-only orfreshlockedprivateenv. No ambientservice/credentialreuse. T4consumer and T5reports remainpending; publicationhasnotoccurred. RDDglobalOFF.

### L9 Controlled consumers and review workspace
Releasecommitd9f7c54, backendinstalledconsumercommitd65c07a5605020363e4ba6acd6afcc310797412c. Backendoperative0.1.23wheel/lock/guard matchesexactdebaehash; RED4FAIL12PASSon0.1.22→GREEN16focused/78unitPASS, outside-repo26modulebytesPASS, negativewrongversion/corruptwheelPASS, independentPASS; parentspot16PASS. No stock/auth/businesslogicchanges. FullownedPG16/Redis/ASR/frontend verificationrunning; CIusesPG17so localversiondifferenceexplicit.
Review-v2 private120caseUI rendered, all14fieldtypes/allPENDIENTE/zerodecisions; ChromiumWAV/AAC+OTROsillónmetadatachecksPASS,no network,240originalhashesunchanged. Initialbrowserprobeusedwrongpropertycomponent; correctedcomponent_refmapsMP0007pieza-6width150/height65/depth45nullunit, mainheight80/depth70nullunit/no160width. Initiallogpreservedandcorrectedverdictadded.
Newpublicauditcommercial-review-v1containsminimal120casehashindex/metrics/17diagnoses/releasehashes/limitations/PRrecommendations; fullprivateworkspace/rawcommercialdictationsnotrepublished. CURRENT.jsonauthoritativebutclosurefalseuntilnewCIandfullconsumerproof. FreshparentNLP976PASS; scopedRuffsrc/test/toolsPASS; broadRuff338preexistingerrors28unchangedhistoricalfilesconfirmedexactsamebaselinecodes/locations/messages. No archivedsourceeditedtohideerrors. FrontendCIpeeronlydefaultupdatedtoactualbackendd65c07aanddocs0.1.23; independentmetadatarecheckpending, applicationbytesunchanged.

### L10 Live semantic consumer blockers
OwnedPG16 fullbackend559PASS/no skips, frontendunit306PASS/lint/buildPASS, actualsmallASR/Celery14integrationPASS, sequentialmockE2E109PASS/1preexistingattachmentskip. Targetedoriginal-ASR MP0007/0048 withoutmanualfill exposes loss: MP0007componentaxesflattenedanddatos_tecnicos.componentesempty; both explicitunitpricesblankinactualreviewthoughrawNLPpriceandbackendtotalpresent. Quantitycorrect; draftsremainBORRADOR/unlinked. Technicalcompletion remainsFALSE; exactrootcausemappingrequested, testsfirstcorrectionrequiredbeforepublication/greenclosure. SyntheticTTS14testsnotindependentspeechgold.

### L11 Focal legacy review projection fix
Chosenconservativefix: addread-onlynullableproyeccion_configuradorplusproyeccion_error tolegacyGETfromsamepersistedfinalizedraw, reusingexistingstrictPRF03projector/sharedDTO; no replayNLP/noItemIAmigration/nopipeline/HITLguard/persistedhistorychanges. BackendpublicAPI4REDmissingkeys→4GREEN; fixturecorrectionsestado.codigo andhistoricalnoItemIAtriggerpreserved. Invalidrawreturnsnull+expliciterror, totalnegotiateddoesnotderiveunitprice. SharedassistedDTOextractedwithoutfieldchanges; schema+10linesgeneratedvalidated.
Frontend15focusedtests(12existing+3new) nowprojectscopedcomponentsandexplicitunitprice, mainonlydimensionsnormalizedtothesamelegacystringrepresentationinbothduplicatefields; unknownunits remainwarnings. LegacyAPIwithoutmetadataunchanged. Componentthickness/accessoriesnotpromotedglobally. JSONAPIcloneusesJSONroundtripratherthanstructuredCloneonVuereactiveproxy; initialclonefailurepreservedandfixed. Additionalrealpublictextcapture→HITLtestusesindependentcontrolledwording, noIDconditions. Fullbackendindependentandfrontend/livevalidationpending.

### L12 Verified correction and publication candidate
Backendprojectioncommit7dae76876477b293db6269d1d3d0a82d9d084ae5 independentfull563PASS/Ruff374formatPASS/schema0errors1CategoryEnumwarning; DTOASTunchanged, permissionsviewbytesunchanged. Frontendfixcommitf00bce6edb10fda68620d11690708f8ff7c25e86, defaultbackendpeer+contractref7dae. Independentfrontend309PASS/lint/type/build/codegencontractsPASS; mockE2E109PASS1existingattachmentskip(allPDFsran); actualsmallASR/Celery+forms15integrationPASS. NewsyntheticHITLpersistedqty2/unit1900/total3800/BORRADOR/main160/credenza110x65MDF; unknown45unitnotinvented. OriginalMP0007/0048no manualfill/confirmation nowunit5200/2800, MP0007component150x65/mainonly80height/malformedwidthpending. SixauthoritychecksPASS. Parentfinal15focusedPASS. Allsourcebytesfrozenbeforeindependentchecks; docs/currentpeeronlylatermetadata. Genericinitial14PASSdidnotmasksemanticfail; beforelogs/screenshots preserved. LocalPG16vsCI17disclosed. T4localtechnicalproofPASS; remoteCIpending. T5minimalnewpublicreports~1MB, noaudio/newrawdictations/privatepaths/credentials; old8293filesnotdeleted. Publishingcontrolledbranchesauthorized; noPR/mainmerge/deploy.
