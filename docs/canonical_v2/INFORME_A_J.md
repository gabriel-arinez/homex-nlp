# HOMEX — informe de ejecución Corpus V2 offline y entrenamiento

Fecha: 27-10-2026. Base de implementación `2292a0c1a6c1c6b6969e4680d8219f4f3fc37432`; curación final `1209c44679f5b46ea6c68a5ef7f203463543f645`.

Se generó un corpus utilizable y se ejecutaron los diez entrenamientos previstos con los datos verificados. **No se declara completado el alcance íntegro de un corpus de cotizaciones completas con todas sus relaciones homologadas**: la parte auténtica aquí anotada está formada por extractos de ámbito cerrado; no hay test independiente ni revisión humana comercial nueva. Las limitaciones no se sustituyen por métricas sintéticas.

## A. Corpus final disponible

Versión `2.0.0-offline.3`: **339 registros**, 312 train / 27 dev, 24 etiquetas. 273 extractos literales auténticos y 66 casos sintéticos recuperados. Estilo documental 292 y oral sintético 47. No hay audios en entrenamiento. Todos los documentos auténticos quedan en train; sus variantes/extractos comparten grupo conservador. El dev conocido tiene 18 orales y 9 documentales sintéticos.

| Familia | Train | Dev | Total |
|---|---:|---:|---:|
| muebles_pedido | 187 | 16 | 203 |
| otros_productos | 16 | 3 | 19 |
| pisos_flotantes | 25 | 3 | 28 |
| sillas | 84 | 5 | 89 |

Los fenómenos y soporte por etiqueta/split están en `AUDIT.json` y `RESULTS.json`. Se conservan cantidades comerciales, dimensiones, componentes y espesores independientes, exclusiones/rectificaciones y negativos sintéticos. Las 24 etiquetas tienen presencia global; ese dato no garantiza suficiente soporte por familia ni por experimento. D3 solo tiene 29 ejemplos de entrenamiento y pierde cobertura de etiquetas.

## B. Material original HOMEX

Los tres documentos son auténticos. Se preservan byte a byte con permisos privados. Sus hashes son:

| Documento | SHA-256 |
|---|---|
| PROFORMAS.txt | `f9497615494ba59c8b76c79c21c5411bbc919aa895c1eff2cc70c88bec0b8020` |
| SILLAS-PISOS-OTROS.txt | `8e22fc29be4d2ed1d75d9745409df02c24cd953bca25a79dc06c083a77fd7ca0` |
| inventario de sillas.txt | `43417573bc0ec98b90d63de89bd9b7dab236760724bbe74377a03fd63d4a0089` |

Se inventariaron 120 bloques candidatos a ítem, **sin identificadores de proforma demostrados**. De 112 bloques se extrajeron 483 ocurrencias literales; deduplicadas, quedan 273 observaciones. Cada una mantiene documento → bloque → rango absoluto/líneas → offsets del extracto → anotación/expected y enlaces adicionales cuando el mismo literal aparece en varias fuentes.

Ocho bloques contienen anomalías: unidades sospechosas, número malformado o discrepancia de importes con cantidad ausente. Quedan segregados íntegros. Se corrigió un falso positivo del detector histórico: `0,80mts` no puede confundirse con `80mts`. No se arreglaron dimensiones ni importes por intuición. Los precios de catálogo y los negociados conservan campos/contextos distintos.

La correspondencia literal de V1 con los originales no está demostrada para sus 675 filas: se mantiene `NO_IDENTIFICADA`, sin recatalogarlas como documentación auténtica. No se inventaron proformas, autores, revisores ni transcripciones.

## C. Curación y conciliación

Se recuperaron selectivamente PR20/22/24/31 y se revisaron PR23/26/27/28/34/35. Los 66 RC2 incluyen los 52 nuevos RC1 (12 bases y 40 orales); no se suman otra vez. Los 675 V1 quedan como baseline, fuera de la nueva fuente canónica offline.

La historia conserva las **375 propuestas RC1** por registro y los 300 casos sin cambio propuesto. No se homologan ciegamente ni se aplican al test. Se auditaron técnicamente los 577 V1 train/dev; los 98 test solo se verifican como archivo/split protegido. Las **49 extensiones reversibles de ACCESORIO** quedan en overlay, sin editar V1. La matriz V1 tiene 49 estados CORREGIDO (overlay) y 626 PENDIENTE/protegido, sin fingir revisión humana.

Matriz final: 333 APROBADO técnicamente, 6 CORREGIDO (cinco fronteras de atributos y la segunda mención de melamina), 8 bloques originales PENDIENTE y un candidato previo DESCARTADO por título truncado. Tres IDs de extractos se renumeraron sin cambiar su contenido; se enlazan por bloque y offset absoluto en AUDIT.json. “APROBADO” aquí significa control técnico del ámbito anotado, no validación comercial humana. El piloto histórico de 48 frases no se recuperó; no se lo reemplazó silenciosamente con los 40 orales RC1.

## D. Pruebas y controles

- **470 tests** aprobados, incluidos 34 nuevos controles y mutaciones de offsets, etiquetas, hashes, solapes, precios, relaciones, grupos, unidades, privacidad y abstenciones.
- Ruff check y format, esquemas, corpus histórico y DocBin aprobados.
- Reconstrucción del bundle dos veces con **todos los hashes idénticos**, incluidos DocBin y originales.
- Auditoría privada de cada rango literal sin errores. Cero pares entre train/dev con Jaccard de 4-gramas normalizados ≥ 0,50; las alertas menores están reportadas. No se equipara este detector con independencia semántica probada.
- Distribución 0.1.15 reconstruida y verificada de forma reproducible; wheel y sdist fuera de producción.
- `uv audit --locked`: 70 paquetes auditados sin vulnerabilidades conocidas ni estados adversos.
- Gitleaks 8.30.1: se verificaron 20 falsos positivos de hashes públicos tokenizer/key2row en el primer commit de resultados. Los fingerprints exactos de commit/ruta/regla/línea se validan por test, sin excluir archivos ni reglas completas. Los nuevos manifiestos usan listas de digest y nombre de archivo para evitar la ambigüedad. El reescaneo está limpio y se preserva la historia.

Comandos ejecutados (logs y retornos bajo el directorio privado de evidencias):

```bash
make check docbin-check distribution-check
uv audit --locked
uv run python -m training.canonical_v2.build --output <bundle-privado-nuevo> --sources <tres-originales>
uv run python -m training.canonical_v2.validate <bundle>
uv run python -m training.canonical_v2.audit <bundle> <auditoria-nueva>
gitleaks git . --log-opts origin/main..HEAD --redact
```

Los intentos fallidos se conservaron: serialización de pérdidas NumPy, advertencia obligatoria de cantidad en una ablación y soporte de dimensiones textuales en un validador ampliado. Se corrigieron y se añadieron regresiones. No se deshabilitó ningún gate. Las evaluaciones finales usan el código corregido y modelos cuyos hashes se comprobaron al reanudar.

## E. Entrenamiento ejecutado

CPU, spaCy 3.8.13, dependencias fijadas en uv.lock, OMP/BLAS/MKL=2, semillas 404/405, batch 8, dropout 0,2. Máximo 25 épocas; parada por paciencia 6 tras mínimo 8; selección por F1 NER bruto dev, primer checkpoint ante empate. Ningún test fue utilizado por el optimizador o la selección.

| Datos | Seed | Train únicos | Épocas | Checkpoint | F1 bruto dev | Segundos |
|---|---:|---:|---:|---:|---:|---:|
| D1 | 404 | 483 | 22 | 16 | 0.3894 | 113.57 |
| D1 | 405 | 483 | 20 | 14 | 0.3826 | 101.04 |
| D2 | 404 | 283 | 22 | 16 | 0.5151 | 15.52 |
| D2 | 405 | 283 | 25 | 20 | 0.5409 | 17.53 |
| D3 | 404 | 29 | 8 | 1 | 0.0000 | 1.57 |
| D3 | 405 | 29 | 8 | 1 | 0.0206 | 1.55 |
| D4 | 404 | 312 | 25 | 19 | 0.6981 | 20.37 |
| D4 | 405 | 312 | 25 | 22 | 0.7170 | 20.63 |
| D4W | 404 | 312 | 21 | 15 | 0.7173 | 20.08 |
| D4W | 405 | 312 | 22 | 16 | 0.7311 | 21.16 |

D1: 483 train históricos. D2: documental técnico (extractos auténticos + casos sintéticos). D3: oral sintético. D4: mezcla natural. D4W: misma mezcla, repite las 29 observaciones orales por época (341 exposiciones). D5 no evaluable: no existen referencias humanas autorizadas de entrenamiento. Se entrenaron modelos de ~3,9 MB cada uno; pesos, configuración spaCy y hashes por archivo permanecen privados, y sus hashes se reportan en RESULTS.json. No se descargó un modelo base externo. D1 se ajustó dos veces de forma independiente con cada semilla: pesos idénticos byte a byte. Para offline.3 se reutilizan los baselines tras probar igualdad exacta de textos, spans e IDs de train/dev y del protocolo; la prueba y los manifiestos originales se conservan. Los ocho candidatos documentales/orales restantes se reentrenaron con el corpus final.

## F. Evaluación comparativa

Mismo dev sintético de 27 casos; la exactitud comercial se limita a **16 muebles**, con **3 negativos**. F1 principal: candidatos ACCEPTED con la misma política en todos los motores. F1 bruto del NER se presenta aparte. Las cifras siguientes son medias de las dos semillas; desviación poblacional en F1. La exactitud exacta exige todos los campos evaluables correctos por caso, incluidas abstenciones explícitas.

| Datos | Motor | F1 accepted ±σ | Exactitud comercial | Falsas propuestas por seed | p95 NLP warm medio ms |
|---|---|---:|---:|---|---:|
| D1 | M-B | 0.0541 ± 0.0101 | 18.75% | [0, 0] / 3 negativos | 7.37 |
| D1 | M-C | 0.3739 ± 0.0000 | 37.50% | [0, 0] / 3 negativos | 7.63 |
| D2 | M-B | 0.3650 ± 0.0302 | 28.12% | [0, 0] / 3 negativos | 8.16 |
| D2 | M-C | 0.3684 ± 0.0072 | 28.12% | [0, 0] / 3 negativos | 8.39 |
| D3 | M-B | 0.0000 ± 0.0000 | 18.75% | [0, 0] / 3 negativos | 7.58 |
| D3 | M-C | 0.3668 ± 0.0071 | 31.25% | [0, 0] / 3 negativos | 8.00 |
| D4 | M-B | 0.5560 ± 0.0154 | 31.25% | [1, 1] / 3 negativos | 7.84 |
| D4 | M-C | 0.3739 ± 0.0000 | 37.50% | [0, 0] / 3 negativos | 8.21 |
| D4W | M-A | 0.3739 ± 0.0000 | 37.50% | [0, 0] / 3 negativos | 1.12 |
| D4W | M-B | 0.5767 ± 0.0470 | 25.00% | [2, 1] / 3 negativos | 6.97 |
| D4W | M-C | 0.3739 ± 0.0000 | 37.50% | [0, 0] / 3 negativos | 7.19 |

El mejor checkpoint bruto es D4W/405, época 16, F1 0.7311; no equivale al F1 accepted del ensamblador ni a exactitud comercial. La ponderación mejora NER, pero no resuelve el ensamblado. M-B genera una falsa propuesta por seed D4 y dos/una en D4W, sobre tres negativos. El híbrido con veto conserva cero falsas propuestas, pero no supera las reglas y puede perder campos correctos por desacuerdo.

Ablaciones diagnósticas V15 de salida: exactitud comercial base 6/16, sin medidas 5/16, sin precio 4/16, sin cantidad (y precio dependiente) 4/16. Son ablaciones de salida validadas, no nuevos motores optimizados. No se les atribuye una latencia independiente.

Matrices TP/FP/FN, micro/macro, soporte y resultados por familia/etiqueta están en el informe público seleccionado y en el resultado completo privado. Los eventos críticos suman FP+FN por campo, excluyendo color/acabado: una sustitución cuenta dos eventos; no son cotizaciones reales fallidas. Las cantidades internas y el descuento sin campo estructurado NLP, la proyección PRF-03 completa y el rendimiento end-to-end se declaran no evaluables en este comparador.

En la versión previa se repitió la evaluación en procesos nuevos para siete modelos, con métricas y matrices idénticas. En la versión final se verificó además que los refits D1 de ambas semillas producen pesos idénticos; los modelos documentales se reentrenaron con los spans finales. Los tiempos no se exigen idénticos. La RAM reportada es el pico del proceso nuevo (incluye imports), no RAM marginal de NER. Primera llamada, carga y p50/p95 solo corresponden a NLP; no incluyen ASR, colas, backend o frontend.

## G. Seguridad e integridad

V1, sus 675 registros y 98 test se conservan con hashes. No hay cambios de src, contratos, versión productiva, backend/frontend ni configuración de laboratorios. No se accedió a test_homex_dev ni a otra base. No se tocaron grabaciones ni workers. Los tres HEAD remotos comprobados son NLP 81d70395d2bb6cfa4757eaaacb95c6179feae332, backend b2d7ef45a8df7b9616abb417517763fe0859983d y frontend 4372106a566972d264ff36894ce4f0436a223258. Los checkouts históricos permanecen intactos.

No se publican documentos originales, precios negociados reales, referencias privadas, predicciones ni pesos. El PR contiene herramientas, recetas sintéticas históricas y evidencia agregada. Los informes temporales y modelos están bajo ~/Descargas/homex-v2-final-evidence/.

## H. Git y CI

Rama `codex/corpus-v2-final`, desde main V15 sincronizado; primer commit `2292a0c1a6c1c6b6969e4680d8219f4f3fc37432` y commit posterior de evidencia.

[PR #37](https://github.com/gabriel-arinez/homex-nlp/pull/37), sin fusión automática. CI del commit de implementación: canonical-data, package, prf04-experiment, secrets y dependency-audit aprobados. Los checks del commit final se consultan en el propio PR; el cierre local registra su resultado efectivo y SHA sin atribuir anticipadamente un PASS.

## I. Reproducción

Los comandos completos desde un entorno limpio están en [README.md](README.md), sección Reproducción. Para regenerar el resumen sin entrenar:

```bash
uv run python -m training.canonical_v2.summarize <bundle-privado> <directorio-experimentos> <salida-json>
```

El bundle contiene registros/expected finales y DocBin; no requiere otra construcción de datos para repetir estos experimentos. Para ampliar a cotizaciones completas con relaciones comerciales exhaustivas sí falta anotación adicional, claramente fuera de lo aquí demostrado. El modelo no puede promoverse por repetir el mismo dev conocido.

## J. Dictamen

**Mantener RULES_ONLY V15.** La mezcla ponderada D4W ofrece el mejor checkpoint NER bruto disponible, pero el ensamblador no preserva la exactitud comercial y produce falsas propuestas. M-C no demuestra mejora comercial y añade ~7–8 ms p95 frente a ~1 ms de reglas en esta muestra. Es una razón técnica medida para no activar NER/híbrido.

No se inventa un test externo. Faltan validación independiente sobre fuentes nuevas, referencias humanas de voz autorizadas y homologación de relaciones de fichas completas. Este trabajo entrega datos entrenables, modelos medidos y herramientas reproducibles; no certifica que HOMEX comprenda con precisión suficiente cualquier cotización dictada ni que las ocho etapas del plan estén cerradas.
