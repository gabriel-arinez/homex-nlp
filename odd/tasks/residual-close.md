# Residual NLP closure
Objective: Correct only the audited residual defects and deliver the coordinated closure evidence.
Branch: feat/nlp-final-lote02 in all four dedicated worktrees. Candidate target: 0.1.32; patch release avoids ambiguous wheel identity. Delivery: corrective Conventional Commits and published candidate branches, no PR/merge/deploy.

## Specs

### S1

Restricciones

- Continuar desde las ramas `feat/nlp-final-lote02` actualmente publicadas.
- Verificar los commits y estados locales/remotos antes de intervenir.
- Utilizar como evidencia `HOMEX_NLP_Implementacion_Final_Lote02.zip`, SHA-256 `56aea20ddc4d03c13713eeda7e83ec0190e5b70543a02893be290bbc77902320`.
- Mantener Whisper Small, CPU/int8, RULES_ONLY y los contratos existentes.
- No repetir el ASR de los 120 audios históricos ni de los 38 nuevos.
- Reutilizar los mismos guiones y transcripciones congeladas.
- No incorporar dependencias nuevas ni realizar cambios ajenos a los problemas descritos.
- Reproducir los defectos mediante pruebas RED antes de corregirlos.

### S2

Corregir la inferencia incoherente de unidades

La revisión independiente del wheel 0.1.31 reproduce:

- «Una mesa de dos metros de largo, sesenta de ancho y setenta de alto»: propone 60 y 70 metros.
- «Un escritorio de 2 metros de largo y 60 de fondo»: propone 60 metros.
- «Un escritorio con credenza de 1 metro de alto y 55 de profundidad»: propone 55 metros.
- «Una mesa de 2 metros de largo y 600 de ancho»: propone 600 metros.

Revisar `unit_inference.py`, especialmente la condición que hereda directamente la unidad cuando todos los vecinos tienen la misma unidad.

Toda inferencia debe pasar una comprobación de plausibilidad contextual, considerando el producto, componente, eje, magnitud y unidades locales.

No confundir unidad explícitamente compartida con mera proximidad de una unidad anterior.

Si heredar metros genera una magnitud desproporcionada, evaluar centímetros y milímetros. Cuando permanezcan varias interpretaciones plausibles, abstenerse.

Mantener las inferencias pendientes de confirmación humana y nunca sustituir unidades explícitas. Los valores explícitos atípicos deben conservarse y advertirse cuando corresponda.

Corregir también las pruebas que consideran satisfactoria una profundidad inferida de 55 metros únicamente porque se respeta el aislamiento entre componentes.

### S3

Completar la interpretación de espesores

La versión actual excluye los espesores del mecanismo de inferencia y no reconoce varias construcciones frecuentes.

Reproducir y corregir:

- «Mesa de melamina de dieciocho de espesor».
- «Mesa de melamina de 18».
- «Melamina de 18 y mesón engrosado a 25».
- «Tablero MDF de 15».
- «Tapacanto de 2 milímetros».
- «Vidrio templado de 6».

Reconocer espesores contextuales mediante el material, componente y construcción lingüística.

Proponer milímetros cuando exista evidencia suficiente del dominio, conservando la naturaleza inferida del valor.

No clasificar cualquier número próximo a un material como espesor. Distinguir dimensiones, modelos, cantidades, longitudes y precios.

Mantener pendientes los casos verdaderamente ambiguos.

### S4

Completar el reconocimiento monetario

Los 22 muebles ya tienen evidencia monetaria, pero únicamente 5 cuentan con precio estructurado. Los 17 restantes tienen cantidad comercial uno y modalidad monetaria no explícita.

Implementar una sugerencia revisable de importe para cantidad explícita uno, aprovechando la equivalencia aritmética entre precio unitario y total, sin falsificar la modalidad dictada.

Verificar que el importe llegue de forma útil al formulario y pueda confirmarse mediante los mecanismos existentes.

Reproducir y corregir:

- «Una mesa de 500 bolivianos».
- «Una mesa de madera a mil doscientos cincuenta bolivianos».
- «Una mesa de madera de mil bolivianos, perdón, de novecientos bolivianos».
- «Una mesa, precio de quinientos bolivianos».

Conservar las restricciones para cantidades superiores a uno cuando la modalidad sea ambigua.

No perder las mejoras existentes de parsing completo, rectificaciones, monedas, importes mixtos y protección contra truncamiento.

No introducir precios ni modalidades ficticias.

### S5

Corregir relaciones de productos compuestos

Actualmente:

«Un mueble con gabinete superior de un metro de ancho y gabinete inferior de dos metros de ancho»

produce NO_PROPOSAL y MULTIPLE_MAIN_PRODUCTS.

Corregir la relación entre producto principal y componentes subordinados de manera general.

Verificar composiciones equivalentes con gabinetes, credenzas, estantes, cajoneras y módulos, manteniendo las protecciones frente a productos realmente independientes.

No agregar excepciones dependientes de los identificadores del corpus.

### S6

Corregir coherencia de evidencia dimensional

En «mesa de dos por tres», el candidato que representa la cadena completa termina con normalized_value correspondiente únicamente al último operando.

Preservar la evidencia del conjunto y la evidencia individual de cada dimensión sin sobrescrituras.

Mantener offsets, decisiones, trazabilidad, referencias y mecanismos de revisión contractual.

No inventar ejes para cadenas dimensionales cuyo orden no está determinado.

### S7

Verificación focalizada

- Ejecutar pruebas nuevas para los defectos anteriores y sus variantes positivas, negativas y ambiguas.
- Ejecutar nuevamente las 50 pruebas dirigidas, comprobando sus resultados semánticos, no solamente que terminen sin errores.
- Comparar nuevamente los 38 casos con los resultados congelados de 0.1.30 y del candidato 0.1.31 anterior a esta corrección.
- Confirmar que se conservan las 22 propuestas de muebles cuando estén sustentadas.
- Comprobar que las asociaciones, cantidades, precios, unidades y códigos ya corregidos no presentan regresiones.
- Verificar que las sugerencias inferidas no se presentan como datos pronunciados.
- Ejecutar las suites completas de NLP, backend y frontend, además de las verificaciones de distribución y despliegue.
- Reproducir mediante navegador la revisión y aplicación de precios, espesores y dimensiones inferidas.

### S8

Restaurar CI completo

Eliminar las excepciones temporales de rama que omiten:

- Backend: f09-frontend-integration.
- Frontend: integration-real.
- Deploy: private-release-candidate.

Ejecutar los workflows completos con sus pruebas sintéticas o fixtures de integración habituales, sin repetir el corpus histórico ni el lote 02 mediante ASR.

No declarar CI completamente verde si se omiten trabajos requeridos, existen fallos o no se verifica el commit exacto.

### S9

Distribución y cierre coordinado

- Versionar e identificar inequívocamente el artefacto corregido. Evitar distribuir dos wheels distintos bajo una identidad inmutable indistinguible.
- Reconstruir wheel y sdist y actualizar hashes, dependencias, documentación y referencias entre repositorios.
- Confirmar que los cuatro repositorios consumen las versiones coordinadas.
- Publicar los commits correctivos en las ramas candidatas.
- Mantener main y producción intactos hasta la aprobación de la auditoría de cierre.

### S10

Entrega final

Generar `~/Descargas/HOMEX_NLP_Cierre_Definitivo.zip`.

Incluir únicamente evidencia suficiente y reproducible:

- Identidad de commits y artefactos.
- Correcciones realizadas.
- Pruebas RED/GREEN.
- Resultados completos de los 38 casos y las 50 pruebas dirigidas.
- Comparación frente al candidato anterior.
- Nuevas pruebas de regresión.
- Evidencia de navegador.
- Resultados de CI completo.
- Logs, hashes y comandos de reproducción.
- Limitaciones residuales reales.

No repetir investigaciones generales ni ampliar el alcance funcional. El objetivo es corregir los defectos residuales y dejar una versión estable, auditable y preparada para su promoción definitiva.

## Tasks

- T1 — S2,S3,S6: plausible inferred dimensions, contextual gauges, intact chain/scalar evidence; delegated (parallel numeric unit and money unit in isolated NLP worktrees); verified source and combined NLP suite1440; commit6b1cd6b; Risk item3 (shared parser/evidence contracts).
- T2 — S4,S7: complete monetary phrases and explicit-quantity-one review suggestion through backend/frontend; delegated (parallel independent numeric unit, isolated NLP tree); verified focused NLP241/backend57/frontend17; commits652ff7e,c6f92d3,86763f5; full seam in T4; Risk items2,3 (trusted review and consumed contracts).
- T3 — S5,S7: generic container/subordinate relations with independent-product guards; inline in disjoint composition/component functions; verified RED5/9 and full1418; commit455a466; Risk item3.
- T4 — S1,S7: semantic50 probes and frozen38 differential against0.1.30/0.1.31, browser and full suites; per-action verification workers; verified local NLP1440/backend906/frontend496/mocked-browser130 and real-browser3, frozen38 and semantic50; CI proof T5; Risk items2,3.
- T5 — S8,S9: release0.1.32, full synthetic CI restored, coordinated consumers/pins/hashes and clean distribution; inline plus per-action checks; in_progress; Risk item5.
- T6 — S10: minimal reproducible closureZIP, independent verification and original/main/production preservation; inline plus independent verifier; in_progress; Risk items2,3,5.

## Log

### L1 — Authorized request (verbatim)

# HOMEX — Corrección residual y cierre de la versión definitiva del NLP

La auditoría del candidato 0.1.31 confirma una mejora sustancial y acepta el incremento de latencia mediana de 0,595 a 1,268 ms.

No realizar otra refactorización general. Resolver exclusivamente los defectos residuales identificados y preparar el cierre coordinado de los cuatro repositorios.

## 1. Restricciones

- Continuar desde las ramas `feat/nlp-final-lote02` actualmente publicadas.
- Verificar los commits y estados locales/remotos antes de intervenir.
- Utilizar como evidencia `HOMEX_NLP_Implementacion_Final_Lote02.zip`, SHA-256 `56aea20ddc4d03c13713eeda7e83ec0190e5b70543a02893be290bbc77902320`.
- Mantener Whisper Small, CPU/int8, RULES_ONLY y los contratos existentes.
- No repetir el ASR de los 120 audios históricos ni de los 38 nuevos.
- Reutilizar los mismos guiones y transcripciones congeladas.
- No incorporar dependencias nuevas ni realizar cambios ajenos a los problemas descritos.
- Reproducir los defectos mediante pruebas RED antes de corregirlos.

## 2. Corregir la inferencia incoherente de unidades

La revisión independiente del wheel 0.1.31 reproduce:

- «Una mesa de dos metros de largo, sesenta de ancho y setenta de alto»: propone 60 y 70 metros.
- «Un escritorio de 2 metros de largo y 60 de fondo»: propone 60 metros.
- «Un escritorio con credenza de 1 metro de alto y 55 de profundidad»: propone 55 metros.
- «Una mesa de 2 metros de largo y 600 de ancho»: propone 600 metros.

Revisar `unit_inference.py`, especialmente la condición que hereda directamente la unidad cuando todos los vecinos tienen la misma unidad.

Toda inferencia debe pasar una comprobación de plausibilidad contextual, considerando el producto, componente, eje, magnitud y unidades locales.

No confundir unidad explícitamente compartida con mera proximidad de una unidad anterior.

Si heredar metros genera una magnitud desproporcionada, evaluar centímetros y milímetros. Cuando permanezcan varias interpretaciones plausibles, abstenerse.

Mantener las inferencias pendientes de confirmación humana y nunca sustituir unidades explícitas. Los valores explícitos atípicos deben conservarse y advertirse cuando corresponda.

Corregir también las pruebas que consideran satisfactoria una profundidad inferida de 55 metros únicamente porque se respeta el aislamiento entre componentes.

## 3. Completar la interpretación de espesores

La versión actual excluye los espesores del mecanismo de inferencia y no reconoce varias construcciones frecuentes.

Reproducir y corregir:

- «Mesa de melamina de dieciocho de espesor».
- «Mesa de melamina de 18».
- «Melamina de 18 y mesón engrosado a 25».
- «Tablero MDF de 15».
- «Tapacanto de 2 milímetros».
- «Vidrio templado de 6».

Reconocer espesores contextuales mediante el material, componente y construcción lingüística.

Proponer milímetros cuando exista evidencia suficiente del dominio, conservando la naturaleza inferida del valor.

No clasificar cualquier número próximo a un material como espesor. Distinguir dimensiones, modelos, cantidades, longitudes y precios.

Mantener pendientes los casos verdaderamente ambiguos.

## 4. Completar el reconocimiento monetario

Los 22 muebles ya tienen evidencia monetaria, pero únicamente 5 cuentan con precio estructurado. Los 17 restantes tienen cantidad comercial uno y modalidad monetaria no explícita.

Implementar una sugerencia revisable de importe para cantidad explícita uno, aprovechando la equivalencia aritmética entre precio unitario y total, sin falsificar la modalidad dictada.

Verificar que el importe llegue de forma útil al formulario y pueda confirmarse mediante los mecanismos existentes.

Reproducir y corregir:

- «Una mesa de 500 bolivianos».
- «Una mesa de madera a mil doscientos cincuenta bolivianos».
- «Una mesa de madera de mil bolivianos, perdón, de novecientos bolivianos».
- «Una mesa, precio de quinientos bolivianos».

Conservar las restricciones para cantidades superiores a uno cuando la modalidad sea ambigua.

No perder las mejoras existentes de parsing completo, rectificaciones, monedas, importes mixtos y protección contra truncamiento.

No introducir precios ni modalidades ficticias.

## 5. Corregir relaciones de productos compuestos

Actualmente:

«Un mueble con gabinete superior de un metro de ancho y gabinete inferior de dos metros de ancho»

produce NO_PROPOSAL y MULTIPLE_MAIN_PRODUCTS.

Corregir la relación entre producto principal y componentes subordinados de manera general.

Verificar composiciones equivalentes con gabinetes, credenzas, estantes, cajoneras y módulos, manteniendo las protecciones frente a productos realmente independientes.

No agregar excepciones dependientes de los identificadores del corpus.

## 6. Corregir coherencia de evidencia dimensional

En «mesa de dos por tres», el candidato que representa la cadena completa termina con normalized_value correspondiente únicamente al último operando.

Preservar la evidencia del conjunto y la evidencia individual de cada dimensión sin sobrescrituras.

Mantener offsets, decisiones, trazabilidad, referencias y mecanismos de revisión contractual.

No inventar ejes para cadenas dimensionales cuyo orden no está determinado.

## 7. Verificación focalizada

- Ejecutar pruebas nuevas para los defectos anteriores y sus variantes positivas, negativas y ambiguas.
- Ejecutar nuevamente las 50 pruebas dirigidas, comprobando sus resultados semánticos, no solamente que terminen sin errores.
- Comparar nuevamente los 38 casos con los resultados congelados de 0.1.30 y del candidato 0.1.31 anterior a esta corrección.
- Confirmar que se conservan las 22 propuestas de muebles cuando estén sustentadas.
- Comprobar que las asociaciones, cantidades, precios, unidades y códigos ya corregidos no presentan regresiones.
- Verificar que las sugerencias inferidas no se presentan como datos pronunciados.
- Ejecutar las suites completas de NLP, backend y frontend, además de las verificaciones de distribución y despliegue.
- Reproducir mediante navegador la revisión y aplicación de precios, espesores y dimensiones inferidas.

## 8. Restaurar CI completo

Eliminar las excepciones temporales de rama que omiten:

- Backend: f09-frontend-integration.
- Frontend: integration-real.
- Deploy: private-release-candidate.

Ejecutar los workflows completos con sus pruebas sintéticas o fixtures de integración habituales, sin repetir el corpus histórico ni el lote 02 mediante ASR.

No declarar CI completamente verde si se omiten trabajos requeridos, existen fallos o no se verifica el commit exacto.

## 9. Distribución y cierre coordinado

- Versionar e identificar inequívocamente el artefacto corregido. Evitar distribuir dos wheels distintos bajo una identidad inmutable indistinguible.
- Reconstruir wheel y sdist y actualizar hashes, dependencias, documentación y referencias entre repositorios.
- Confirmar que los cuatro repositorios consumen las versiones coordinadas.
- Publicar los commits correctivos en las ramas candidatas.
- Mantener main y producción intactos hasta la aprobación de la auditoría de cierre.

## 10. Entrega final

Generar `~/Descargas/HOMEX_NLP_Cierre_Definitivo.zip`.

Incluir únicamente evidencia suficiente y reproducible:

- Identidad de commits y artefactos.
- Correcciones realizadas.
- Pruebas RED/GREEN.
- Resultados completos de los 38 casos y las 50 pruebas dirigidas.
- Comparación frente al candidato anterior.
- Nuevas pruebas de regresión.
- Evidencia de navegador.
- Resultados de CI completo.
- Logs, hashes y comandos de reproducción.
- Limitaciones residuales reales.

No repetir investigaciones generales ni ampliar el alcance funcional. El objetivo es corregir los defectos residuales y dejar una versión estable, auditable y preparada para su promoción definitiva.

### L2 — Initial identity and bounded routing

Reference ZIP SHA256 verified. All four candidate worktrees are clean and equal their fetched remote candidate refs. Original main/production remain out of scope. Latency0.595→1.268ms is now explicitly accepted by the user. Full usual synthetic integration ASR is authorized; corpus38/120 ASR remains prohibited. RDD global off remains unchanged. Numeric and money units run in parallel with isolated NLP edit trees because they share rules.py; parent owns integration, git and all artifact identity changes. No broad refactor.

- L3 (2026-11-27): T1 isolated numeric unit observed RED16/22 then GREEN76 and full1417. Detached parent-owned commit7cef629 awaits seam integration. T2 public NLP RED7/12, backend genuine RED6/9 after isolated UTF8-template repair, mounted frontend RED2 and GREEN8; final worker verification pending. T3 read-only map identified bare conjunction continuation after explicit subordinate connector; parent RED5/9, focused GREEN38 including independent-product guards. No ASR/corpus processing. Private PostgreSQL55442 and external settings use only homex_close/test_homex_close. RDD remains globalOFF.

- L4 (2026-11-27): Parent committed monetary units652ff7e/c6f92d3/86763f5 and composition455a466, then cleanly cherry-picked isolated numeric unit as6b1cd6b. Composition full suite initially caught existing comma+y ambiguous-order protection; parent narrowed the conjunction condition, retaining that test unchanged; final1418 passed. Combined NLP1440 passes after all units and0.1.32 identity. Semantic50 explicit assertions improve40/50 to46/50; four pre-existing out-of-scope omissions TXT019/036/038/039 remain documented, not hidden or fixed by scope expansion. Frozen38 yields22/22 furniture proposals on scripts and ASR; quantity/price/catalog-field outputs unchanged vs0.1.31. New wheel SHA4e40a9b21055eab6c4dc85a805c83298d75ba8ef56397e46a0afe52ffc8f7b58. All three branch-specific CI job skips removed; actual fullCI still pending.

- L5 (2026-11-27): Final backend full suite906passed/0failed/0skipped on7c2ae90 with installed0.1.32; staleidentity first run33failed/871passed retained. Parent public gaugeprovenance RED2→GREEN23 distinguishes contextual inference from explicitshared enumeration. Frontend final full496unit+130mockedE2E+lint/type/build/schema green; test-only Array.at replaced by slice per existing TSlib. Real Chromium3/3 verifies money500 confirmation audit, MDF15mm explicit componentassignment, and2m+60/70cm inferred fields blank→human-reviewed persistence in three isolated syntheticproformas; no product/client/master creation, no audio. Independent fresh verifier24publicprobes+source/realintegration review finds S1-S6 met and no new blocker; closing proof pending fullCI/publication/ZIP. Offline cleanwheel/sdist installs45dependencies each and byte-rebuild bothhashes match. Backend final22d1225 differs from full-suite7c2ae90 only in CIpeerpin; deployed images/main remain unchanged. CI/publication starting now, no completedCI claim.
