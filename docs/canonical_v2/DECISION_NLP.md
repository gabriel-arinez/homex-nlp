# Decisión comparativa: V15 RULES_ONLY para captura asistida

Se recomienda `homex-nlp 0.1.15`, `prf04-rules-v15`. No ejecutar los modelos NER
ni el híbrido en la captura operativa. Conservar sus artefactos como investigación
histórica; suspender nuevos entrenamientos y ampliación del corpus como trabajo
inmediato. El vendedor debe revisar siempre. No se autoriza guardado automático,
merge, despliegue ni promoción por este resultado.

## Evidencia nueva

Se recuperaron con Git LFS y verificaron **20/20 WAV reales**, 522,635 segundos,
mono PCM 16 kHz/16 bit, SHA/tamaño coincidentes con el manifiesto. No se alteraron
los originales. Se transcribieron los veinte con Faster-Whisper 1.2.1,
CTranslate2 4.8.2 y el modelo small existente del worker, CPU/int8/español,
con parámetros fijos. ASR p50/p95: 3,807/6,650 s; carga: 1,049 s.
Los veinte textos ASR quedaron congelados antes de comparar motores.

Se ejecutaron **21 mecanismos**: V15, los diez NER y sus diez híbridos, sobre
103 entradas cada uno, sin mezclar conjuntos: dev21, holdout11, histórico27,
20 ASR reales, 20 guiones previstos y cuatro negativos de train identificados
solo como diagnóstico. No se entrenó, ajustó ni seleccionó un checkpoint nuevo.
Los pesos/tokenizadores originales se verificaron por SHA. **1239 resultados
semánticos anteriores se reprodujeron**; solo cambió el tiempo medido.

| Evidencia | V15 | NER (diez variantes) | Híbrido (diez variantes) |
|---|---:|---:|---:|
| Comparador histórico conocido | 6/16 | 2–3/16 | 5–6/16 |
| Integral en cinco muebles del holdout | 0/5 | 0/5 | 0/5 |
| Propuestas sobre ASR real (disponibilidad, no exactitud) | 18/20 | 0–15/20 | 5–18/20 |
| Fallas de contrato sobre ASR | 0/20 | 0 en los diez | Dos variantes con 1/20 cada una |

Dos híbridos adicionales fallaron en un guion previsto cada uno. Se preservaron
las excepciones por referencias incompatibles de componentes; no se sustituyó
silenciosamente el resultado por reglas. La instrumentación comprueba igualdad
con `.extract()` del NER, sin modificar motores ni ensambladores congelados.

Las abstenciones negativas correctas se reportan aparte: no se cuentan como un
mueble positivo completamente resuelto. El 6/16 conserva exclusivamente su métrica
histórica para comparar con antecedentes. En el comparador integral nuevo se
usan solo positivos en el denominador de exactitud completa. Una afirmación
incorrecta y una omisión permanecen visibles como FP y FN.

## Referencias y límites

Se localizaron los guiones y el proyecto histórico con los veinte SHA, que declara
HUMAN_GOLD=NO y carece de anotaciones humanas fieles. El demo sintético no se
utilizó como referencia real. **WER humano y exactitud comercial humana de audio:
NO_EVALUABLE**. La discrepancia provisional con guiones fue 69/915 palabras y
143/5236 caracteres normalizados; no se llama WER humano. No se atribuye toda
variación a ASR sin evidencia de lo pronunciado.

Los guiones tienen referencias asistidas de campos previstos, no gold completo
del audio. Los veinte WAV aportan disponibilidad, estabilidad, coherencia,
diferencias entre motores y coste. NER/híbrido no demostraron superioridad
comercial que justifique reemplazar la alternativa conservadora existente.
El holdout es interno y conocido, no externo/ciego: 0/5 tiene IC Wilson95 %
[0; 0,4345]. Confianza alta en la recomendación conservadora; limitada en una
estimación generalizable de exactitud. Ningún motor está homologado para fabricar
sin revisión humana.

## Rendimiento e integración

Benchmark en procesos específicos nuevos, tres repeticiones warm por cada audio,
60 llamadas por motor, con fallos contados aparte. V15: p50/p95
**1,026/1,445 ms**, pico RSS **32072 KiB**. Imports: 0,124 s; primera inferencia:
58,187 ms. La caché del sistema operativo no se purgó. Los otros veinte procesos,
carga, primera inferencia, memoria y latencias se publican en el agregado.
La memoria incluye imports; no se presenta como asignación marginal del modelo.
Las sumas ASR+NLP+proyección son etapas medidas, no cronómetro de cola/API/UI.

Se ejecutaron **541 pruebas NLP, 14 operacionales, 417 backend en PostgreSQL
nuevo aislado y 61 frontend PRF-03/04/HITL**. Contratos OpenAPI byteidénticos.
De 2163 ejecuciones, cuatro no produjeron salida por fallas híbridas; las otras
2159 pasaron la proyección Django real y validación PRF-03, sin errores. Se probó
idempotencia de esa proyección. Esto demuestra compatibilidad, no exactitud.
El adaptador real V15 sigue rechazando modos experimentales no autorizados;
no se parcheó para favorecer los candidatos. Los tests de pipeline/UI conservan
sus dobles; no se afirma haber medido un ciclo real de navegador a guardado.

La inspección del worker activo encontró un paquete legado **0.1.0**: la versión
recomendada V15 y la efectivamente desplegada son distintas. La prioridad posterior
es una integración controlada de V15 ya validado, sin ejecutar ese despliegue aquí.
La optimización ASR queda separada; no se cambiaron su modelo ni parámetros.

Ruta recomendada: captura → Faster-Whisper existente → texto original → V15
RULES_ONLY → contrato/validación → PRF-03 → revisión del vendedor → acción
explícita de agregar/guardar. Mantener límites, ámbitos, cantidad comercial,
negaciones, rectificaciones, moneda contextual sin conversiones, precios por
modalidad y pendientes. No cargar pesos NER ni conciliar un segundo motor.
spaCy puede continuar como dependencia instalada: no se ejecuta un modelo NER.

## Reproducción

El auxiliar nuevo solo evalúa checkpoints congelados:

```bash
uv run --locked --extra dev --extra asr python -m training.decision_nlp \
  --bundle "$BUNDLE_PRIVADO_CONGELADO" \
  --models "$MODELOS_OFFLINE5_1" \
  --inputs "$ENTRADAS_PRIVADAS_EVALUACION" \
  --output "$HOME/Descargas/NUEVA_SALIDA_PRIVADA_NO_EXISTENTE"
```

Rechaza destinos existentes y pesos/código de entrenamiento alterados. Ejecuciones
por motor en procesos nuevos. No usa los 98 test V1 ni cambia V15/corpus/modelos.
Los originales WAV incorporados por el propietario siguen en Git LFS.

[Agregados](DECISION_NLP_RESULTS.json). El expediente privado
`~/Descargas/HOMEX_DECISION_FINAL_NLP_20261028/` contiene informes 01–08,
transcripciones, segmentos, predicciones, referencias, diagnóstico causal,
ranking, benchmark, pruebas/CI, comandos y manifiesto SHA. Ningún texto comercial,
precio privado, predicción individual ni peso nuevo se publica en esta entrega.
CI pública acredita código/fixtures; no se le atribuyen las ejecuciones privadas.
