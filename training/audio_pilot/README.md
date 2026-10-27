# Evaluador offline de 20 WAV / ASR — etapas 2 y 5

Arnés de medición independiente, base **PR #23**
`9b2d57d145c09d6ac354ee3d8ecef4f294db94ee`. Reutiliza `benchmark_campo`
(canonical/digest, escritura privada, estadísticas, Batch, doble revisión y WER)
sin modificar sus archivos ni duplicar su scorer. No depende del experimento #24,
no importa motores NLP, no cambia Backend/Frontend, contratos, corpus ni modelos.
No declara cierre de etapa8 ni mejora comercial. No entrena.

## Datos externos y alcance

Rama separada `data/piloto-audios-reales-v13-20261026`, commit observado
`265949dbfe098dbff251dc7b267d0f23fe2a48b3`. El código acepta `--dataset-dir`
externo; no requiere merge de datos y no incluye audios/transcripciones en Git.
`main` no se presupone actualizado. Los 20 WAV son **piloto conocido de diagnóstico**,
no holdout, train, gold ni equivalentes demostrados de los 22 intentos históricos.
Los guiones V2 contienen lo planeado; nunca se importan como transcripción fiel.

CSV exacto `manifest.csv`: columnas `guion,archivo,sha256,bytes`, IDs `01`…`20`,
rutas exactas `audios/01.wav`…`audios/20.wav`. Valida tamaño, SHA256, RIFF/WAVE,
PCM completo sin compresión (1/2 canales, 8–192kHz, 1–4bytes/muestra), frames,
IDs/hash duplicados, extras (incluido mueble.m4a), archivos faltantes, traversal,
symlinks en todos los componentes, archivos especiales y LFS no hidratado.
Límite128MiB/audio. Formatos fuera del perfil fallan explícitamente, no se convierten.
La validación estructural no certifica que el contenido semántico sea el guion.
Los originales se abren solo lectura; ASR recibe bytes revalidados en BytesIO.

## Instalación y validación sin modelo (Ubuntu / uv)

Python3.11.15, uv0.12.9 en CI, dependencias de `uv.lock` intactas. Desde la rama:

```bash
uv sync --locked --extra dev --python 3.11.15
export TASK_DATA="$HOME/Descargas/homex-nlp-piloto-audios-v13/datasets/piloto_voz_v13"
export TASK_OUTPUT="$HOME/Descargas/homex-audio-evaluacion"
uv run --locked --extra dev python -m training.audio_pilot.cli evaluate \
  --dataset-dir "$TASK_DATA" --validate-only --output-dir "$TASK_OUTPUT/validate-1"
uv run --locked --extra dev python -m training.audio_pilot.cli evaluate \
  --dataset-dir "$TASK_DATA" --validate-only --output-dir "$TASK_OUTPUT/validate-2"
cmp "$TASK_OUTPUT/validate-1/validation.json" "$TASK_OUTPUT/validate-2/validation.json"
```

Usar directorios nuevos: no sobrescribe evidencia. `--run-asr` es opt-in; por defecto
solo valida. LFS debe hidratarse **por el custodio de la rama de datos**, no mediante
este runner; no descarga/copia WAV, no altera ramas ni elimina archivos.
Resultados privados fuera de cualquier Git, directorios0700, archivos0600/O_EXCL;
symlinks de salida rechazados. stdout solo éxito/error fijo, sin texto/rutas privadas.

## ASR local explícito

Preparar dependencias y modelo antes de ejecutar sin red. No hay fallback automático
Base→Small ni descarga de pesos. Indicar **ruta local explícita** y variante; Small
solo puede ser una comparación explícitamente etiquetada, nunca sustituto silencioso.
`--expected-model-sha256` fija el binario conocido; se verifica antes de importar ASR.
Se registran hashes de archivos operativos del modelo y versiones Faster-Whisper,
CTranslate2 y PyAV. La variante es declaración del operador; si config contiene
`d_model` se verifica dimensión, pero algunos CT2 omiten ese dato: entonces no se
certifica arquitectura por nombre de carpeta. La procedencia Base real debe
respaldarse con el SHA publicado por la fuente, sin descargar otro modelo.
En el piloto local se cotejó model.bin con el LFS OID del repositorio primario
`Systran/faster-whisper-base`, revisión registrada en la evidencia privada.

```bash
export TASK_MODEL="/ruta/local/al/modelo-base"
export TASK_BASE_SHA="SHA256_VERIFICADO_DEL_MODELO_BASE"
HF_HUB_OFFLINE=1 HF_DATASETS_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
uv run --locked --extra dev --extra asr python -m training.audio_pilot.cli evaluate \
  --dataset-dir "$TASK_DATA" --run-asr --model-dir "$TASK_MODEL" \
  --model-variant base --expected-model-sha256 "$TASK_BASE_SHA" \
  --language es --beam-size 5 --best-of 5 --cpu-threads 2 \
  --device cpu --compute-type int8 --output-dir "$TASK_OUTPUT/base-1"
```

Si falta modelo/extra/hardware: error fijo y ASR_NO_EJECUTADO, sin tiempos inventados.
No descarga modelos al validar/importar. Base: temperatura0, beam5/best_of5,
VADfalse, condition_on_previous_text=true, word_timestamps=false, initial_prompt=null,
un worker CT2; idioma/dispositivo/compute/hilos/beam/best_of y VAD parametrizados.
`--no-condition-on-previous-text` desactiva contexto, todo fijado en parámetros/digest.
En CPU/int8 se mide ejecución local, sin tocar servicios ni configuración del lab.

## Esquema y medición

- `validation.json` (`audio-pilot-input-1`): CSV SHA y digest del inventario
  normalizado, veinte IDs/hashes/tamaños, canales/rate/frames/duración; sin rutas
  absolutas, transcripciones ni tiempos. Repetición determinista.
- `annotation-template.json` (`audio-pilot-annotation-1`): IDs y audio SHA,
  `reference=null` para completar fielmente por humanos; no precarga ASR/guiones.
- `provenance.json` en validate-only: commit/dirty, digest de herramientas,
  lock SHA, Python, CPU/arquitectura/RAM/SO; no hostname, usuario ni rutas privadas.
- `run.json` (`audio-pilot-run-1`), solo privado: entrada, parámetros/modelo,
  versiones, veinte records ligados a audio SHA, estado/error fijo, segmentos y
  **texto bruto sin corrección**, timers por ID y procedencia. Cada error queda
  explícito; fallos no se convierten en transcripciones vacías exitosas.
- `summary.json` (`audio-pilot-summary-1` en ASR): contadores, hashes/config/modelo,
  latencias n/p50/p95/max por primera inferencia/warm/todas, carga y setup separados,
  hardware; **no transcripciones ni segmentos**. Validate-only emite resumen mínimo
  ASR_NO_EJECUTADO / HUMAN_GOLD=NO / WER=N/A / HOLDOUT_EXTERNO=0 / PROMOCION=NO.

`perf_counter`: setup incluye validación/hash del modelo/imports/carga;
model_load_seconds mide solo constructor WhisperModel. Inferencia empieza después
verificar bytes y termina tras consumir todos los segmentos (decodificación incluida).
Primera llamada de nueva instancia vs warm posteriores: no controla caché OS,
no es latencia de UI/cola/Backend/voz E2E. Estadísticas reutilizan PR23: mediana y
nearest-rank p95. Errores excluidos de la distribución y contados separadamente;
si no hay inferencias exitosas, n0 y percentiles null. No se mide NLP/proyección/UX.

Quality digest cubre entrada/parámetros/modelo/records, excluye timers y hardware.
Es una huella de artefactos, no prueba de independencia ni precisión. Los segmentos
incluyen sus tiempos acústicos, diferentes de las latencias de procesamiento.
La integridad SHA no autentica un acta humana ni un experimento independiente.

## Comparación futura

Repetir con destinos nuevos, misma entrada sellada y parámetros explícitos. Los
modelos/parámetros pueden variar, pero el manifiesto/bytes/source_type deben coincidir.

```bash
uv run --locked --extra dev python -m training.audio_pilot.cli compare \
  --run-dirs "$TASK_OUTPUT/base-1" "$TASK_OUTPUT/base-2" \
  --output-dir "$TASK_OUTPUT/comparison"
```

Rechaza duplicado canónico/alias, input diferente o run alterado sin digest válido.
Reporta cada configuración y medidas separadas, nunca una mejora por una anécdota.
Dos rutas/copias o hashes iguales no acreditan procesos independientes: UNVERIFIED.
Mientras falte gold fiel verificado: WER=N/A y mejora de calidad NOT_EVALUABLE.

## Gold fiel y exportación compatible con #23

Mecanismo optativo, no formulario obligatorio del flujo comercial. Custodio conserva
consentimiento/finalidad/retención y pseudónimos fuera de Git. Dos personas escuchan
el **mismo audio** de forma independiente, sin ver ASR ni guion esperado; transcriben
literalmente números, vacilaciones y lo realmente dicho. Arbitrar discrepancias,
registrar actas/fecha/identidades autorizadas, ligar decisiones al hash final. Una
referencia comercial ideal se mantiene separada de `faithful`. No generar etiquetas.

Para exportar, archivo privado de declaraciones **completado por responsable real**:
`{batch_id, frozen_date, sessions:[{id,speaker_id,consent}]}` con los20IDs; consent
sigue el modelo PR23 (human_declared,act_id,use_policy_id,retention_policy_id).
No se suministra un consentimiento ficticio por defecto. Sin declaración no exporta
ASR_REAL al banco. Plantilla opcional de anotaciones: completar `reference` con
Reference PR23 (origin independent_human, faithful {text,sha256}, revisión/actas);
el exportador verifica dataset/ID/audio SHA. No convierte esas declaraciones en gold.

```bash
uv run --locked --extra dev python -m training.audio_pilot.cli export \
  --run-dirs "$TASK_OUTPUT/base-1" --declarations /ruta/privada/declaraciones.json \
  --annotations /ruta/privada/anotaciones.json --output-dir "$TASK_OUTPUT/export"
uv run --locked --extra dev python -m training.evaluar_campo_prf04 prepare-review \
  "$TASK_OUTPUT/export/batch.json" --output /ruta/privada/review-kit.json
# Tras doble revisión humana real, usar las decisiones/registro externos:
uv run --locked --extra dev python -m training.evaluar_campo_prf04 score \
  "$TASK_OUTPUT/export/batch.json" --decisions /ruta/privada/decisiones.json \
  --authorized-reviewers /ruta/privada/revisores.json --output /ruta/privada/reporte.json
```

La exportación `field-benchmark-1` usa PREVIOUSLY_OPEN, sin motores NLP, sin campos
comerciales inventados, sin clocks de Backend fabricados. Se exporta solo una corrida
completa; no se mezclan fallos con gold. WER y doble revisión se calculan exclusivamente
por el scorer existente y sus gates de referencia/consentimiento; este arnés no
reinventa normalización, adjudicación o WER. Las plantillas y banderas no autentican
por sí solas identidades ni una revisión de verdad. Sin humanos: HUMAN_GOLD=NO.

## Pruebas y CI

```bash
uv run --locked --extra dev python -m training.audio_pilot.gate --evidence /ruta/privada/gate-audio
uv run --locked --extra dev python -m training.benchmark_campo.gate --evidence /ruta/privada/gate-benchmark
uv run --locked --extra dev python -m training.corpus_v2_rc2.ci_gate --evidence /ruta/privada/gate-rc2
uv audit --locked
```

WAV pequeños **sintéticos** generados en memoria/temporales; ningún audio real,
transcripción, peso o salida se versiona ni se publica en artefactos CI. Workflows
sin descarga LFS/ASR pesado/training: dev-only, guards CI/ASR/training activos,
allowlist de archivos exactos y padre#23 para primer push. Producción/mixto preserva
CI histórica; secretos/dependency-audit no se deshabilitan. Artefacto nuevo solo
result.json con resultados técnicos de pruebas, nunca contenido de audio/ASR.
La opción explícita --synthetic-test-data etiqueta pruebas; no demuestra naturaleza
real/sintética del contenido por sí sola y no habilita ASR real en CI.

**Bloqueos científicos:** transcripción fiel y doble revisión/consentimiento verificable
pendientes; WER y precisión real N/A; correspondencia22↔20 UNVERIFIED; cero holdout.
Este trabajo prepara medición verificable y no corrige el NLP ni cierra etapa8.
