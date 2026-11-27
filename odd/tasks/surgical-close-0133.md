# Surgical NLP closure 0.1.33
Objective: close only approved candidate residual drawer scope and unknown technical evidence.
Branch: feat/nlp-final-lote02; version target0.1.33. Delivery: reviewable candidate commits/push only, no PR/merge/deploy; task by task.

## Specs

### S1

1. **Reconocimiento singular de cajón.** En `semantics.py`, el patrón `cajones?` no reconoce «cajón». Revisar y corregir la morfología singular/plural mediante `caj[oó]n(?:es)?` o una solución equivalente. Auditar las expresiones relacionadas en cantidades internas, accesorios y asociaciones.

### S2

2. **Asociación de dimensiones.** Corregir TXT-019. Las dimensiones de 40 cm de ancho y 20 cm de alto deben pertenecer al cajón, no al escritorio principal. Reproducir variantes con un cajón, varios cajones, gavetas y componentes equivalentes. Evitar duplicaciones y conservar cantidades comerciales.

### S3

3. **Conservación de información desconocida.** Resolver de manera acotada TXT-036, TXT-038 y TXT-039. Conservar enchapado, acabado de poliuretano, marcas desconocidas explícitamente dictadas y materiales no reconocidos como evidencia u observaciones revisables. No inventar referencias comerciales ni ampliar masivamente el vocabulario. Si alguna representación requiere modificaciones contractuales desproporcionadas, documentarla como limitación aceptable y conservar la transcripción.

### S4

4. **Pruebas RED/GREEN.** Reproducir los defectos antes de corregirlos. Incorporar variantes positivas, negativas, singulares y plurales. Verificar que no se introduzcan asociaciones incorrectas.

### S5

5. **Preservación del candidato.** No modificar otras reglas que ya fueron aprobadas. Mantener Whisper Small, CPU/int8, RULES_ONLY, contratos y configuración vigente. No introducir dependencias ni ejecutar nuevamente ASR sobre los 158 audios.

### S6

6. **Evaluación diferencial.** Reutilizar las 38 entradas congeladas y las 50 pruebas dirigidas. Confirmar las 22 propuestas de muebles, las 22 sugerencias monetarias revisables y la ausencia de regresiones comerciales. No alterar las expectativas para obtener resultados favorables.

### S7

7. **Distribución coordinada.** Si cambia el contenido del paquete, asignar una nueva versión inequívoca, reconstruir sus artefactos y actualizar los consumidores, hashes, dependencias y referencias correspondientes.

### S8

8. **CI completo.** Ejecutar las suites y workflows requeridos en los cuatro repositorios. No omitir trabajos. Confirmar los resultados sobre los commits exactos publicados.

### S9

9. **Entrega final.** Generar un ZIP reducido que incluya las correcciones, pruebas RED/GREEN, resultados diferenciales, identidad de artefactos, commits, CI y manifiesto SHA-256. Verificar su estructura y semántica con un script comprobado previamente sobre una copia del paquete. No considerar una excepción del verificador como aprobación.

### S10

10. **Congelamiento.** No realizar nuevas investigaciones, ampliaciones generales ni refactorizaciones. Mantener main y producción intactos hasta la autorización final. El objetivo es cerrar exclusivamente el riesgo residual de asociación de componentes y conservar información técnica desconocida sin inventarla.

- no hay mucho uso restante (39%), asi que realiza tarea por tarea, si detectas que llegas a un porcentaje con el cual no completaras la tarea, documenta todo y sube tu avance, y responde hasta donde es que llegaste.

## Tasks

- T1 [S1,S2,S4,S5] delegated/context-backstop; verified; drawer RED21/39 plus genericRED4/5, focused218 and combinedfull1484GREEN; commit in log; Risk item3.
- T2 [S3,S4,S5] delegated/context-backstop afterT1; verified49newtests andfull1533GREEN; narrow unknown technical evidence retention; Risk item3.
- T3 [S6] per-action verification; in_progress; frozen38/50 semantic differential and22reviewableprices.
- T4 [S7,S8] inline plus per-action fullchecks; pending;0.1.33 build/pins/consumer CI exactheads; Risk item5.
- T5 [S9,S10] inline plus scoped verification; pending; pretested packagechecker then reducedZIP, main/prod preserved.

## Log

- L1 user request verbatim:

# HOMEX — Cierre quirúrgico del candidato NLP 0.1.32

La auditoría independiente del ZIP HOMEX_NLP_Cierre_Definitivo.zip confirma su integridad, reproduce las 108 respuestas NLP y las 50 pruebas dirigidas sin diferencias semánticas respecto a los resultados archivados.

Se aprueban las correcciones dimensionales, monetarias, de espesores, productos compuestos, rendimiento, distribución y restauración de CI.

Resolver exclusivamente los siguientes pendientes antes del cierre definitivo:

1. **Reconocimiento singular de cajón.** En `semantics.py`, el patrón `cajones?` no reconoce «cajón». Revisar y corregir la morfología singular/plural mediante `caj[oó]n(?:es)?` o una solución equivalente. Auditar las expresiones relacionadas en cantidades internas, accesorios y asociaciones.

2. **Asociación de dimensiones.** Corregir TXT-019. Las dimensiones de 40 cm de ancho y 20 cm de alto deben pertenecer al cajón, no al escritorio principal. Reproducir variantes con un cajón, varios cajones, gavetas y componentes equivalentes. Evitar duplicaciones y conservar cantidades comerciales.

3. **Conservación de información desconocida.** Resolver de manera acotada TXT-036, TXT-038 y TXT-039. Conservar enchapado, acabado de poliuretano, marcas desconocidas explícitamente dictadas y materiales no reconocidos como evidencia u observaciones revisables. No inventar referencias comerciales ni ampliar masivamente el vocabulario. Si alguna representación requiere modificaciones contractuales desproporcionadas, documentarla como limitación aceptable y conservar la transcripción.

4. **Pruebas RED/GREEN.** Reproducir los defectos antes de corregirlos. Incorporar variantes positivas, negativas, singulares y plurales. Verificar que no se introduzcan asociaciones incorrectas.

5. **Preservación del candidato.** No modificar otras reglas que ya fueron aprobadas. Mantener Whisper Small, CPU/int8, RULES_ONLY, contratos y configuración vigente. No introducir dependencias ni ejecutar nuevamente ASR sobre los 158 audios.

6. **Evaluación diferencial.** Reutilizar las 38 entradas congeladas y las 50 pruebas dirigidas. Confirmar las 22 propuestas de muebles, las 22 sugerencias monetarias revisables y la ausencia de regresiones comerciales. No alterar las expectativas para obtener resultados favorables.

7. **Distribución coordinada.** Si cambia el contenido del paquete, asignar una nueva versión inequívoca, reconstruir sus artefactos y actualizar los consumidores, hashes, dependencias y referencias correspondientes.

8. **CI completo.** Ejecutar las suites y workflows requeridos en los cuatro repositorios. No omitir trabajos. Confirmar los resultados sobre los commits exactos publicados.

9. **Entrega final.** Generar un ZIP reducido que incluya las correcciones, pruebas RED/GREEN, resultados diferenciales, identidad de artefactos, commits, CI y manifiesto SHA-256. Verificar su estructura y semántica con un script comprobado previamente sobre una copia del paquete. No considerar una excepción del verificador como aprobación.

10. **Congelamiento.** No realizar nuevas investigaciones, ampliaciones generales ni refactorizaciones. Mantener main y producción intactos hasta la autorización final. El objetivo es cerrar exclusivamente el riesgo residual de asociación de componentes y conservar información técnica desconocida sin inventarla.

- no hay mucho uso restante (39%), asi que realiza tarea por tarea, si detectas que llegas a un porcentaje con el cual no completaras la tarea, documenta todo y sube tu avance, y responde hasta donde es que llegaste.

- L2: T1 committed c479c8de045babb639503c4d0de57e3585915493. ExactTXT019 and variants now preserve drawer40/20cm vsdesk120/60cm; commercialquantity stable. Existingownershippolicy unchanged; enginegenericdetailmorphology RED4/5→GREEN44, combinedfull1484pass. T2starts next, sameboundedsequentialworkflow.

- L3: T2 committed 6e782a9313b88942bdf65dd2359326e9321225c1. UnknownESPEC/observations preserveexacttargets withno newcontract/lexicon. Parentreview foundliteralbrandtruncation andmarca/modeloCajónfalsephysicalcomponent; boundedcorrection RED6thenRED2, final49newtests/full1533GREEN. Product-wordbrand ambiguity andnumeric-brand monetaryambiguity remainoldabstentions; no approvedparsermasking. T3artifactidentity0.1.33 starts.
