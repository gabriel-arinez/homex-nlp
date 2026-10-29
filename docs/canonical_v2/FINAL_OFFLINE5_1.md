# Continuación integral del PR #37: resultados offline.5.1

La ejecución técnica sobre `2.0.0-offline.5.1` terminó con PASS. Esta entrega
continúa el trabajo de `4f10480`; no declara homologado el Plan Maestro ni cambia
V15/RULES_ONLY. Código de entrenamiento congelado: `1036b1fb6f70a2261b9a3fef70bd29a1fd5b722a`.

De las 93 fichas pendientes, 90 se resolvieron técnicamente y tres se segregaron
por una anomalía de diámetro que requiere aclaración documental/comercial.
El inventario queda en **120/120 con decisión: 108 aptas, 12 cuarentenas y cero
parciales pendientes**. Se conservan las nueve cuarentenas previas. Las ocho
anomalías originales se revisaron individualmente, sin corregir unidades por intuición.
Las referencias son revisión técnica asistida; ninguna firma o gold humano.

El corpus supervisado contiene **161 registros completos: 108 documentales
literales y 53 orales sintéticos nuevos**. Familias: 110 muebles, 37 sillas,
10 pisos y cuatro otros. Particiones: **129 train / 21 dev / 11 holdout**,
con 37/3/4 grupos supervisados. Los 24 labels tienen soporte en train.
Padres, paráfrasis y 152 vínculos de similitud/plantilla se agrupan antes de entrenar.
El holdout es interno de documentos conocidos, sin independencia de fuente.
No se hicieron predicciones sobre los 98 test V1. V1 conserva 483/94/98,
las 375 operaciones históricas no se cuentan como ejemplos nuevos y las 49
correcciones reversibles no se aplican al D1 original.

## Entrenamientos y comparación

Diez entrenamientos nuevos, semillas 404/405, checkpoints seleccionados con el
mismo dev y congelados antes de evaluar el holdout. A=V15 RULES_ONLY,
B=NER con ensamblador integral offline, C=híbrido. Las ablaciones M-A2 son
diagnósticos de salida, no motores con tiempos independientes.

| Experimento | Semilla | Train | Épocas | F1 bruto dev | F1 bruto holdout | Históricos 16: A / B / C | Holdout integral A / B / C |
|---|---:|---:|---:|---:|---:|---|---|
| D1 | 404 | 483 | 11 | 0.2348 | 0.1387 | 6 / 3 / 6 de 16 | 0 / 0 / 0 de 5 |
| D1 | 405 | 483 | 18 | 0.2222 | 0.2747 | 6 / 3 / 6 de 16 | 0 / 0 / 0 de 5 |
| D2 | 404 | 84 | 25 | 0.7619 | 0.7237 | 6 / 3 / 6 de 16 | 0 / 0 / 0 de 5 |
| D2 | 405 | 84 | 25 | 0.7713 | 0.7843 | 6 / 3 / 5 de 16 | 0 / 0 / 0 de 5 |
| D3 | 404 | 45 | 25 | 0.3109 | 0.2732 | 6 / 2 / 5 de 16 | 0 / 0 / 0 de 5 |
| D3 | 405 | 45 | 25 | 0.3261 | 0.2420 | 6 / 2 / 6 de 16 | 0 / 0 / 0 de 5 |
| D4 | 404 | 129 | 24 | 0.8054 | 0.7692 | 6 / 2 / 5 de 16 | 0 / 0 / 0 de 5 |
| D4 | 405 | 129 | 25 | 0.8194 | 0.7139 | 6 / 2 / 6 de 16 | 0 / 0 / 0 de 5 |
| D4W | 404 | 129 | 24 | 0.8000 | 0.7562 | 6 / 2 / 5 de 16 | 0 / 0 / 0 de 5 |
| D4W | 405 | 129 | 22 | 0.8078 | 0.7852 | 6 / 3 / 5 de 16 | 0 / 0 / 0 de 5 |

El comparador histórico reproduce su ámbito de campos y se mantiene separado de
la nueva exactitud integral por atributos y relaciones. La exactitud integral es
estricta, con identidad léxica por pieza/ámbito; los errores de nombre y omisiones
cuentan. El F1 de entidades **no acredita** una especificación de fabricación
correcta. No hay evidencia suficiente para promover un modelo ni afirmar una
mejora comercial general sobre reglas. Se mantiene RULES_ONLY sin modificaciones.

[Agregados completos](FINAL_OFFLINE5_1_RESULTS.json) contienen TP/FP/FN por
etiqueta, raw y ACCEPTED separados, campos y relaciones, intervalos Wilson,
negativos, errores críticos, familias, tiempos, carga cold/warm y pico RSS por
proceso. [CSV resumido](FINAL_OFFLINE5_1_SUMMARY.csv) conserva denominadores y
digest de cada modelo. Los pesos, textos, precios y predicciones individuales
permanecen privados.

En el holdout de cinco muebles, la exactitud 0/5 tiene IC Wilson 95 %
[0; 0,4345]; no demuestra equivalencia ni permite una conclusión externa.
Como diagnóstico concreto, D4W/405 obtiene TP/FP/FN de campos 69/26/55,
frente a 21/18/103 de V15 y 19/15/105 del híbrido. Los eventos críticos FP+FN
son 60/95/94 respectivamente: menor omisión parcial no basta para un mueble
completo correcto. En los tres negativos históricos, D4W/405 genera una falsa
propuesta NER frente a cero de reglas/híbrido; son casos conocidos, no prueba externa.

Para esa corrida, warm p50/p95 sobre las 11 entradas del holdout (todas las
familias, no solo cinco muebles) fue 0,0339/1,6607 ms en reglas,
8,7464/9,8955 ms en NER y 8,9755/12,5497 ms en híbrido. La carga NER fue
0,0589 s y el pico RSS del proceso 144716 KiB. No se oculta esta regresión de
coste. `first` corresponde al primer caso de cada split; solo el primer caso
del primer split es la primera inferencia del proceso, los demás ya están warm.

## Controles ejecutados y límites

Dos builds con **35 hashes idénticos**, DocBin con roundtrip, 120 expedientes y
161 referencias validadas, 18 mutaciones rechazadas, rechazo del runner antes de
crear modelos con un certificado alterado. Las 161 referencias pasan las funciones
estructurales puras del backend V15 fijado. Con spans anotados, 161 extracciones
pasan contrato/proyección: es una prueba de compatibilidad, no exactitud del modelo.
Las proyecciones de las predicciones guardadas tienen 3540
validaciones estructurales y 0 fallas. Los resultados registran
0 fallas de contrato NER y 0
fallbacks por error de conciliación; no se ocultan como abstenciones correctas.

`make check docbin-check distribution-check`: **536 tests generales**, Ruff,
esquemas y distribución. Pruebas operacionales: **14**. `uv audit --locked`:
70 paquetes, sin vulnerabilidades conocidas. Gitleaks sobre commits del PR:
sin hallazgos reales. Se clasifica un falso positivo nuevo de SHA del tokenizador
y se añade únicamente su fingerprint exacto de commit/ruta/regla/línea, siguiendo
la política existente; no se excluyen archivos ni reglas. El hash fue verificado
contra el preflight congelado y el detector conserva su control positivo. Un canario secreto inventado fue detectado
por el escáner externo. El escaneo histórico inicial tuvo 4094 coincidencias,
verificadas como metadatos SHA-256 preexistentes; no se lo presenta como cero
hallazgos históricos. El contenido privado no se publica en CI.

Los cuatro negativos orales nuevos están en train por sus grupos; sus resultados
no acreditan falsas propuestas en un test nuevo. Pisos/zócalos no tienen soporte
en este holdout conservador. Dev carece de seis etiquetas y holdout de cuatro;
el JSON publica cuáles. Las sillas/pisos se evalúan como NER documental, sin
habilitar su voz. El piloto de 48 frases no fue localizado: los 53 nuevos no lo
suplantan. HUMAN_GOLD, WER y test externo son NO_EVALUABLE con estos datos.

Se preservan los intentos fallidos y sus razones en el informe privado: detector
histórico, error de identidad del adaptador y revisión literal de ejes sin unidad.
No se ajustaron hiperparámetros ni particiones usando resultados del holdout.
Un D1 previo llegó a evaluarse antes del fallo del adaptador; el corpus final no
se anuncia como ciego. La revisión offline.5.1 añade 16 valores de eje sin unidad y
cuatro expresiones multiextensión, con evidencia fuente, no metros supuestos.

## Gates A–J

| Requisito | Estado técnico | Evidencia |
|---|---|---|
| A inventario | APROBADO | 120 decisiones, tres fuentes y offsets/SHA privados |
| B anotación integral resoluble | APROBADO con exclusión expresa | 108 aptas, 12 cuarentenas, cero parciales |
| C corpus versionado | APROBADO | 161 registros, 35 hashes reproducidos |
| D historia y cobertura | APROBADO | 675 V1, 375 operaciones, 49 overlays; matrices por familia/label/fenómeno |
| E particiones y contaminación | APROBADO en alcance interno | Grupos, padres y duplicados; no test externo |
| F compilador/runner/contratos | APROBADO | Dos builds, DocBin, mutaciones y rechazo cerrado |
| G entrenamientos | APROBADO | Diez modelos nuevos y hashes verificados |
| H comparación | APROBADO como evaluación | Métricas nuevas y comparador histórico separados; promoción BLOQUEADA |
| I pruebas/publicación | Ver CI del HEAD del PR | Checks locales ejecutados; no merge ni despliegue |
| J evidencias | APROBADO en entrega privada | Informe A–J, manifiesto SHA, errores individuales y comandos privados |
| Homologar 12 conflictos | BLOQUEADO | Falta aclaración documental/comercial, no trabajo de anotación pendiente |
| HUMAN_GOLD / WER / externo | NO_EVALUABLE | Sin evidencia humana/externa autorizada |

Reproducción y alta de fuentes: [protocolo](INTEGRAL_OFFLINE5.md) y
[guía](../../training/policies/annotation_guide.md). CI verifica el código y
fixtures inventadas; las diez corridas privadas se acreditan por sus artefactos,
no por atribuirlas a los entrenamientos históricos de CI. PR #37 continúa abierto.
