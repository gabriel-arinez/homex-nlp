# Final Lote02 ASR/NLP candidate
Objective: Stabilize RULES_ONLY using frozen38-case audit; no ASR rerun, historical evaluation, production data, merge or deploy.
Branches: feat/nlp-final-lote02 in isolated four-repository worktrees. Delivery: candidate branches only, no PR requested; reviewable Conventional Commit units. Runner: existing Python3.11/pytest, isolated PostgreSQL and frontend tooling; evidence in Descargas.

## Specs

### S1

Contextualización y restricciones

- Revisar `homex-nlp`, `homex-backend`, `homex-frontend` y los mecanismos de distribución y despliegue relacionados.
- Utilizar como referencia `~/Descargas/HOMEX_NLP_Auditoria_Final_Lote02.zip`, SHA-256 `285db839fe0a652819ccd1eeefe84bb849e44bb67693ac1a807d8cc5336c11f0`.
- La línea base auditada es NLP 0.1.30, commit `a73c462a58f3211004289229bd62380d13f520cf`.
- Verificar el estado local y remoto actualizado antes de intervenir. Preservar cualquier cambio preexistente ajeno a la tarea.
- Mantener Faster-Whisper Small, CPU/int8, configuración ASR vigente y motor RULES_ONLY.
- No incorporar nuevos modelos NER, LLM, correctores generalistas, servicios externos ni dependencias pesadas.
- Trabajar exclusivamente con los 38 audios del lote 02. No volver a procesar los 120 audios anteriores.
- Reutilizar las transcripciones congeladas de Small para la comparación diferencial del NLP.
- No utilizar los guiones de referencia como entradas ocultas del procesamiento de voz ni incorporar reglas dependientes de identificadores de evaluación.
- Implementar soluciones generalizables, no excepciones para hacer pasar casos concretos.
- No modificar datos comerciales reales.
- Priorizar cambios incrementales y mantener las funcionalidades existentes.

### S2

Reconocimiento e identidad comercial de muebles

- Ampliar el reconocimiento de familias comerciales y variantes del sector mueblero: cocineta, gabinetes, alacenas, mostradores, estanterías, aparadores, repiseros, zapateros, tocadores, muebles funcionales y otras denominaciones justificadas.
- Corregir el patrón singular/plural de cubo móvil: actualmente `m[oó]viles?` no reconoce correctamente móvil en singular.
- Auditar otros patrones de pluralización, género, tildes y variantes morfológicas.
- Diferenciar nombre comercial completo de familia de mueble.
- Conservar calificativos como gerencial, circular, simple, archivadora, móvil, plegable, en L y funcionales como aguatero o para escobas.
- Evitar que cantidades, medidas y especificaciones técnicas sean absorbidas dentro del nombre.
- Permitir propuestas parciales cuando exista una identidad comercial suficiente, aunque no se hayan dictado dimensiones, precio, color o material.
- Mantener protecciones ante conversaciones ajenas, pruebas de micrófono, productos negados y referencias no comerciales.
- Reproducir los casos mínimos mediante NLP, backend y frontend antes de modificar condiciones de admisión.

### S3

Interpretación numérica y dimensional

- Consolidar la interpretación de magnitudes mediante una gramática reutilizable.
- Reconocer dimensiones separadas por `x`, `×` y la palabra «por», conservando límites completos y evitando interpretar precios o cantidades internas como dimensiones.
- Admitir cadenas de dos y tres valores, decimales con punto o coma, números escritos, números en palabras y expresiones mixtas.
- Admitir expresiones como «un metro veinte», «un metro y medio», «medio metro», «dos metros y cuarto», «dos metros con treinta centímetros» y variantes justificadas.
- Impedir la extracción parcial de expresiones compuestas. En particular, «dos metros con treinta centímetros de largo» debe representar 230 cm, nunca solamente 30 cm.
- Diferenciar dimensiones, espesores, diámetros, perfiles, longitudes de accesorios, capacidades, ángulos, cantidades y precios.
- Reconocer espesores expresados en mm, cm y, cuando esté contextualizado, sin unidad.
- Evitar considerar automáticamente toda expresión en milímetros como espesor.

### S4

Inferencia contextual de unidades

- Aplicar la siguiente precedencia: unidad explícita, unidad compartida por enumeración, contexto local del mismo elemento, perfil dimensional y finalmente revisión por ambigüedad.
- Resolver, cuando exista suficiente evidencia, expresiones como «mesa de dos por tres», «mesa de cincuenta y cinco por cincuenta y cinco», «escritorio de ciento veinte por sesenta» y medidas mixtas.
- En muebles generales, estudiar las interpretaciones plausibles en metros, centímetros y milímetros. En tableros, perfiles, cantos y herrajes, utilizar el contexto técnico correspondiente.
- Interpretar omisiones como «90 centímetros de ancho, 43 de profundidad y 70 de alto», proponiendo centímetros para los valores elípticos cuando corresponda.
- No utilizar exclusivamente umbrales numéricos globales.
- Incorporar perfiles dimensionales configurables como evidencia orientativa, nunca como restricciones absolutas para muebles personalizados.
- Separar inferencia de unidad y asignación de eje. No asignar largo/ancho arbitrariamente cuando el orden no esté sustentado.
- Conservar valor original, evidencia, valor normalizado e indicación de unidad inferida.
- Si existen varias interpretaciones plausibles, mantener el campo pendiente.
- Una unidad explícita atípica no debe sustituirse por otra silenciosamente.

### S5

Geometrías especiales

- Reconocer mesas circulares, cuadradas, rectangulares, escritorios en L, muebles modulares y conjuntos.
- Diferenciar diámetro y altura en mesas circulares.
- En muebles en L, conservar los tramos sin convertir automáticamente dos longitudes en largo y ancho convencionales.
- Reconocer rangos dimensionales, orientación, configuraciones regulables y otras características geométricas cuando estén expresadas claramente.
- Aprovechar componentes, conjuntos, candidatos y observaciones existentes antes de ampliar el contrato.
- Las geometrías que no puedan representarse con seguridad deben conservarse como información revisable, sin fabricar ejes.

### S6

Productos compuestos, componentes y relaciones

- Corregir la interpretación de escritorio con credenza, cocineta con gabinetes, escritorio con estante, muebles con cajonerías, cubos móviles y otras composiciones comerciales.
- No exigir exclusivamente palabras como «integrada» para reconocer una relación de componente.
- Analizar construcciones como «con», «incluye», «incorpora», «compuesto por» y referencias descriptivas posteriores.
- Resolver correctamente MP-0086, MP-0088, MP-0094 y MP-0099 sin eliminar las protecciones frente a múltiples productos independientes.
- Diferenciar menciones reiteradas del mismo componente de componentes realmente distintos.
- Evitar duplicar cajones por el hecho de que se describan nuevamente en otra cláusula.
- Diferenciar cantidad comercial, cantidades internas, distribución por lado, cantidades por componente y capacidad de uso.
- No convertir tres cajones, seis niveles o cuatro ruedas en cantidades comerciales de muebles.
- Asociar atributos considerando el ámbito sintáctico y semántico, no solamente la proximidad del último componente o la puntuación del ASR.
- Corregir MP-0081: el ancho general del gavetero no debe pertenecer automáticamente a sus cajones.
- Corregir MP-0089: el largo general del escritorio no debe atribuirse automáticamente a las patas; los 18 mm del faldón corresponden al espesor y no a la altura general.
- Diferenciar espesores de tablero, mesón, laterales y otros elementos.
- Mantener pendientes las asociaciones que no puedan resolverse inequívocamente.

### S7

Conocimiento especializado del sector mueblero

- Revisar y consolidar los vocabularios y recursos existentes, verificando cuáles son utilizados realmente por el código.
- Organizar familias, nombres, materiales, marcas, componentes, accesorios, acabados, colores, unidades y variantes lingüísticas.
- Incorporar terminología relevante respaldada por especificaciones del sector y por el lote 02.
- Diferenciar sustrato, recubrimiento, material estructural, tratamiento, textura y diseño decorativo.
- Contemplar MDF, MDP, HDF, aglomerado, contrachapado, melamina, PVC, ABS, vidrio templado, acero cromado y otros materiales pertinentes.
- Reconocer marcas como Novopan y diseños/colores como sapelli, wengué, cerezo, chumbo, cedro y maderable oscuro.
- Diferenciar madera real de un acabado o imitación decorativa.
- Reconocer combinaciones de colores y conservar «color a elección» como selección pendiente.
- Ampliar herrajes y accesorios: correderas, rieles, bisagras, jaladores, tiradores, chapas centralizadas, tapacantos, regatones, ruedas con freno, porta CPU, porta teclado, pasacables, luminarias y otros términos pertinentes.
- Conservar características como telescópico, batiente, ajustable, plegable, engomado, cromado y cierre suave cuando se dicten.
- Evitar propagar el material de un accesorio al mueble o componente que lo contiene.
- No inventar materiales específicos cuando solamente se haya indicado «metálico».

### S8

Recuperación léxica de errores ASR

- Mantener intacta la transcripción original y sus offsets.
- Implementar recuperaciones léxicas estrictamente contextualizadas, utilizando las reglas existentes cuando sea posible.
- Estudiar las variantes observadas: gadetero/gavetero, nobopan/Novopan, novo pan/Novopan, me lamina/melamina, melaménico/melamínico, me son/mesón, huengüe/wengué, conjalador/con jalador.
- Registrar texto original, interpretación propuesta, regla responsable y estado de revisión.
- No corregir automáticamente expresiones demasiado degradadas sin evidencia suficiente.
- No aplicar similitud indiscriminada a nombres comerciales, marcas, modelos, números o importes.
- No sustituir términos reconocidos por los valores esperados de los guiones de evaluación.
- Mantener las correcciones monetarias especializadas existentes y comprobar que no introduzcan regresiones.

### S9

Interpretación monetaria

- Reutilizar y consolidar el parser monetario existente para evitar gramáticas incompatibles.
- Corregir `find_ambiguous_price()` para que conserve importes completos escritos en cifras, palabras y expresiones mixtas.
- Impedir que «13 mil 200» genere un candidato monetario de 13.
- Reconocer «precio de mil cien bolivianos», «precio de 2 mil 500» y construcciones equivalentes.
- Mantener separados importe reconocido y modalidad comercial.
- Cuando se indique una cantidad explícita de uno y un precio inequívoco, permitir una sugerencia revisable aprovechando la equivalencia aritmética entre unitario y total, sin falsificar la modalidad pronunciada.
- Para cantidades superiores a uno y modalidad ambigua, conservar el importe y solicitar confirmación.
- Reconocer expresiones inequívocas de precio unitario y total, incluidas modalidades pospuestas como «por dos mil bolivianos en total».
- Conservar monedas, decimales, separadores, rectificaciones y conflictos.
- No cambiar importes pronunciados porque otro valor sea más habitual o coincida con el guion.
- Preservar las reglas comerciales de totales, descuentos y revisión humana del backend.

### S10

Conservación de especificaciones no estructuradas

- Identificar características técnicas que actualmente se pierden después de la extracción: garantía, procedencia, instalación, entrega, traslado, acabados, distribución, resistencia y condiciones de fabricación.
- Utilizar los campos estructurados existentes cuando sean semánticamente compatibles.
- Conservar el resto mediante atributos técnicos, descripción u observaciones revisables.
- Evitar duplicar información o copiar indiscriminadamente toda la transcripción como si fuera una extracción estructurada.
- Mantener siempre la transcripción original y su trazabilidad.
- Verificar que la información extraída llegue realmente al formulario y al flujo de revisión correspondiente.

### S11

Correcciones de catálogo

- Mantener separados los flujos de muebles a pedido y creación de productos de catálogo.
- Corregir nombres de sillas, pisos y zócalos que incorporan cantidades cotizadas.
- Reconocer el nombre comercial de pisos flotantes cuando comienza por una cantidad en metros cuadrados.
- Corregir el truncamiento de códigos como `NF Guión 7,782`, que actualmente termina como NF-7.
- Un código debe reconocerse completamente o quedar pendiente; no aceptar fragmentos como códigos completos.
- Mejorar interpretación de modelos alfanuméricos cuando la evidencia lo permita.
- No reconstruir letras ausentes de códigos como D81A o NA9174 sin evidencia suficiente.
- Admitir capacidades de carga, ángulos, giro y demás especificaciones soportadas tanto en números como en palabras.
- Detectar valores técnicos atípicos, como 80 mm de espesor para un piso flotante, solicitando confirmación en lugar de sustituir automáticamente el número.
- Mantener las cantidades cotizadas separadas de las existencias.
- Conservar información técnica de zócalos y otros productos mediante las estructuras compatibles existentes.
- No crear productos, marcas, colores o referencias comerciales ficticias.

### S12

Contratos, backend y frontend

- Inspeccionar los contratos Pydantic, `apps/capturas/nlp/adapter.py`, `proyeccion_prf03.py`, `revision_voz.py`, `catalogo.py` y las rutas reales de consumo.
- Preservar la singularidad de la propuesta comercial y la compatibilidad contractual.
- Reutilizar los mecanismos de evidencia y revisión existentes para representar inferencias, cuando sean suficientes.
- Si una ampliación contractual es indispensable, justificarla y actualizar coordinadamente todos los consumidores estrictos, esquemas, serializers y pruebas.
- Verificar que los candidatos inferidos no se presenten como datos explícitamente pronunciados.
- Comprobar la proyección de dimensiones, componentes, materiales, colores, nombres, cantidades, precios y observaciones.
- Verificar `StagedVoiceCapture.vue`, `capturaAsistidaMapper.ts`, `MuebleStudio.vue`, `ProductoForm.vue` y los consumidores reales encontrados.
- Reproducir en navegador los muebles con pocas especificaciones y comprobar que los campos reconocidos se aplican correctamente.
- Los campos ausentes deben permanecer pendientes o vacíos; no impedir la extracción parcial por requisitos propios del guardado definitivo.
- Mantener permisos, validaciones comerciales, idempotencia, trazabilidad y revisión humana.
- Realizar las pruebas de navegador y persistencia en un entorno aislado, sin modificar datos comerciales reales.

### S13

Pruebas de regresión y casos dirigidos

- Reproducir los defectos identificados mediante pruebas RED antes de implementar las correcciones.
- Ejecutar las 50 pruebas dirigidas incluidas en la auditoría.
- Ampliar con casos independientes que incluyan combinaciones nuevas de productos, medidas, componentes, materiales y accesorios.
- Incorporar pruebas positivas, negativas, ambiguas y casos de frontera.
- Probar variantes singular/plural, puntuación ausente, acentos, espacios y representaciones numéricas alternativas.
- Probar explícitamente que no se generan precios, cantidades, unidades, códigos o componentes incorrectos.
- No modificar expectativas existentes solamente para que la nueva implementación pase.
- Ejecutar las suites automatizadas de NLP, backend y frontend.
- No volver a ejecutar el reconocimiento ASR ni la evaluación histórica de los 120 audios anteriores.

### S14

Evaluación diferencial del lote 02

- Comparar la línea base auditada y la versión candidata sobre exactamente los mismos 38 guiones y las mismas 38 transcripciones congeladas.
- Evaluar por separado guion→NLP, ASR→NLP y proyección integrada.
- No mezclar resultados de pruebas dirigidas con métricas de audios reales.
- Conservar respuestas completas, candidatos, asociaciones, advertencias y resultados por identificador.
- Revisar especialmente los 22 muebles a pedido.
- Informar mejoras, regresiones, campos incorrectos, omisiones y abstenciones justificadas.
- Evaluar exactitud de identidad, dimensiones, unidades, ámbitos, cantidades, materiales, colores, importes y códigos donde exista una referencia suficiente.
- Diferenciar datos explícitos, inferidos, ambiguos, no soportados y pendientes.
- No calcular precisión, recall o F1 definitivos utilizando anotaciones incompletas.
- No afirmar validación independiente cuando los mismos 38 casos hayan servido para desarrollar las mejoras.
- Medir latencia NLP antes y después en condiciones comparables, con múltiples repeticiones y reporte de mediana y percentil 95.
- No introducir degradaciones injustificadas de rendimiento.

### S15

Criterios de aceptación y cierre

- Aspirar a recuperar todos los muebles legítimos de los 22 guiones, siempre que su identidad y composición estén suficientemente sustentadas.
- Para las transcripciones ASR, recuperar toda propuesta justificable por el texto real; no forzar 22/22 mediante invenciones.
- Resolver los siete casos críticos identificados o documentar una causa residual legítima y reproducible.
- No truncar números compuestos, dimensiones ni códigos comerciales.
- No introducir errores nuevos de importe, cantidad o asociación.
- Demostrar que las inferencias de unidades son revisables y no se confunden con datos explícitos.
- Confirmar que los casos simples funcionan de extremo a extremo.
- Verificar que las mejoras no perjudican las restantes categorías.
- Superar pruebas unitarias, contractuales, integración, lint, esquemas y build.
- Construir el wheel de distribución y verificarlo en un entorno limpio.
- Incrementar la versión del paquete y la identificación de reglas conforme al estado real del repositorio.
- Actualizar el backend consumidor, dependencias fijadas, hashes y documentación de despliegue.
- Verificar la versión realmente cargada durante la ejecución.
- No declarar definitiva la versión si existen regresiones comerciales críticas o pruebas fallidas.

### S16

Entrega de evidencia

- Generar `~/Descargas/HOMEX_NLP_Implementacion_Final_Lote02.zip`.
- Incluir identidad exacta de línea base y candidato, commits, diferencias de código, inventario de reglas modificadas, pruebas RED/GREEN, resultados completos de los 38 casos, comparación diferencial, evidencia de integración, métricas de rendimiento, wheel, hashes, logs y comandos de reproducción.
- Incluir capturas y evidencia de las pruebas reales del navegador.
- Entregar un resumen por problema identificado, causa raíz, corrección aplicada, resultado y riesgo residual.
- Incluir los casos que sigan fallando, sin ocultarlos ni ajustar artificialmente sus resultados.
- Excluir secretos, credenciales y datos ajenos a la evaluación.
- Mantener el trabajo candidato identificable mediante commits separados. Publicar la rama de trabajo para revisión, sin promover todavía la nueva versión a producción ni fusionarla definitivamente a main hasta superar la auditoría final.
- No alterar el corpus histórico ni sus resultados.

El objetivo no es conseguir únicamente más coincidencias textuales: es obtener propuestas comerciales técnicamente correctas, contextualizadas, trazables y utilizables para HOMEX.

## Tasks

- T1 — S3,S4,S9,S12,S13: complete scalar/money/dimension grammar and reviewable unit proposals; route delegated (parallel independent catalog unit T4, disjoint files); reopened (broad-suite regressions); commit d9b7c9d; Risk item3 (shared parsers and consumer evidence).
- T2 — S2,S7,S8,S10,S13: commercial identities, contextual lexical variants, vocabulary and scoped descriptions; route inline; reopened (false component and scope regressions); commit 6a27475; Risk item3 (shared product/semantic extraction).
- T3 — S5,S6,S12,S13: composition, geometry, owner resolution and component deduplication; route inline; reopened (broad-suite numeric and owner regressions); commits 32f3824,fce3c92; Risk item3 (shared projection evidence and associations).
- T4 — S11,S13: complete catalog names/codes/technical values; route delegated (parallel independent T1, catalog/spoken-code surfaces only); reopened (catalog observation regression); commit e7a9de5; Risk item3 (shared catalog extraction consumed by backend).
- T5 — S1,S12,S13: backend/frontend propagation, inference review and real isolated-browser minimal cases; route delegated (long-session context backstop); in_progress (focused checks committed, browser/full suites pending); commits backend b94d9a9/frontend 6adba39; Risk items2,3 (trusted review guard and strict consumer/projection contracts).
- T6 — S14,S15: full permitted suites, frozen38-case differential,50probes, repeated latency and independent high-risk verifier; route inline plus per-action verification workers; pending; Risk item3.
- T7 — S1,S15,S16: version/wheel/clean verification, backend/deploy pins and hashes, candidate commits/branch publication and final evidenceZIP; route inline; in_progress (candidate0.1.31, offline build/runtime checks); Risk item5 (distribution/dependencies; no deployment).

## Log

### L1 — Original request, verbatim

# HOMEX — Implementación, estabilización y cierre definitivo del ASR/NLP

Implementar la última versión del componente NLP de HOMEX antes de la defensa del proyecto de grado, utilizando la auditoría del lote 02 y las siguientes especificaciones como base de trabajo.

HOMEX recibe dictados técnicos intencionales de productos, no conversaciones ni negociaciones. Su objetivo es reconocer, interpretar, clasificar y asociar especificaciones comerciales y técnicas, generando propuestas revisables sin inventar información.

## 1. Contextualización y restricciones

- Revisar `homex-nlp`, `homex-backend`, `homex-frontend` y los mecanismos de distribución y despliegue relacionados.
- Utilizar como referencia `~/Descargas/HOMEX_NLP_Auditoria_Final_Lote02.zip`, SHA-256 `285db839fe0a652819ccd1eeefe84bb849e44bb67693ac1a807d8cc5336c11f0`.
- La línea base auditada es NLP 0.1.30, commit `a73c462a58f3211004289229bd62380d13f520cf`.
- Verificar el estado local y remoto actualizado antes de intervenir. Preservar cualquier cambio preexistente ajeno a la tarea.
- Mantener Faster-Whisper Small, CPU/int8, configuración ASR vigente y motor RULES_ONLY.
- No incorporar nuevos modelos NER, LLM, correctores generalistas, servicios externos ni dependencias pesadas.
- Trabajar exclusivamente con los 38 audios del lote 02. No volver a procesar los 120 audios anteriores.
- Reutilizar las transcripciones congeladas de Small para la comparación diferencial del NLP.
- No utilizar los guiones de referencia como entradas ocultas del procesamiento de voz ni incorporar reglas dependientes de identificadores de evaluación.
- Implementar soluciones generalizables, no excepciones para hacer pasar casos concretos.
- No modificar datos comerciales reales.
- Priorizar cambios incrementales y mantener las funcionalidades existentes.

## 2. Reconocimiento e identidad comercial de muebles

- Ampliar el reconocimiento de familias comerciales y variantes del sector mueblero: cocineta, gabinetes, alacenas, mostradores, estanterías, aparadores, repiseros, zapateros, tocadores, muebles funcionales y otras denominaciones justificadas.
- Corregir el patrón singular/plural de cubo móvil: actualmente `m[oó]viles?` no reconoce correctamente móvil en singular.
- Auditar otros patrones de pluralización, género, tildes y variantes morfológicas.
- Diferenciar nombre comercial completo de familia de mueble.
- Conservar calificativos como gerencial, circular, simple, archivadora, móvil, plegable, en L y funcionales como aguatero o para escobas.
- Evitar que cantidades, medidas y especificaciones técnicas sean absorbidas dentro del nombre.
- Permitir propuestas parciales cuando exista una identidad comercial suficiente, aunque no se hayan dictado dimensiones, precio, color o material.
- Mantener protecciones ante conversaciones ajenas, pruebas de micrófono, productos negados y referencias no comerciales.
- Reproducir los casos mínimos mediante NLP, backend y frontend antes de modificar condiciones de admisión.

## 3. Interpretación numérica y dimensional

- Consolidar la interpretación de magnitudes mediante una gramática reutilizable.
- Reconocer dimensiones separadas por `x`, `×` y la palabra «por», conservando límites completos y evitando interpretar precios o cantidades internas como dimensiones.
- Admitir cadenas de dos y tres valores, decimales con punto o coma, números escritos, números en palabras y expresiones mixtas.
- Admitir expresiones como «un metro veinte», «un metro y medio», «medio metro», «dos metros y cuarto», «dos metros con treinta centímetros» y variantes justificadas.
- Impedir la extracción parcial de expresiones compuestas. En particular, «dos metros con treinta centímetros de largo» debe representar 230 cm, nunca solamente 30 cm.
- Diferenciar dimensiones, espesores, diámetros, perfiles, longitudes de accesorios, capacidades, ángulos, cantidades y precios.
- Reconocer espesores expresados en mm, cm y, cuando esté contextualizado, sin unidad.
- Evitar considerar automáticamente toda expresión en milímetros como espesor.

## 4. Inferencia contextual de unidades

- Aplicar la siguiente precedencia: unidad explícita, unidad compartida por enumeración, contexto local del mismo elemento, perfil dimensional y finalmente revisión por ambigüedad.
- Resolver, cuando exista suficiente evidencia, expresiones como «mesa de dos por tres», «mesa de cincuenta y cinco por cincuenta y cinco», «escritorio de ciento veinte por sesenta» y medidas mixtas.
- En muebles generales, estudiar las interpretaciones plausibles en metros, centímetros y milímetros. En tableros, perfiles, cantos y herrajes, utilizar el contexto técnico correspondiente.
- Interpretar omisiones como «90 centímetros de ancho, 43 de profundidad y 70 de alto», proponiendo centímetros para los valores elípticos cuando corresponda.
- No utilizar exclusivamente umbrales numéricos globales.
- Incorporar perfiles dimensionales configurables como evidencia orientativa, nunca como restricciones absolutas para muebles personalizados.
- Separar inferencia de unidad y asignación de eje. No asignar largo/ancho arbitrariamente cuando el orden no esté sustentado.
- Conservar valor original, evidencia, valor normalizado e indicación de unidad inferida.
- Si existen varias interpretaciones plausibles, mantener el campo pendiente.
- Una unidad explícita atípica no debe sustituirse por otra silenciosamente.

## 5. Geometrías especiales

- Reconocer mesas circulares, cuadradas, rectangulares, escritorios en L, muebles modulares y conjuntos.
- Diferenciar diámetro y altura en mesas circulares.
- En muebles en L, conservar los tramos sin convertir automáticamente dos longitudes en largo y ancho convencionales.
- Reconocer rangos dimensionales, orientación, configuraciones regulables y otras características geométricas cuando estén expresadas claramente.
- Aprovechar componentes, conjuntos, candidatos y observaciones existentes antes de ampliar el contrato.
- Las geometrías que no puedan representarse con seguridad deben conservarse como información revisable, sin fabricar ejes.

## 6. Productos compuestos, componentes y relaciones

- Corregir la interpretación de escritorio con credenza, cocineta con gabinetes, escritorio con estante, muebles con cajonerías, cubos móviles y otras composiciones comerciales.
- No exigir exclusivamente palabras como «integrada» para reconocer una relación de componente.
- Analizar construcciones como «con», «incluye», «incorpora», «compuesto por» y referencias descriptivas posteriores.
- Resolver correctamente MP-0086, MP-0088, MP-0094 y MP-0099 sin eliminar las protecciones frente a múltiples productos independientes.
- Diferenciar menciones reiteradas del mismo componente de componentes realmente distintos.
- Evitar duplicar cajones por el hecho de que se describan nuevamente en otra cláusula.
- Diferenciar cantidad comercial, cantidades internas, distribución por lado, cantidades por componente y capacidad de uso.
- No convertir tres cajones, seis niveles o cuatro ruedas en cantidades comerciales de muebles.
- Asociar atributos considerando el ámbito sintáctico y semántico, no solamente la proximidad del último componente o la puntuación del ASR.
- Corregir MP-0081: el ancho general del gavetero no debe pertenecer automáticamente a sus cajones.
- Corregir MP-0089: el largo general del escritorio no debe atribuirse automáticamente a las patas; los 18 mm del faldón corresponden al espesor y no a la altura general.
- Diferenciar espesores de tablero, mesón, laterales y otros elementos.
- Mantener pendientes las asociaciones que no puedan resolverse inequívocamente.

## 7. Conocimiento especializado del sector mueblero

- Revisar y consolidar los vocabularios y recursos existentes, verificando cuáles son utilizados realmente por el código.
- Organizar familias, nombres, materiales, marcas, componentes, accesorios, acabados, colores, unidades y variantes lingüísticas.
- Incorporar terminología relevante respaldada por especificaciones del sector y por el lote 02.
- Diferenciar sustrato, recubrimiento, material estructural, tratamiento, textura y diseño decorativo.
- Contemplar MDF, MDP, HDF, aglomerado, contrachapado, melamina, PVC, ABS, vidrio templado, acero cromado y otros materiales pertinentes.
- Reconocer marcas como Novopan y diseños/colores como sapelli, wengué, cerezo, chumbo, cedro y maderable oscuro.
- Diferenciar madera real de un acabado o imitación decorativa.
- Reconocer combinaciones de colores y conservar «color a elección» como selección pendiente.
- Ampliar herrajes y accesorios: correderas, rieles, bisagras, jaladores, tiradores, chapas centralizadas, tapacantos, regatones, ruedas con freno, porta CPU, porta teclado, pasacables, luminarias y otros términos pertinentes.
- Conservar características como telescópico, batiente, ajustable, plegable, engomado, cromado y cierre suave cuando se dicten.
- Evitar propagar el material de un accesorio al mueble o componente que lo contiene.
- No inventar materiales específicos cuando solamente se haya indicado «metálico».

## 8. Recuperación léxica de errores ASR

- Mantener intacta la transcripción original y sus offsets.
- Implementar recuperaciones léxicas estrictamente contextualizadas, utilizando las reglas existentes cuando sea posible.
- Estudiar las variantes observadas: gadetero/gavetero, nobopan/Novopan, novo pan/Novopan, me lamina/melamina, melaménico/melamínico, me son/mesón, huengüe/wengué, conjalador/con jalador.
- Registrar texto original, interpretación propuesta, regla responsable y estado de revisión.
- No corregir automáticamente expresiones demasiado degradadas sin evidencia suficiente.
- No aplicar similitud indiscriminada a nombres comerciales, marcas, modelos, números o importes.
- No sustituir términos reconocidos por los valores esperados de los guiones de evaluación.
- Mantener las correcciones monetarias especializadas existentes y comprobar que no introduzcan regresiones.

## 9. Interpretación monetaria

- Reutilizar y consolidar el parser monetario existente para evitar gramáticas incompatibles.
- Corregir `find_ambiguous_price()` para que conserve importes completos escritos en cifras, palabras y expresiones mixtas.
- Impedir que «13 mil 200» genere un candidato monetario de 13.
- Reconocer «precio de mil cien bolivianos», «precio de 2 mil 500» y construcciones equivalentes.
- Mantener separados importe reconocido y modalidad comercial.
- Cuando se indique una cantidad explícita de uno y un precio inequívoco, permitir una sugerencia revisable aprovechando la equivalencia aritmética entre unitario y total, sin falsificar la modalidad pronunciada.
- Para cantidades superiores a uno y modalidad ambigua, conservar el importe y solicitar confirmación.
- Reconocer expresiones inequívocas de precio unitario y total, incluidas modalidades pospuestas como «por dos mil bolivianos en total».
- Conservar monedas, decimales, separadores, rectificaciones y conflictos.
- No cambiar importes pronunciados porque otro valor sea más habitual o coincida con el guion.
- Preservar las reglas comerciales de totales, descuentos y revisión humana del backend.

## 10. Conservación de especificaciones no estructuradas

- Identificar características técnicas que actualmente se pierden después de la extracción: garantía, procedencia, instalación, entrega, traslado, acabados, distribución, resistencia y condiciones de fabricación.
- Utilizar los campos estructurados existentes cuando sean semánticamente compatibles.
- Conservar el resto mediante atributos técnicos, descripción u observaciones revisables.
- Evitar duplicar información o copiar indiscriminadamente toda la transcripción como si fuera una extracción estructurada.
- Mantener siempre la transcripción original y su trazabilidad.
- Verificar que la información extraída llegue realmente al formulario y al flujo de revisión correspondiente.

## 11. Correcciones de catálogo

- Mantener separados los flujos de muebles a pedido y creación de productos de catálogo.
- Corregir nombres de sillas, pisos y zócalos que incorporan cantidades cotizadas.
- Reconocer el nombre comercial de pisos flotantes cuando comienza por una cantidad en metros cuadrados.
- Corregir el truncamiento de códigos como `NF Guión 7,782`, que actualmente termina como NF-7.
- Un código debe reconocerse completamente o quedar pendiente; no aceptar fragmentos como códigos completos.
- Mejorar interpretación de modelos alfanuméricos cuando la evidencia lo permita.
- No reconstruir letras ausentes de códigos como D81A o NA9174 sin evidencia suficiente.
- Admitir capacidades de carga, ángulos, giro y demás especificaciones soportadas tanto en números como en palabras.
- Detectar valores técnicos atípicos, como 80 mm de espesor para un piso flotante, solicitando confirmación en lugar de sustituir automáticamente el número.
- Mantener las cantidades cotizadas separadas de las existencias.
- Conservar información técnica de zócalos y otros productos mediante las estructuras compatibles existentes.
- No crear productos, marcas, colores o referencias comerciales ficticias.

## 12. Contratos, backend y frontend

- Inspeccionar los contratos Pydantic, `apps/capturas/nlp/adapter.py`, `proyeccion_prf03.py`, `revision_voz.py`, `catalogo.py` y las rutas reales de consumo.
- Preservar la singularidad de la propuesta comercial y la compatibilidad contractual.
- Reutilizar los mecanismos de evidencia y revisión existentes para representar inferencias, cuando sean suficientes.
- Si una ampliación contractual es indispensable, justificarla y actualizar coordinadamente todos los consumidores estrictos, esquemas, serializers y pruebas.
- Verificar que los candidatos inferidos no se presenten como datos explícitamente pronunciados.
- Comprobar la proyección de dimensiones, componentes, materiales, colores, nombres, cantidades, precios y observaciones.
- Verificar `StagedVoiceCapture.vue`, `capturaAsistidaMapper.ts`, `MuebleStudio.vue`, `ProductoForm.vue` y los consumidores reales encontrados.
- Reproducir en navegador los muebles con pocas especificaciones y comprobar que los campos reconocidos se aplican correctamente.
- Los campos ausentes deben permanecer pendientes o vacíos; no impedir la extracción parcial por requisitos propios del guardado definitivo.
- Mantener permisos, validaciones comerciales, idempotencia, trazabilidad y revisión humana.
- Realizar las pruebas de navegador y persistencia en un entorno aislado, sin modificar datos comerciales reales.

## 13. Pruebas de regresión y casos dirigidos

- Reproducir los defectos identificados mediante pruebas RED antes de implementar las correcciones.
- Ejecutar las 50 pruebas dirigidas incluidas en la auditoría.
- Ampliar con casos independientes que incluyan combinaciones nuevas de productos, medidas, componentes, materiales y accesorios.
- Incorporar pruebas positivas, negativas, ambiguas y casos de frontera.
- Probar variantes singular/plural, puntuación ausente, acentos, espacios y representaciones numéricas alternativas.
- Probar explícitamente que no se generan precios, cantidades, unidades, códigos o componentes incorrectos.
- No modificar expectativas existentes solamente para que la nueva implementación pase.
- Ejecutar las suites automatizadas de NLP, backend y frontend.
- No volver a ejecutar el reconocimiento ASR ni la evaluación histórica de los 120 audios anteriores.

## 14. Evaluación diferencial del lote 02

- Comparar la línea base auditada y la versión candidata sobre exactamente los mismos 38 guiones y las mismas 38 transcripciones congeladas.
- Evaluar por separado guion→NLP, ASR→NLP y proyección integrada.
- No mezclar resultados de pruebas dirigidas con métricas de audios reales.
- Conservar respuestas completas, candidatos, asociaciones, advertencias y resultados por identificador.
- Revisar especialmente los 22 muebles a pedido.
- Informar mejoras, regresiones, campos incorrectos, omisiones y abstenciones justificadas.
- Evaluar exactitud de identidad, dimensiones, unidades, ámbitos, cantidades, materiales, colores, importes y códigos donde exista una referencia suficiente.
- Diferenciar datos explícitos, inferidos, ambiguos, no soportados y pendientes.
- No calcular precisión, recall o F1 definitivos utilizando anotaciones incompletas.
- No afirmar validación independiente cuando los mismos 38 casos hayan servido para desarrollar las mejoras.
- Medir latencia NLP antes y después en condiciones comparables, con múltiples repeticiones y reporte de mediana y percentil 95.
- No introducir degradaciones injustificadas de rendimiento.

## 15. Criterios de aceptación y cierre

- Aspirar a recuperar todos los muebles legítimos de los 22 guiones, siempre que su identidad y composición estén suficientemente sustentadas.
- Para las transcripciones ASR, recuperar toda propuesta justificable por el texto real; no forzar 22/22 mediante invenciones.
- Resolver los siete casos críticos identificados o documentar una causa residual legítima y reproducible.
- No truncar números compuestos, dimensiones ni códigos comerciales.
- No introducir errores nuevos de importe, cantidad o asociación.
- Demostrar que las inferencias de unidades son revisables y no se confunden con datos explícitos.
- Confirmar que los casos simples funcionan de extremo a extremo.
- Verificar que las mejoras no perjudican las restantes categorías.
- Superar pruebas unitarias, contractuales, integración, lint, esquemas y build.
- Construir el wheel de distribución y verificarlo en un entorno limpio.
- Incrementar la versión del paquete y la identificación de reglas conforme al estado real del repositorio.
- Actualizar el backend consumidor, dependencias fijadas, hashes y documentación de despliegue.
- Verificar la versión realmente cargada durante la ejecución.
- No declarar definitiva la versión si existen regresiones comerciales críticas o pruebas fallidas.

## 16. Entrega de evidencia

- Generar `~/Descargas/HOMEX_NLP_Implementacion_Final_Lote02.zip`.
- Incluir identidad exacta de línea base y candidato, commits, diferencias de código, inventario de reglas modificadas, pruebas RED/GREEN, resultados completos de los 38 casos, comparación diferencial, evidencia de integración, métricas de rendimiento, wheel, hashes, logs y comandos de reproducción.
- Incluir capturas y evidencia de las pruebas reales del navegador.
- Entregar un resumen por problema identificado, causa raíz, corrección aplicada, resultado y riesgo residual.
- Incluir los casos que sigan fallando, sin ocultarlos ni ajustar artificialmente sus resultados.
- Excluir secretos, credenciales y datos ajenos a la evaluación.
- Mantener el trabajo candidato identificable mediante commits separados. Publicar la rama de trabajo para revisión, sin promover todavía la nueva versión a producción ni fusionarla definitivamente a main hasta superar la auditoría final.
- No alterar el corpus histórico ni sus resultados.

El objetivo no es conseguir únicamente más coincidencias textuales: es obtener propuestas comerciales técnicamente correctas, contextualizadas, trazables y utilizables para HOMEX.

### L2 — Authorization and initial evidence

User answered "si" to explicit GitHub CLI session authorization: fetch references and publish candidate branches only in gabriel-arinez/{homex-nlp,homex-backend,homex-frontend,homex-deploy}; no SSH, merge or deployment. Four HTTPS fetches succeeded through gh. BaselineZIP SHA256285db839fe0a652819ccd1eeefe84bb849e44bb67693ac1a807d8cc5336c11f0 verified. NLPHEAD a73c462 matches origin/main; backend5d91605 and frontend aee2058 match origin/main. Deploy worktree starts from updated origin/main0175b50, not dirty older checkout. All original checkout state/hashes recorded externally. RDD mode globaloff remains unchanged. Forecast roughly1800–3000authored changed lines including regression tests across behavior units; commit budget advisory, never a reason to omit tests or minify. User delivery is branch publication for final audit, not PR creation; PR slicing decision remains outside this requested delivery.

### L3 — Parallel bounded implementation starts

T1 numeric/money/unit evidence and T4 catalog names/codes run together in one NLP candidate tree with declared disjoint edit surfaces. Parent owns git, task document and later identity/relations changes. Existing parser signatures and raw text/spans remain invariants; no worker runs installs/global normalizers/ASR/history or commits. Parent will run a seam check after both handoffs.

### L4 — T1/T4 observed checks and commits

T4 RED13fail/3pass; final scoped207pass; commit e7a9de5(238authoredlines). T1 RED18fail/5pass; scoped305pass; commit d9b7c9d(627authoredlines): coherent shared magnitude replacement, contextual units and regression coverage kept together rather than omitting tests or shrinking code. Parent normalization then joint48newtests passed. Public parser differential preserved prior explicit money/axes and malformed-compound behavior. Qty1 ambiguous amount remains unresolved with arithmetic-equivalence reason; consumer suggestion still T5. Native assess returned typedunassessable due untracked inventory; risk remains nameditem3 and feature-end independent verifier required. RDDglobaloff: no reviewSTART/consent. Baseline NLP admits4minimalinputs; real isolatedbackend rejectsall4HTTP400(20wordminimum); actualChromium shows4disabledapplybuttons and screenshots. Browser uses expliciteditabletextstate testseam, notASR/microphone; subsequentDOMinteraction andAPI are real. No commercial records. Initial harness failures(Pathsettings type/missingstartupscript/overstrictbuttonlocator)logged and resolved without productionchanges.

### L5 — Resume, identity and consumer boundary

User requested "continue" after interruption. Existing d9b7c9d/e7a9de5 and taskmirror reconciled; only newworktrees/scratch touched. T2 RED33fail/7pass; final related128pass; commit6a27475(507authoredlines, finite runtimelexicon plus literal-span recovery and independent regressions kept with behavior). T3 RED12fail/6pass; scopedrelations106pass; development-only38text replay exposed newlyrecognized filing-function nouns as falsemainproducts, corrected generally via component/function context and plural head normalization; independent3caseRED/GREEN added. Numericfollowup preserves shared18and36gauges and prevents physicalunits being consumed as monetaryprefixes. Backendpartial unit20newpass; related58pass/3superseded20wordpolicyfailures retained pending explicit S2/S12 expectation update, not commercial guard relaxation. T5 consumer unit delegated for long-session context backstop: exact backend/frontend surfaces; parent retains git, NLP and actual isolated-browser driver. No token-counter or runtime limit is claimed.

### L6 — Compositions and geometry checked

T3 public scoped146pass at32f3824; material/cardinal and per-side/color/range regressions included. Development38 replay now22/22scriptproposals. Two remainingASRabstentions exposed comma/period-dependent repeated descriptions; source-general regression uses spatial reception top and previouslyintroducedsideboard, while a freshlycountedsideboard remainsindependent. ScopedASR-pause regression proof logged separately. This is development recovery, not semantic/acoustic accuracy or independentvalidation. Originaltranscripts neverrewritten, numbersnotchangedtomatchscripts. Fullsuite and consumerproofstillpending.

### L7 — Broad proof exposes blockers; not a release

NLPsafe suite atfce3c92:1316pass/36fail; Ruffcheck/format andv1schemasPASS; sixevaluationfilesexcluded(noASR/historicalrun), backendconsumertestdeferred. Failuresinclude real thickness/correction, malformedcompoundgrammar, dimensionscope, componentfalsepositive and catalogobservationregressions; only explicit S3fraction/S4reviewableunitinference expectations may be legitimatelysuperseded. Triagefirstcandidate367pass usedwrongsourcebinding andisINVALID; verifiedcandidatepathrerun reproduced36fail/331pass. Triageworkerimproperofflineuvprovisioning createdcandidate.venv(54existingpackages), no tracked/originalsourcechange; logdisclosed, neverusedasproductionenvironment. CorrectiveNLPunitdelegatedforlong-sessioncontextbackstop; one boundedall-blockercorrection andscopedrecheck, no fakegreen. T5consumerfocusedbackend101pass+6trusted-auditpass, frontend42pass; keepscorrectexplicit110/65cm and36mm whileinferredotheraxis/gaugepending, optionalexistingvalor marker enforcedbyfrontendandserver. Riskitem2addedforhuman-reviewguard. Parentbrowser/fullconsumerbuild/independentverification/releaseevidence remainpending.

### L8 — Consumer unit frozen for full integration

Parent guard4pass and frontend review6pass confirm handoff; backend b94d9a9/frontend6adba39 committed. Regressionclosure worker launched with exactsourcebinding, noinstalls/ASR; T1–T4 remainreopened. Distributionmap read-only. Riskitems2/3 require independentfeature-endverifier; RDDremainsoff.

### L9 — Candidate checks and semantic closure

Correctiond89f1e6 parent16pass; alignedNLP1367pass, cleanofflinewheel/sdistrebuildPASS;0.1.31/context3 candidate notfinal. Frontend494pass after documentedtestAPIenv and externalnode_modules fsallow; earliermissing-env/path-denial failures retained asinvalidharnessproof. ESLint/Oxlint/format/types/buildPASS. Actualbrowser4minimalapplied, noAPIcommercialwrites; inferred90/43/70casekeeps explicit90cm while43/70blank withtypedreviewmessages. Wheel-based108backendflows complete38cases, commercialcountsremainzero. Semanticreviewexposed residualheight/gauge/owner regressions despite22/22proposalcounts; furtherboundedclosure required beforefinality. Backendcollectionlostpublictoken-countutility; restoredidenticalpurehelper withoutminimumgate, fullsuitepending.
