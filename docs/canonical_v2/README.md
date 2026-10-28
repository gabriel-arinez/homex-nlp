> **Versión activa del cierre integral:** `2.0.0-offline.5.1`, constructor
> `training.integral_v2.build`. Ver [resultados nuevos](FINAL_OFFLINE5_1.md) y
> [reproducción con seis entradas privadas](INTEGRAL_OFFLINE5.md).
> El contenido siguiente conserva el contexto histórico offline.3/4; sus
> extractos y métricas no representan la versión integral actual.

# Corpus V2 offline: fuente canónica y experimentos

Generador versión `2.0.0-offline.4`, base NLP V15 `81d70395d2bb6cfa4757eaaacb95c6179feae332`.
El runtime comercial continúa `homex-nlp==0.1.15`, `RULES_ONLY`. Esta entrega
no instala modelos ni cambia contratos, backend, frontend, bases o workers.

La fuente **canónica offline** es el bundle privado generado por
`training.canonical_v2.build`: `records.jsonl`, `expected.jsonl`, `manifest.json`,
`sha256.json`, `docbin/`, inventario original y conciliación. Los dos JSONL de
`data/canonical_v2/` son entradas sintéticas públicas de ese constructor;
no representan por sí solos el corpus completo. V1 permanece referencia histórica
inmutable bajo `data/corpus`, con sus splits y expected originales. No hay una
segunda versión RC1/RC2 activa en este checkout.

## Datos realmente disponibles

La corrida **histórica `offline.3`** obtuvo 339 observaciones: 273 **extractos literales únicos** de documentos HOMEX auténticos
y 66 casos sintéticos RC2 (incluyen los 12 casos base y 40 orales de RC1, más
14 escenarios RC2). No se suman nuevamente las entregas anteriores.
312 train / 27 dev; las 24 etiquetas históricas se conservan. El corpus contiene
203 muebles, 89 sillas, 28 pisos y 19 otros. El estilo oral tiene 29 train / 18 dev.
Los extractos documentales solo entran en train, en un único grupo conservador.
Los 27 dev son sintéticos ya conocidos: **no son evaluación ciega ni documental**.
No se ha construido test interno o externo independiente.

Los originales aportan 120 bloques candidatos, no 120 proformas identificadas.
Se preservan íntegros, con SHA-256, líneas y offsets. Hay extractos utilizables de
112 bloques; ocho contienen anomalías literales y se segregan. Los extractos
mantienen todos sus enlaces originales incluso tras deduplicarlos (483 ocurrencias
se reducen a 273 observaciones). No son fichas completas de fabricación.
Los precios de catálogo tienen `catalog_price` separado del unitario negociado.
El identificador de proforma queda nulo cuando no figura en el documento.

La matriz V1 tiene 675 filas, con 98 test protegidos de curación. Las 49 extensiones
de ACCESORIO son un overlay reversible, nunca una edición de V1. Las 375 propuestas
RC1 se conservan individualmente en `historical_decisions.jsonl`: no se certifican
como 375 ejemplos nuevos ni como 375 revisiones humanas. Los 577 train/dev V1 tienen
auditoría literal técnica; no se promueven a documentación auténtica sin vínculo.

El piloto histórico de 48 frases no se recuperó de los archivos disponibles.
Los 40 orales RC1 son otro artefacto y así quedan identificados. No se inventaron
las ocho frases restantes ni referencias humanas. D5 no es evaluable por ausencia
de transcripciones humanas autorizadas para entrenamiento.

## Reproducción desde un checkout limpio

Requiere los tres originales privados. La ruta de salida debe quedar fuera de Git
y no existir. Los permisos del bundle se limitan a su propietario.

```bash
uv sync --locked --extra dev --extra asr --python 3.11.15
uv run python -m training.canonical_v2.build \
  --output "$HOME/Descargas/homex-v2-repro-corpus" \
  --sources "$HOME/Documentos/PROFORMAS.txt" \
  "$HOME/Documentos/SILLAS-PISOS-OTROS.txt" \
  "$HOME/Descargas/inventario de sillas.txt"
uv run python -m training.canonical_v2.validate \
  "$HOME/Descargas/homex-v2-repro-corpus"
uv run python -m training.canonical_v2.audit \
  "$HOME/Descargas/homex-v2-repro-corpus" \
  "$HOME/Descargas/homex-v2-repro-audit"
uv run python -m training.canonical_v2.experiment run \
  --bundle "$HOME/Descargas/homex-v2-repro-corpus" \
  --output "$HOME/Descargas/homex-v2-repro-models"
```

Un fallo puede reanudarse con `run --resume` usando las mismas rutas: se verifican
los hashes del protocolo, datos y pesos antes de reutilizar un entrenamiento.
Cada fase registra comando, retorno, duración y log. No reutiliza pesos alterados.
Los modelos y predicciones permanecen privados. `comparison.json` agrega las diez
corridas; cada directorio guarda historia, checkpoint seleccionado, hashes,
matrices de errores y métricas por etiqueta/familia, además de predicciones por caso.

## Protocolo científico y límites

`training/canonical_v2/protocol.json` fija semillas 404/405, máximo 25 épocas,
paciencia 6 tras al menos 8 épocas, dropout 0.2, batch 8 y selección por F1 dev.
D1 usa solo los 483 train originales; D2 documental (incluye extractos auténticos y
casos documentales sintéticos); D3 oral sintético; D4 mezcla natural; D4W duplica
el muestreo oral para estudiar su escasa representación. Todos comparan el mismo
dev sintético. La falta de un dev documental independiente limita especialmente D2.

M-A es V15 auténtico; M-A2 son ablaciones **de salida**, diagnósticas, de precio,
cantidad y medidas: no son implementaciones optimizadas de reglas. M-B reutiliza
el ensamblador NER histórico. M-C reutiliza el veto de conflictos PR24 sobre la
estructura de reglas, adaptado y validado contra el contrato V15. No se usa la
unión ingenua de predicciones ni se sustituyen reglas productivas.

La vista NER principal compara candidatos ACCEPTED para todos los motores;
el NER bruto se reporta aparte. Sin esa separación el F1 de mecanismos diferentes
no es comparable. TP/FP/FN son coincidencias exactas de etiqueta y offsets.
Las métricas comerciales miden el subconjunto representable de muebles: los demás
productos tienen evaluación NER, pero su voz no se habilita. Exactitud de campos
incluye abstenciones explícitamente evaluadas y reporta denominadores. Los errores
críticos son eventos FP+FN de campos, excluyendo color/acabado; una sustitución
cuenta dos eventos. No equivalen a porcentaje de cotizaciones mal fabricadas.
Cantidad interna/descuento no tienen campo estructurado en el DTO NLP actual;
se conservan en referencias auxiliares sin afirmar una medición inexistente.

Latencias son solo NLP con `perf_counter`, primera llamada y warm p50/p95;
el híbrido suma A+B+conciliación. Las ablaciones no tienen timing independiente.
RAM es pico del proceso de evaluación nuevo, incluidos imports; no se atribuye
como RAM marginal del modelo. No se mide ASR, colas, proyección o interacción UI.

## Correctivos posteriores a la corrida offline.3

El generador offline.4 corrige la extracción de cantidades comerciales **enteras**
(«25 piezas») y sus unidades, sin convertir números internos de componentes
(«2 tomacorrientes») en cantidad comercial. Conserva los formatos documentales
«6,00 Pza.», «52,00 Mts.2» y «12 m²». Se añadieron pruebas de regresión.

El nuevo archivo **privado** `full_item_review.jsonl` conserva el texto literal
completo de cada bloque original junto con los fragmentos ya reconocidos y sus
offsets referidos al ítem íntegro; incluye incluso bloques en cuarentena. Cada
expediente lleva `supervised=false`, `eligible_for_training=false` y
`commercial_expected=null`. **No se entrena con spans parciales de una
descripción completa**, porque eso convertiría entidades reales no anotadas en
falsos negativos.

Las cifras de 339 registros, métricas D1–D4W y hashes en
`INFORME_A_J.md`, `AUDIT.json` y `RESULTS.json` describen **solo la
corrida offline.3**: NO corresponden automáticamente al generador offline.4.
Se debe reconstruir el bundle privado desde los tres originales, validar
sus nuevos hashes y repetir D2/D3/D4/D4W antes de comparar resultados.
El contenido privado de `~/Descargas/homex-v2-final-evidence/` no está
disponible para los controles públicos de CI, por lo que no se deben
declarar completados esos ensayos a partir de las suites sintéticas.

Para promover ítems completos a entrenamiento se requiere terminar de revisar
entidades y relaciones por pieza, los estados ambiguos y el contrato comercial.
La construcción de expedientes es **preparación verificable de esa revisión**,
no homologación inventada ni cierre del Plan Maestro.

## Recuperación selectiva y seguridad

Se reutilizan PR20/22 (casos/referencias), PR24 (ensamblado, métricas, veto),
PR31 (49 parches y auditor literal), y se revisa la corrección de aislamiento
PR35. PR23 es infraestructura de campo, PR26/27 son evaluación/puente de audios
y PR28 es instrumento HUMAN_GOLD/WER; no aportan automáticamente gold autorizado.
PR34 documenta limitaciones de evidencia. No se fusionó ninguna de esas ramas.

No hay validación humana independiente ni evidencia externa nueva. Los datos
conflictivos quedan pendientes; la aprobación técnica de offsets/extractos no
acredita homologación comercial completa. Esta versión sirve para entrenar y
comparar el material verificable disponible, sin declarar cerrado todo el plan
maestro ni un corpus completo de cotizaciones anotadas de extremo a extremo.
