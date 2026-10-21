# HOMEX — PRF-04: especificación técnica NLP/ASR

**Estado:** propuesta técnica para aprobación, sin código implementado. Se rige por `PRF_04_CONTRATO_COMPARTIDO.md` y por las decisiones funcionales PRF-04.1–04.5 aprobadas.

**Baseline de lectura:** `homex-nlp/main@dbfc80a3d2c6628fc5051658e5fd8d34668ce921`, verificado 21-10-2026.

## 1. Hallazgos del repositorio actual

- `src/homex_nlp/engine.py`: `RulesEngine` actual. `src/homex_nlp/rules.py`: detección de productos, cantidades, precio, medidas, espesores y accesorios mediante reglas; las relaciones complejas todavía requieren implementación/evaluación.
- `src/homex_nlp/contracts/{input,item,evidence,result}.py`: `ExtractionRequest` y `ExtractionResult` **estrictos**; `ItemProposal` singular; `EngineInfo.mode` ya enumera `RULES_ONLY`/`HYBRID`. Candidatos con `candidate_id`, spans exactos sobre `text_original`, `source` y `decision`.
- `src/homex_nlp/asr/`: transcripción con `faster-whisper`, modelo local, audio efímero; documentación F05 constata que falta WER de dictados reales.
- `training/`: validación de spans, conversión spaCy DocBin, particiones por familia, entrenamiento NER y evaluación P/R/F1. El experimento histórico NER dio F1 test **0,1348**; no está promovido.
- `data/corpus/`: cuatro corpus recientes, **675 registros sintéticos** comprobados en `main`: `muebles_pedido` 380, `sillas` 101, `pisos_flotantes` 97, `otros_productos` 97. No tratarlos como muestras reales revisadas.
- `Makefile` todavía valida `data/curated/homex_original_v1.jsonl` y `catalogo_sillas_v1.jsonl`; `tests/training/` y `training/policies/annotation_guide.md` documentan flujo antiguo. Reemplazarlos integralmente.
- La liberación operativa fija en backend `homex-nlp 0.1.0`, `ExtractionResult.schema_version == '1.0'` y `RULES_ONLY`; actualizar consumidor y empaquetado coordinadamente, sin cambiar silenciosamente la versión en producción.

## 2. Corpus: consolidación definitiva y limpieza aprobadas (PRF-04.2)

**Únicas cuatro fuentes activas:** `muebles_pedido`, `sillas`, `pisos_flotantes`, `otros_productos`.

Acciones obligatorias:

1. Inventariar todos los corpus, metadatos, particiones, scripts, fixtures y referencias de CI/documentos. Reconciliar las diferencias entre corpus AP6.0.21, fuente real del usuario y cuatro corpus actualmente versionados. Dar cuenta explícita de registros faltantes/sobrantes o modificados.
2. Antes de borrar versiones anteriores, verificar que el contenido auténtico aprovechable ha sido incorporado a las fuentes nuevas y revisado. No confundir `SINTETICO` con `REAL`, ni llamar a `PREANOTACION` una verdad de entrenamiento. No conservar copias obsoletas dentro del árbol activo o un directorio `legacy` operativo: **eliminar archivos antiguos** después de migrar las dependencias; el historial Git conserva su trazabilidad.
3. Auditar manual y programáticamente spans Unicode `[start,end)`, etiquetas permitidas, ausencia de cruces no válidos, identificadores, hashes, moneda, familia, procedencia, duplicados exactos y paráfrasis entre particiones.
4. Corregir etiquetas insuficientes para `COMPONENTE`, `MATERIAL`, `ESPESOR`, `COLOR`, `ACABADO`, `ACCESORIO`, dimensiones, cantidades comerciales e internas; evaluar incorporación controlada de `CANTIDAD_INTERNA`. Diferenciar accesorios independientes de herrajes/atributos internos sin hacer proliferar etiquetas innecesarias.
5. Vincular cada ejemplo a una **salida estructurada esperada revisada**, separada de los spans NER y con un ID estable: `expected/comercial` y `expected/especificacion` cuando sea mueble; referencias comerciales propias para sillas, pisos y otros. El JSON de salida se evalúa/ensambla por la capa semántica; **NER spaCy por sí solo no aprende a producir JSON estructurado**.
6. Alinear la salida mueble a PRF-03: `datos_tecnicos.caracteristicas_generales.dimensiones`, `conjuntos` con UID/relaciones, `componentes` con `cantidad_interna` y `atributos[]`, `accesorios[]`, `advertencias[]`, `descripcion_original`; **nunca** `schema_version` en el JSONB comercial.
7. Introducir ejemplos de **habla natural**: «seis veladores, cada uno dos cajones», pausas, rectificaciones, unidades habladas, variantes regionales, orden variable, información omitida y casos ambiguos. Generar contrastes negativos, no entrenar solo frases de cotización sintética estereotipada.
8. Crear particiones por familia/proforma/plantilla o grupos semánticos: no permitir que paráfrasis casi idénticas se filtren a `train` y `test`. Bloquear `test` antes de comparar motores, versionar manifiestos/hashes; no reutilizar el test histórico como conjunto de ajuste.
9. Actualizar `Makefile`, `training`, tests, guías, manifiestos y workflows para referenciar únicamente los nuevos corpus activos; los cuatro pasan validación formal aunque el alcance funcional inicial sea **solo muebles a pedido**.

**Salida de T1:** manifiesto reproducible (conteos y origen), guía de anotación aprobada, fixtures NER + `expected` estructurados, cuatro validadores verdes y evidencia de cero rutas dependientes de corpus eliminados.

## 3. Arquitectura NLP a comparar (PRF-04.3)

| Variante | Componentes | Uso |
| --- | --- | --- |
| A | `RulesEngine` **mejorado** con relaciones y validaciones | Baseline y respaldo, sin dependencia de modelo NER |
| B | NER spaCy entrenado + ensamblado semántico determinista | Experimento independiente |
| C | **Híbrido**: NER + reglas/normalización + resolución de conflictos + ensamblado estructural | Arquitectura preferente si supera gates objetivos |

No promover un NER por el solo F1; medir acierto de **campo completo, asociación a pieza correcta y productividad**. Mantener sinergia reglas/modelo sin duplicar propuestas o perder candidatos rechazados.

**Responsabilidades internas** (rutas orientativas, a contrastar con la arquitectura final):

- `training/`: curación, splits, conversión, entrenamiento reproducible, evaluación y comparación A/B/C.
- `src/homex_nlp/rules.py`/`engine.py`: reglas mejoradas y motor operativo A.
- Nuevo ensamblador semántico: compone `ItemProposal` desde evidencias y relaciones, no desde posiciones ciegas de listas. Debe separar `quantity` principal de cantidad de componentes.
- Gestión de `EngineInfo`: declarar modo realmente ejecutado y versiones exactas; si falta/fracasa modelo híbrido seguir política explícita, sin fingir que corrió NER.
- ASR continúa desacoplado, con audio temporal y transcripción original inmutable.

## 4. Reglas semánticas obligatorias

- Multiproducto comercial → `NO_PROPOSAL`; piezas de un mueble o conjuntos no son multiproducto comercial.
- «6 veladores con 2 cajones» → `quantity=6` y dos cajones por velador en la salida esperada; jamás 2 o 12 muebles.
- Medida sin eje → candidato no resuelto; valor `43 cm` con eje «ancho» puede asignarse sin advertencia. No suponer unidad ni orientación de `140x140`.
- «Tapa de melamina MDP 25 mm; panel frontal 18 mm» → referencia de espesor a componente respectivo. Material no explicitado en panel frontal permanece vacío.
- Color/espesor general → no propagar automáticamente a piezas si no existe una relación explícita.
- Conservación literal de evidencia: `start/end`, normalización exacta cuando la unidad es inequívoca, candidato rechazado con razón, ambigüedad en `unresolved`. Spans sobre **texto ASR original**; si el usuario corrige texto se genera otro intento/captura con nueva evidencia, sin editar el primero.
- Datos técnicos se proponen, **no** permiten inventar precio unitario; los precios dictados como total conservan su distinción semántica.
- Un `ExtractionResult` válido NO acredita una línea comercial guardable: sus datos incompletos podrán ser corregidos en PRF-03 antes de agregar.
- Sin porcentajes ni score en UI; las señales de advertencia deben ser estados verificables con motivo accionable, no `confidence` sin calibrar.

## 5. Contrato de versión y empaquetado

- Mantener contratos NLP versionados; `schema_version` de extracción ≠ versión `datos_tecnicos` (no existe).
- No añadir campos incompatibles a un Pydantic `extra=forbid` sin desplegar consumidor actualizado; cambio incompatible → versión mayor/documentación y pruebas; campo opcional compatible → versión menor documentada con adopción coordinada.
- `EngineInfo.mode='HYBRID'` solo cuando el NER realmente participó y `model_version` existe; `RULES_ONLY` conserva `model_version=null` y `rules_version` exacta.
- Distribuir wheel reproducible con manifiesto/hash, no cargar pesos desde Internet en runtime, evaluar memoria/CPU y regresión de latencia sobre hardware objetivo. Backend actualizará wheel/lock/adapter de forma atómica con contratos.

## 6. Evaluación y criterios de promoción

Medir y publicar: P/R/F1 micro/macro y por etiqueta; exactitud de `quantity`, unidad comercial, precio; exactitud de relaciones `(componente, atributo, valor)`; acierto de JSON esperado; porcentaje de capturas aceptadas sin correcciones; campos corregidos/añadidos/eliminados; tiempo hasta incorporar; latencia, memoria y WER ASR con audio real autorizado y transcripciones de referencia.

- **100 % de salidas propuestas al configurador deben superar validación estructural de contrato**, o rechazarse sin reemplazar el borrador. No equivale a 100 % exactitud semántica.
- Ninguna degradación material de cantidades/precios/asociaciones frente a A. Selección con `dev`, test independiente sellado una vez fijado candidato, y evaluación humana de casos complejos.
- Los objetivos numéricos de rendimiento semántico/productividad se fijarán **después de establecer baseline real reproducible y antes de elegir/promover candidato**, sin inventar porcentajes ahora.
- Si B o C no cumplen, conservar A mejorado; no instalar NER experimental en producción por obligación de completar fase.
- No guardar audios de vendedores para entrenamiento; si se realizan sesiones autorizadas, el audio es efímero y solo permanecen datos textuales/evaluaciones permitidas con controles de acceso.

## 7. Pruebas específicas

1. Integridad de cuatro corpus y expected targets; eliminación de referencias antiguas; aislamiento train/dev/test.
2. NER por etiquetas, negativos, abreviaturas, tildes, unidades mm/cm/m y expresiones habladas.
3. Componentes dobles con espesor igual/diferente y relaciones; conjuntos e internos; `PIEZA`/`JUEGO`.
4. Candidato ambivalente / medida sin eje, número sin unidad, colisiones, moneda incompatibles, precio total vs unitario.
5. `NO_PROPOSAL`, `ERROR`, texto vacío, multiproducto y ASR con fallo.
6. JSON esperado de velador, escritorio en L, escritorio con cajonera, conjunto modular y vitrina.
7. `ExtractionResult` con candidatos y offsets exactos, serialización Pydantic y tests consumidor backend.
8. Rendimiento hardware local y ausencia de audio/modelos secretos en wheel/sdist.

**Verificación de repositorio tras cambios:** `uv sync --locked --extra dev --extra asr --python 3.11.15`, `make check`, `make distribution-check`, `make backend-consumer-check`; correr `make docbin-check` actualizado, `git diff --check` y CI. Evidencias de entrenamiento/evaluación específicas adicionales; no presentar pruebas no ejecutadas como aprobadas.

## 8. Entrega y coordinación

**T1** corpus + validadores + muestras reales revisadas → **T2** motor A/B/C, evaluación, paquete candidato. No liberar automáticamente hasta que backend T3/T5 soporte contrato y despliegue. Presentar commits/PR, manifiestos de corpus/modelo, métricas, trazabilidad y comandos reproducibles. Respetar lo aprobado sin añadir voz a sillas/pisos/otros.
