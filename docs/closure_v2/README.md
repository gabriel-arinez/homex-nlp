# Cierre técnico verificable del plan NLP — 27-10-2026

Entrega aislada en `codex/nlp-corpus-v2-cierre`, base histórica del plan
`449a5cf` (paquete 0.1.5, reglas v6). **Ninguna etapa completa se declara cerrada.**
El encargo actual autoriza implementar etapas 2–6; sustituye el antiguo flujo de
aprobación punto por punto. No se modifica PR #30, runtime, contratos, V1,
backend, frontend, fuentes privadas ni evaluación privada. No hay merge/deploy.

## Evidencias nuevas

- `audit.json`: 675 registros, 483/94/98, 300 proformas sintéticas y 65 familias;
  integridad de hashes/sellos, IDs, expected, etiquetas, offsets Unicode,
  tokenización, solapes, duplicados y cruces. Cero errores formales y duplicados
  exactos o normalizados. Cero cruces por proforma/familia/ID.
- Hay **79 grupos de prefijo literal de 65 caracteres** compartidos entre splits
  y un source_id compartido. Son alertas de plantilla/fuente común, no 79 pares
  ni prueba de 79 fugas semánticas. El detector histórico de 80 coincidencias
  tenía otra unidad de conteo. No se acredita independencia semántica.
- `development_overlay.json`: censo mecánico de los **577 train/dev**. 49 parches
  reversibles amplían ACCESORIO para incluir el núcleo explícito «Membrana
  protectora». Se conservan offsets antes/después y literal. 277 registros tienen
  hechos adicionales: 247 descuentos explícitos, 35 menciones de cantidad interna
  y 12 de capacidad (pueden coexistir). Cantidad interna conserva ámbito pendiente;
  no se asigna una pieza por posición. No se agregan clases NER ni se cambian
  precios, unidades, texto, origen o splits. Todos siguen pendientes de revisión
  humana; no son GOLD ni corpus activo. Descartar overlay revierte la propuesta.
- Los 98 test se auditan mecánicamente; no se exportan IDs, etiquetas por registro,
  texto, propuestas ni observaciones semánticas de test. Su revisión de dominio
  corresponde al custodio independiente. No se usa test para curar/entrenar/elegir.
- `oral_intake/`: esquema estricto, manifiesto y JSONL vacío. No añade frases para
  aparentar cobertura. El validador rechaza padres test/desconocidos, grupos,
  sesiones, hablantes, audio o texto compartidos entre splits, spans inválidos,
  referencias reales incompletas y datos personales obvios. Las declaraciones
  automáticas no certifican consentimiento, escucha humana ni anonimización.

## Procedencia y trabajo ya existente

Se leyeron íntegramente el plan maestro de Documentos, continuidad de auditoría
25/10, handoff 26/10 y especificaciones PRF-04/guía/F02/F04/F05. El plan tiene SHA
`73c1f325397caa7155f9b867ae9b732947cefb6571b4a420c3c1ee337ccf4610`.
Las estimaciones porcentuales del handoff no se heredan como gates cumplidos.

Los TXT locales `PROFORMAS.txt` y `SILLAS-PISOS-OTROS.txt` coinciden por SHA con
`training/corpus_v2/source_fingerprints.json` en la entrega rc.1: respectivamente
`f9497615494ba59c8b76c79c21c5411bbc919aa895c1eff2cc70c88bec0b8020` y
`8e22fc29be4d2ed1d75d9745409df02c24cd953bca25a79dc06c083a77fd7ca0`.
El tercer TXT no está en la ubicación examinada de Documentos. No se copió texto
privado. El informe rc.1 registra cero correspondencias literales confirmadas de
675 contra 120 ítems privados; esto es evidencia previa consultada, no una nueva
adjudicación documental. Una coincidencia de hashes de archivos no demuestra
correspondencia entre ítems. El overlay conserva `source_document_id=null`.

Entregas remotas consultadas, todas draft al consultar el 27/10:

| Entrega | Artefacto y límite |
|---|---|
| [#20](https://github.com/gabriel-arinez/homex-nlp/pull/20), `0154ecb` | Candidato rc.1 y reconciliación; no homologación humana |
| [#22](https://github.com/gabriel-arinez/homex-nlp/pull/22), `b27edfa` | rc.2: 39 train/27 dev, 46 grupos; V1 histórico separado; holdout/GOLD=0 |
| [#24](https://github.com/gabriel-arinez/homex-nlp/pull/24), `4c94a75` | Comparación rc.2/v13/NER/veto; sintética, independencia histórica no verificada |
| [#26](https://github.com/gabriel-arinez/homex-nlp/pull/26), `7ba61ea` | Validador del piloto WAV y evaluación ASR local |
| [#28](https://github.com/gabriel-arinez/homex-nlp/pull/28), `544f680` | Instrumento de doble escucha y adjudicación humana; referencias reales pendientes |

No se reconstruyen ni se promueven esos candidatos ni se mezclan sus datos con
el experimento V1. Los 375 cambios rc.1 documentados requieren revisar su kit;
no equivalen a 375 correcciones humanas aprobadas ni autorizan editar test.

## Experimento nuevo: baseline histórico V1 en desarrollo sintético

`dev_experiment.json` incluye TP/FP/FN, precisión/recall/F1 por cada etiqueta,
micro, macro y denominadores; `training.json` conserva las 10 épocas.
262 muebles train / 62 dev, 1.368 entidades dev, seed 404, spaCy 3.8.13;
mejor época elegida exclusivamente por dev (primera máxima: 5). Sin test.
No es comparación contra v14 ni evaluación de voz real. No mide mejora respecto
al PR #30. La señal de plantillas y selección con dev limitan la interpretación.

| Vista de evidencia aceptada | P micro | R micro | F1 micro | F1 macro (17 etiquetas con actividad) | p50 ms | p95 ms |
|---|---:|---:|---:|---:|---:|---:|
| A RULES_ONLY v6 | 0,6640 | 0,2442 | 0,3570 | 0,2545 | 0,377 | 1,969 |
| B NER + ensamblador experimental existente | 1,0000 | 1,0000 | 1,0000 | 1,0000 | 13,389 | 16,835 |

B incluye además su vista de spans estadísticos brutos para distinguir predicción
del modelo de abstención del ensamblador. A usa candidatos ACCEPTED; PRECIO solo
se mapea con modalidad estructurada disponible, de lo contrario cuenta como
PRECIO_UNMAPPED. Etiquetas sin soporte ni predicción tienen métricas null. Macro
promedia razones definidas y registra cuántas; no asigna F1=1 por ausencia.
El F1 sintético perfecto no acredita semántica comercial ni generalización.

Latencia: 5 warmups por motor, tres pasadas ordenadas A y luego B, 186 mediciones
por motor, nearest-rank; extracción caliente, concurrencia 1, CPU i5-1135G7,
x86_64, Python 3.11.15, OMP/OPENBLAS=1. Carga NER separada en JSON. Las repeticiones
son mediciones temporales sobre las mismas 62 frases, no 186 muestras independientes.
No se midió E2E, ASR, cola, productividad ni rendimiento multiusuario. No se
neutralizó ruido/carga del host. Ambos validan 186/186 salidas de contrato.
Una corrida de entrenamiento; no se atribuye variabilidad entre semillas.

Se conserva RULES_ONLY. La alternativa híbrida relevante ya está documentada en
#24; no se inventa una nueva mejora ni se promueve el ensamblador antiguo, cuyas
asociaciones requieren revisión. D2–D5/ablations/relaciones/JSON completo quedan
pendientes de corpus homologado y referencias válidas. No comparar el F1 de esta
vista V1/v6 con cifras rc.2/v13 como serie temporal.

## Audio y GOLD

Se ejecutó **solo** el validador existente `training.audio_pilot.dataset.validate`
del checkout NLP `544f680`, en lectura y sin escribir bytecode allí. Resultado en
`audio_inventory.json`: 20 WAV PCM, 16 kHz, 522,635 s, 16.725.880 bytes, SHA/tamaño
válidos y sin extras. No se escuchó, transcribió, copió ni modificó audio.
Son piloto conocido, no train ni holdout externo. La relación uno a uno con los
22 intentos históricos sigue sin verificar. No se proporcionaron referencias
humanas aprobadas; los guiones y el demo humano sintético no sirven como GOLD.
**WER=null; holdout externo disponible=0; promoción=false.**

El instrumento #28 permite completar doble escucha, actas y consentimiento de
forma privada. Solo después corresponde ejecutar su scorer existente. Este paquete
no crea aliases humanos, firmas, autorizaciones ni transcripciones.

## Reproducción

Desde este worktree de homex-nlp; destinos nuevos fuera de Git:

```bash
uv sync --locked --extra dev --python 3.11.15
make closure-v2-check
uv run --locked --extra dev python -m training.closure_v2.audit --output /tmp/homex-audit-new
uv run --locked --extra dev python -m training.closure_v2.curate --output /tmp/homex-overlay-new.json
uv run --locked --extra dev python -m training.closure_v2.oral docs/closure_v2/oral_intake/records.jsonl
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 uv run --locked --extra dev python -m training.train_prf04 --epochs 10 --destination /tmp/homex-train-new
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 uv run --locked --extra dev python -m training.closure_v2.experiment /tmp/homex-train-new/model-dev-best /tmp/homex-dev-new.json
make check docbin-check distribution-check
git diff --check
```

`verify` reconstruye audit/overlay/esquema y los compara con los versionados; no
entrena ni evalúa test ni consume datos privados. Dos auditorías y dos overlays
producidos localmente coinciden. Los modelos/pesos permanecen fuera de Git;
model_files_sha256, lock y hashes de datos constan en el informe. Las latencias no
se esperan idénticas al reproducir. La distribución no incluye audios/pesos.
DocBin valida/convierten las particiones existentes, sin inferencia sobre test.

Para repetir el inventario WAV, usar el checkout **del mismo repositorio NLP**
que contiene #28, a su revisión 544f680, con entorno Python ya instalado:

```bash
export TASK_VALIDATOR=/ruta/al/checkout-nlp-human-gold
export TASK_DATA=/ruta/privada/piloto_voz_v13
export TASK_PYTHON=/ruta/absoluta/a/este/worktree/.venv/bin/python
cd /tmp
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$TASK_VALIDATOR" "$TASK_PYTHON" - <<'PY'
import os
from pathlib import Path
from training.audio_pilot.dataset import validate
r = validate(Path(os.environ['TASK_DATA']))
print({'files': len(r['entries']), 'dataset_digest': r['dataset_digest'],
       'human_gold': r['HUMAN_GOLD'], 'wer': r['WER']})
PY
```

No ejecutar `git lfs pull` ni ASR como parte de este control. El custodio mantiene
sus datos/autorizaciones fuera de Git. La rama de esta entrega no depende en runtime
de #28; la dependencia solo aplica al inventario externo documentado.

## Siguiente gate externo exacto

El custodio debe adjudicar la procedencia y los casos ambiguos del kit V2,
proporcionar transcripciones humanas escuchadas e independientes del ASR y
referencias comerciales revisadas; fijar umbrales antes de elegir candidato y
adquirir un conjunto externo independiente. Ver `MATRIZ_8_ETAPAS.md`. No integrar
este overlay automáticamente en corpus activo ni abrir test para iterar.

## Verificación ejecutada y bloqueos de calidad

- `make closure-v2-check`: 28 pruebas de mutación/límites y reconstrucción exacta PASS.
- Suite completa final: **136 passed**, Python 3.11.15.
- `make check docbin-check distribution-check`: PASS (suite entonces 135; se añadió
  después una prueba de alineación de todos los parches, y suite final 136 PASS).
- `ruff check`, `ruff format --check`, esquemas y `git diff --check`: PASS.
- Comparación byte a byte entre dos auditorías y dos overlays: PASS.
- Diff contra base para `data`, `src`, `schemas`, `pyproject.toml`, `uv.lock`: vacío.
- **`uv audit --locked`: FAIL**, cuatro vulnerabilidades conocidas: tres en
  filelock 3.32.6 (GHSA-v4x8-3wr5-3wq8, GHSA-9vhv-jxww-xfm5,
  GHSA-567q-5qvw-pf92) y una en setuptools 84.0.0
  (GHSA-xmj3-9gf7-h52w). El lock preexistente se conserva; este gate queda abierto
  para una actualización coordinada con el frente de integración. No se presenta
  el paquete como aprobado en todas sus dependencias ni se omite el gate en CI.

No se ejecutaron suites/servicios backend/frontend ni bases de datos en este trabajo.
El smoke consumidor incluido en distribution-check valida el artefacto en entorno
Python temporal; no es integración Django ni prueba de persistencia comercial.
