# Correctivo metodológico PR #24 — análisis suplementario retrospectivo

**SUPPLEMENTARY_POST_HOC**, sin reentrenamiento ni cambio del protocolo predeclarado.
HUMAN_GOLD=NO; TEST_VOZ_REAL=NO; HOLDOUT_EXTERNO=0; PROMOCION=NO.
Recomendación: **mantener RULES_ONLY**, sin afirmar precisión de campo.

El informe original comparaba A/C ACCEPTED con B raw: son vistas diferentes y
sus F1 no acreditan una mejora comparable. Se conserva íntegro abajo como histórico;
el correctivo y el nuevo results.json distinguen explícitamente ambas vistas.
`results.json.historical_report` mantiene todos los valores originales; el nuevo
`supplementary_post_hoc` contiene TP/FP/FN/P/R/F1, documentos/entidades/grupos y
soporte por etiqueta/familia en ambas vistas. Etiquetas sin soporte tienen null,
no F1 perfecto. Ningún dato, peso, motor ni referencia fue modificado.

| Vista comparable, 16 muebles / 98 entidades / 11 grupos | Motor | TP | FP | FN | P | R | F1 |
|---|---|---:|---:|---:|---:|---:|---:|
| ACCEPTED | A v13 | 33 | 15 | 65 | 0.6875 | 0.3367 | 0.4521 |
| ACCEPTED | B NER | 26 | 12 | 72 | 0.6842 | 0.2653 | 0.3824 |
| ACCEPTED / veto | C híbrido | 33 | 15 | 65 | 0.6875 | 0.3367 | 0.4521 |
| Todos los candidatos | A v13 | 37 | 18 | 61 | 0.6727 | 0.3776 | 0.4837 |
| Todos los candidatos | B NER | 51 | 21 | 47 | 0.7083 | 0.5204 | 0.6000 |

B supera a A en raw F1 y queda por debajo en accepted F1 y campos comerciales.
C solo se informa en la vista aceptada/veto: sus candidatos REJECTED de auditoría
no son raw NER equiparable a A/B. No se atribuye causalidad ASR ni significación
estadística. Los 11 auxiliares fuera del alcance de voz se separan en el agregado.

## Independencia: corrección de la certificación

`comparison` canonicaliza rutas con Path.resolve y rechaza el mismo directorio,
symlinks y alias con `..`. Se separan `evaluations_supplied`, directorios distintos,
`distinct_artifacts` (pares de archivos predicciones/rendimiento por contenido) y
`independent_runs_verified`. Ni rutas distintas ni hashes iguales prueban procesos
independientes. Copias idénticas cuentan como un conjunto de artefactos.

Para eval-1/eval-2 históricos: dos directorios y dos conjuntos de artefactos
(las mediciones difieren); predicciones/pesos idénticos. **Independencia UNVERIFIED,
0 procesos certificados**, porque no hay IDs de proceso/ejecución confiables unidos
a entrenamientos distintos. Los logs de finalización, tiempos y los training.json
son evidencia conservada, pero no proporcionan esa cadena. No se inventan metadatos
a posteriori. `independent_evaluation_processes=null` conserva el nombre legado
sin volver a contar rutas como procesos. Los informes originales con valor2 son
históricos, no una certificación vigente. No se realizaron nuevos fits ni inferencias.

## Reproducción del suplemento, sin entrenamiento ni carga de modelos

Con el código del correctivo y el paquete original privado extraído:

```bash
export TASK_ORIGINAL="$HOME/Descargas/HOMEX_EXPERIMENTO_RC2_V13_20261026"
export TASK_SUPPLEMENT="$HOME/Descargas/HOMEX_CORRECTIVO_PR24_20261026"
uv run --locked --extra dev python -m training.offline_rc2_v13.cli supplement \
  --evaluation-dirs "$TASK_ORIGINAL/eval-1" "$TASK_ORIGINAL/eval-2" \
  --preflight "$TASK_ORIGINAL/predeclared.json" \
  --output "$TASK_SUPPLEMENT/supplementary-repeat.json"
```

Solo se leen DTO sellados mediante el adaptador `worker.evidence` sin cambiarlo.
Cada vista se recalcula con las mismas referencias técnicas y partición dev.
SHA-256 original de predictions.json de ambas rutas:
`2d28ea71fa1109323f4e25ff9e9bc428441a1eea87225440f5bc088d7a0824ab`.
El suplemento registra estos hashes y el digest de modelo/protocolo. No es un
experimento prospectivo nuevo ni modifica seeds/epochs/config/modelos.

Pruebas de regresión: B UNRESOLVED se excluye en accepted y se incluye en raw;
C raw omitido; duplicados/alias rechazados; copias sin procedencia y mediciones
distintas sin autenticación permanecen UNVERIFIED; protocolos/modelos incompatibles
siguen rechazados. La entrega privada aporta pruebas fallidas antes del parche,
los cuatro recuentos con los DTO reales y el pase posterior sin reentrenamiento.

## Informe original preservado — histórico del commit 3dcb8d8

Las tablas y afirmaciones que siguen reproducen la entrega original. Su comparación
NER mezclaba vistas y su afirmación de independencia no está certificada; se
interpretan únicamente con las correcciones anteriores. Para el resultado vigente,
consultar el suplemento. No se han borrado las cifras anteriores.

---

# Experimento offline limitado RC2 / v13 — etapa 6

Estado: **EXPERIMENTO_OFFLINE_LIMITADO_EJECUTADO**. Recomendación: **mantener RULES_ONLY**.
HUMAN_GOLD=NO; TEST_VOZ_REAL=NO; HOLDOUT_EXTERNO=0; PROMOCION=NO.
No equivale a NER_VALIDADO_EN_CAMPO, WER, benchmark ciego o APTO_PRODUCCION.

## Fuentes y protocolo congelado

Base de herramientas: PR #23 `9b2d57d145c09d6ac354ee3d8ecef4f294db94ee`.
Datos RC2: #22 `b27edfa522f08c4621d31113b14295ece08e2109`, intactos.
Motor A: #21 `27aad1f4dc1e29093317a8a5ebf04a730496b325`, 0.1.12,
`prf04-rules-v13`, contrato 1.0. Wheel aprobado SHA-256:
`abeee2738b4b6c81d8428e244dddc3cbf0555c06fe00137a6f34d0e1801d4c69`.
Se extrajo literalmente del vendor del Backend #37 aprobado, sin modificarlo;
los .py instalados se cotejaron byte a byte con el wheel y con el commit de #21.
No se recompiló ni etiquetó v12 como v13. Los intérpretes están separados:
checkout/CI mantiene 0.1.11; experimento usa exclusivamente el wheel 0.1.12.

`config.json` fija hashes de RC2 completo, expected, etiquetas, lock y ensamblador.
Verificar hashes de archive_v1 no significa entrenar con sus textos. El optimizador
solo recibe **39** registros de development_v2/train, cuatro familias, **22 muebles**.
Dev: **27**, exclusivamente evaluación; **16 muebles operativos**, 11 auxiliares
(sillas/pisos/otros fuera del alcance aprobado de voz). Grupos train/dev: 27/19,
46 en total, sin cruzar IDs/casos/plantillas/paráfrasis/grupos. Holdout/gold: cero.
No entran V1, RC1, fuentes privadas, guiones de evaluación, audios ni laboratorio.

Configuración declarada antes de evaluar dev: semilla **606**, spaCy **3.8.13**,
Python **3.11.15**, blank es + ner por defecto; **20 épocas**, minibatch 8, dropout
0.2, CPU, OMP_NUM_THREADS=OPENBLAS_NUM_THREADS=1. Orden determinista con shuffle
sembrado. Se guarda solo checkpoint final; no evaluación dev por época, early
stopping, selección por dev, búsqueda de parámetros, aumento de datos o replicaciones
presentadas como muestras independientes. Dos repeticiones finales, misma configuración.
No se retocó el candidato al observar dev. Tamaño/condiciones están en results.json.

## A/B/C y comparabilidad

- **A:** RulesEngine auténtico v13, sin cambios. NER diagnóstico: candidatos ACCEPTED
  dentro de las 24 etiquetas RC2; PRECIO genérico solo se mapea si el modo de precio
  estructurado es inequívoco. Etiquetas no mapeadas quedan auditables privadamente.
- **B:** spaCy entrenado solo con train RC2. Reutiliza sin modificar
  `training/experimental_engines.py::NerExperimentalEngine` como ensamblador.
  Su NER se puntúa sobre **todos los spans estadísticos**, también cuando el
  ensamblador se abstiene; no se esconden falsos positivos en negativos.
- **C:** híbrido de veto conservador. Reutiliza B como dependencia, parte de la
  estructura v13 y nunca resucita un rechazo de A. Si ambos proponen y discrepan
  en producto, se abstiene de propuesta; cantidad/precio/moneda conflictivos se
  vacían con advertencias y se invalidan totales derivados. NER no rellena faltantes
  de A ni asigna componentes por posición. Evidencias B se conservan REJECTED para
  auditoría, no como unión aceptada. Se valida ExtractionResult 1.0 tras ensamblar.
  No se reutiliza HybridExperimentalEngine original porque puede heredar cantidades
  o precios de B cuando A se abstiene. En este dev **no se activó ningún veto**:
  C no demuestra mejora respecto a A. Eso no prueba que el veto sea innecesario.

El NER de A/C es evidencia aceptada de reglas; B es NER estadístico crudo. Son vistas
explícitas distintas del mismo esquema de etiquetas/offsets; no medir como mejora
productiva una diferencia de políticas. En auxiliares A/C se abstienen por alcance:
F1 bajo allí no demuestra regresión en el objetivo PRF-04. Las referencias son
**técnicas sintéticas no homologadas**, no anotación humana ni proformas reales.

NER: TP/FP/FN, P/R/F1 micro/macro por etiqueta y familia. Razón indefinida=null;
ningún F1=1 por ausencia de entidades. Cada etiqueta incluye documentos, entidades
y grupos de referencia del subconjunto evaluable. Familias sin soporte no prueban
inaplicabilidad universal. Muchas etiquetas tienen solo 1–2 casos/grupos dev.

Comercial, solo muebles: comparación literal casefold/espacios y Decimal exacto,
sin convertir unidades/monedas ni corregir expected. Nombre, venta, unidad,
unitario/total explícito, dimensiones con eje/unidad, componente-nombre y atributos,
y nombres de accesorios cuando hay pares válidos. Componentes se vinculan por nombre
literal único, nunca por índice. Campo ambiguo/no representable produce NOT_EVALUABLE.
Cantidades de capacidad/internas, descuentos comerciales y cantidades de accesorios
no tienen pares contrato/referencia suficientes: no se inventan métricas para ellos.
Moneda de Condiciones es contexto suministrado (BOB salvo moneda explícita de caso),
no extracción acertada por el modelo; se comprueba consistencia de moneda del precio,
no precisión contra una moneda gold cuando expected es null. No hay proyección Backend.

Los cinco campos comerciales raíz tienen ausencias explícitas bajo la política
RC2 SIN_EVIDENCIA_NO_COMPLETAR. Otras claves no generan un universo de TN: se consideran
hechos esperados y afirmaciones observadas. Exactitud=correctos/positivos esperados;
omisión=omisiones/positivos esperados; falsa afirmación=incorrectos/positivos emitidos.
Abstenciones se cuentan separadas. Error crítico=error por clave revisada (incluye
falsas afirmaciones), denominador unión revisada/esperada/emitida salvo color/acabado;
puede diferir entre motores: no confundir estas tasas con un test estadístico pareado.
Relaciones incluyen nombre y atributos ligados al componente, no asignación ordinal.
Negativos de propuesta: reference.status NO_PROPOSAL o nombre null, no falsos gold.

## Reproducir (Ubuntu / uv; entrenamiento manual)

Preparar dependencias y fuente v13 antes de desconectar red. En clon nuevo con toda
la historia del PR, obtener el commit v13 sin fusionarlo:

```bash
git fetch origin 27aad1f4dc1e29093317a8a5ebf04a730496b325
uv sync --locked --extra dev --python 3.11.15
export TASK_ROOT="$PWD"
export TASK_PRIVATE="$HOME/Descargas/homex-offline-rc2-v13-repro"
install -d -m 700 "$TASK_PRIVATE"
uv export --locked --extra dev --no-emit-project --format requirements-txt > "$TASK_PRIVATE/requirements.lock.txt"
uv venv --python 3.11.15 "$TASK_PRIVATE/v13-env"
uv pip sync --python "$TASK_PRIVATE/v13-env/bin/python" "$TASK_PRIVATE/requirements.lock.txt"
# Obtener el wheel exacto del paquete privado; verificar SHA antes de instalar.
sha256sum "$TASK_PRIVATE/homex_nlp-0.1.12-py3-none-any.whl"
uv pip install --python "$TASK_PRIVATE/v13-env/bin/python" --no-deps "$TASK_PRIVATE/homex_nlp-0.1.12-py3-none-any.whl"
export PYTHONPATH="$TASK_ROOT"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
"$TASK_PRIVATE/v13-env/bin/python" -m training.offline_rc2_v13.cli prepare \
  --wheel "$TASK_PRIVATE/homex_nlp-0.1.12-py3-none-any.whl" --output "$TASK_PRIVATE/predeclared.json"
# ÚNICA entrada que autoriza entrenamiento; falla con CI o guard de datos activo.
"$TASK_PRIVATE/v13-env/bin/python" -m training.offline_rc2_v13.cli train --allow-training \
  --preflight "$TASK_PRIVATE/predeclared.json" --wheel "$TASK_PRIVATE/homex_nlp-0.1.12-py3-none-any.whl" \
  --output "$TASK_PRIVATE/train-1"
"$TASK_PRIVATE/v13-env/bin/python" -m training.offline_rc2_v13.cli evaluate \
  --wheel "$TASK_PRIVATE/homex_nlp-0.1.12-py3-none-any.whl" --model-run "$TASK_PRIVATE/train-1" --output "$TASK_PRIVATE/eval-1"
"$TASK_PRIVATE/v13-env/bin/python" -m training.offline_rc2_v13.cli summarize \
  --predictions "$TASK_PRIVATE/eval-1/predictions.json" --output "$TASK_PRIVATE/summary-1.json" \
  --private-detail "$TASK_PRIVATE/differences-1.json"
```

Repetir entrenamiento/evaluación exactamente con destinos nuevos train-2/eval-2,
sin sobrescritura, cambiar datos, seed, epochs o elegir el mejor por dev. Producir
la comparación completa, incluidos rendimiento y procedencia:

```bash
"$TASK_PRIVATE/v13-env/bin/python" -m training.offline_rc2_v13.cli compare \
  --evaluation-dirs "$TASK_PRIVATE/eval-1" "$TASK_PRIVATE/eval-2" \
  --preflight "$TASK_PRIVATE/predeclared.json" --output "$TASK_PRIVATE/comparison.json"
```

Comparar
model_files de training.json, predictions.json y summaries: idénticos aquí en dos
procesos independientes. No usar `uv run` del proyecto para ejecutar A/B/C: reinstalaría
el proyecto editable v12. Usar directamente el Python privado como arriba.
Los pesos y detalles viven fuera de cualquier Git, permisos restringidos.
El paquete privado incluye wheel/lock/bundles; v13-source.bundle permite importar
el commit v13 sin red mediante git fetch local en el clon, sin merge.

Validación **sin entrenar** en checkout original / CI:

```bash
uv run --locked --extra dev python -m training.offline_rc2_v13.gate --evidence /tmp/homex-offline-tools
uv run --locked --extra dev python -m training.benchmark_campo.gate --evidence /tmp/homex-benchmark-regression
uv run --locked --extra dev python -m training.corpus_v2_rc2.ci_gate --evidence /tmp/homex-rc2-regression
```

CI instala v12 base solo para contratos/stubs, no carga wheel v13 ni pesos NER. El
nuevo gate fija CI/guard, bloquea initialize/update/load reales y llama a pruebas
sintéticas/stubs. Publica solo result.json, no pesos, detalles, textos o fuentes.
Allowlist exacta de nuevos archivos y padre #23 para primer push. Producción/mixto
conserva CI histórica; secretos y dependencias siguen activos, sin skip-ci.
No modificar benchmarks/fixtures, V1/RC1/RC2, runtime, Backend/Frontend o laboratorio.

## Resultados y límites

Predicciones de las dos evaluaciones y resúmenes idénticos; los pesos finales también.
Hash predictions.json: `2d28ea71fa1109323f4e25ff9e9bc428441a1eea87225440f5bc088d7a0824ab`.
Tiempos/RSS fluctúan y se separan del hash de calidad. perf_counter por extracción,
p50 mediana, p95 nearest-rank ceil(.95*n). Primera llamada dev se separa de warm;
no es cold-start de ASR. La prueba de procedencia ya puede calentar reglas globales.
Carga NER medida aparte; RSS es máximo del proceso completo (intérprete/imports/
ambos motores), no memoria marginal por motor. C se mide como A+B+conciliación
secuenciales; no presentar solo el tiempo de merge como coste híbrido.

Las dos corridas finales son del mismo protocolo, sin selección. Dos intentos
previos con parámetros idénticos entrenaron pero fallaron al serializar pérdidas
float32; se conservan privadamente y no se evaluaron ni eligieron por dev. Se corrigió
la serialización, el manejo de la respuesta de validación y se exigió prevuelo.
Todos esos detalles técnicos se registran, no se ocultan como si hubiera un solo fit.

Las tablas siguientes son exploratorias. Más F1 de entidades de B no compensa por sí
solo peores cantidades/relaciones; C no aporta mejora aquí y añade coste. Con 27 dev,
16 muebles y cero gold independiente no hay conclusión robusta ni significación.
Continuar RULES_ONLY y obtener referencias externas homologadas antes de invertir
en una especialización mayor o promover candidato. BLOCKED_EXTERNAL: homologación
humana, voces consentidas, transcripciones fieles, benchmark independiente y productividad.

### NER por familia / alcance

| Alcance | Docs | Entidades | Grupos | F1 A | F1 B | F1 C |
|---|---:|---:|---:|---:|---:|---:|
| muebles_pedido | 16 | 98 | 11 | 0.4521 | 0.6000 | 0.4521 |
| AUXILIARY_NON_VOICE | 11 | 74 | 8 | 0.0000 | 0.6667 | 0.0000 |
| otros_productos | 3 | 18 | 2 | 0.0000 | 0.9412 | 0.0000 |
| pisos_flotantes | 3 | 23 | 2 | 0.0000 | 0.7556 | 0.0000 |
| sillas | 5 | 33 | 4 | 0.0000 | 0.4615 | 0.0000 |
| ALL_SYNTHETIC | 27 | 172 | 19 | 0.3000 | 0.6306 | 0.3000 |

### NER por etiqueta (27 sintéticos; detalle por familia en results.json)

| Etiqueta | Entidades ref | Grupos ref | F1 A | F1 B | F1 C |
|---|---:|---:|---:|---:|---:|
| ACABADO | 2 | 2 | 0.0000 | 0.0000 | 0.0000 |
| ACCESORIO | 6 | 5 | 0.0000 | 0.2500 | 0.0000 |
| ALTO | 2 | 2 | 0.0000 | 0.5000 | 0.0000 |
| ANCHO | 2 | 2 | 0.0000 | 0.6667 | 0.0000 |
| APOYABRAZOS | 2 | 2 | 0.0000 | 0.6667 | 0.0000 |
| CABECERA | 1 | 1 | 0.0000 | 0.0000 | 0.0000 |
| CANTIDAD | 21 | 15 | 0.3846 | 0.8235 | 0.3846 |
| CLASE_RESISTENCIA | 1 | 1 | 0.0000 | 0.0000 | 0.0000 |
| COLOR | 11 | 7 | 0.4286 | 0.6667 | 0.4286 |
| COMPONENTE | 13 | 5 | 0.6000 | 0.1053 | 0.6000 |
| DESCUENTO | 6 | 4 | 0.0000 | 0.8000 | 0.0000 |
| DIAMETRO | 1 | 1 | 0.0000 | 0.0000 | 0.0000 |
| ERGONOMIA | 2 | 2 | 0.0000 | 0.0000 | 0.0000 |
| ESPESOR | 3 | 3 | 0.5000 | 1.0000 | 0.5000 |
| LARGO | 2 | 2 | 0.0000 | 0.5000 | 0.0000 |
| MATERIAL | 10 | 8 | 0.5333 | 0.7000 | 0.5333 |
| OBSERVACION | 18 | 12 | 0.0000 | 0.3077 | 0.0000 |
| PRECIO_TOTAL | 9 | 7 | 0.0000 | 0.7778 | 0.0000 |
| PRECIO_UNITARIO | 9 | 7 | 0.2000 | 0.7778 | 0.2000 |
| PRODUCTO | 26 | 19 | 0.4118 | 0.5000 | 0.4118 |
| PROFUNDIDAD | 1 | 1 | 0.0000 | 0.0000 | 0.0000 |
| SISTEMA | 2 | 2 | 0.0000 | 0.0000 | 0.0000 |
| SOPORTE_LUMBAR | 1 | 1 | 0.0000 | 0.0000 | 0.0000 |
| UNIDAD_MEDIDA | 21 | 15 | 0.4444 | 0.9767 | 0.4444 |

### Campos comerciales evaluables (16 muebles; correctos/positivos esperados)

| Campo | A | B | C |
|---|---:|---:|---:|
| acabado | 0/2 | 0/2 | 0/2 |
| color | 0/6 | 1/6 | 0/6 |
| component_name | 6/13 | 1/13 | 6/13 |
| dimension_alto | 2/2 | 0/2 | 2/2 |
| dimension_ancho | 1/2 | 0/2 | 1/2 |
| dimension_diametro | 1/1 | 0/1 | 1/1 |
| dimension_largo | 0/1 | 0/1 | 0/1 |
| dimension_profundidad | 0/1 | 0/1 | 0/1 |
| espesor | 0/2 | 1/2 | 0/2 |
| material | 3/6 | 1/6 | 3/6 |
| product | 7/13 | 7/13 | 7/13 |
| sold_quantity | 5/11 | 2/11 | 5/11 |
| total_price | 0/6 | 1/6 | 0/6 |
| unit | 6/11 | 6/11 | 6/11 |
| unit_price | 1/3 | 0/3 | 1/3 |

### Rendimiento, corrida 1 (ms warm, n=26)

| Motor | p50 | p95 |
|---|---:|---:|
| A | 0.171 | 1.823 |
| B | 6.686 | 16.608 |
| C | 7.575 | 17.124 |

En los tres negativos sintéticos operativos, A/C se abstienen 3/3 y B 2/3.
El caso etiquetado multiproducto se reporta además con su denominador separado
(multiple_product_negatives / multiple_product_false_proposals en results.json).
Las diferencias por caso y valores literales están solo en el paquete privado.
No se adjudica causalidad de ASR: nunca intervino audio. Las hipótesis descriptivas
son fronteras/etiquetas/ensamblado NLP sobre referencias técnicas sin homologar.
