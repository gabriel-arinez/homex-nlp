# Escucha humana y WER del piloto conocido

Base inmediata: PR #26, `7ba61ea3447174dc9d373494209cb5edcc1261cb`, apilado sobre
#23 `9b2d57d145c09d6ac354ee3d8ecef4f294db94ee`. Extensión local de etapas 2/5;
prepara etapa 8 sin cerrarla. Ningún audio se descarga ni se añade a Git.
Los 20 WAV conocidos NO son las 22 capturas históricas; su asociación no está
probada. No se comparan por posición ni se afirma mejora sin baseline comparable.

## Protocolo human-listening-1

Dos personas autorizadas, aliases distintos, escuchan cada WAV en sesiones
identificadas. No consultar ASR, guion ni otra lectura durante la captura. La
herramienta no precarga texto. `inspect` muestra una lectura propia por alias y
sesión; sólo muestra ambas cuando las dos fueron enviadas. Los aliases no son
credenciales: el responsable debe asegurar separación efectiva de personas y
acceso. Dos sesiones de una persona quedan registradas, pero NO constituyen
independencia interobservador y NO permiten aprobación GOLD. No inventar aliases.

Estados locales: DRAFT → SUBMITTED; dos textos distintos → DISAGREEMENT. Incluso
textos iguales exigen adjudicación explícita con acta → ADJUDICATED. Cada lector
aprueba el texto adjudicado explícitamente → APPROVED al reunir dos aliases.
Una voz dudosa bloquea adjudicación hasta reescucha y acta que contenga RESUELTO;
si sigue dudosa, conservar pendiente. APPROVED es aprobación **local**, no autentica
identidad, consentimiento ni permiso de publicación. WER real exige además las
aceptaciones externas del benchmark #23 para referencia y consentimiento.

Transcribir lo realmente pronunciado, conservando repeticiones, rectificaciones,
muletillas y negaciones: «dos, eh, dos mesas, no tres». No sustituir «precio» por
«dimensión» aunque el guion lo espere. Mantener términos técnicos según lo oído;
no completar nombres omitidos. Escribir números como palabras pronunciadas
(«veinte», «dos coma cinco»), unidades como palabras («centímetros»), sin convertir
magnitudes. Ortografía española convencional, sin reconstruir errores fonéticos
ni corregir semántica. Puntuación ligera y consistente; no puntuar cada respiración.
Registrar pausas/ruido e intervalos en la nota, fuera del literal. Palabras dudosas:
marcar la duda y su intervalo en la nota, volver a escuchar. Cuando sea imposible
resolver una palabra, usar `[ininteligible]` y justificar su intervalo en acta;
confirmar explícitamente esa convención al adjudicar. El marcador se cuenta como
palabra con el normalizador existente, por lo que se advierte su efecto en WER.
Una referencia completamente vacía no puede enviarse: queda pendiente. El scorer
original mantiene NOT_EVALUABLE/N=0 e inserciones para referencias vacías externas.

Normalizador `pr23-casefold-unicode-word-1`: exactamente
`training.evaluar_campo_prf04.palabras`, regex Unicode `\w+` tras `casefold`.
No convierte números, unidades, acentos ni sinónimos. Literal bruto, notas y
normalización se mantienen separados; `binding.json` guarda tokens normalizados.
El scorer existente conserva S/D/I/N por audio y agregado; el reporte añade
longitud de hipótesis, advertencias, digest de lote. `binding.json` vincula además
corrida completa, modelo/configuración ASR, proyecto, ledger y declaraciones.

## Preparación segura en Ubuntu

Desde este checkout independiente (no cambiar las ramas del equipo de integración):

```bash
uv sync --locked --extra dev --python 3.11.15
export TASK_DATA="$HOME/Descargas/homex-nlp-piloto-audios-v13/datasets/piloto_voz_v13"
export TASK_PRIVATE="$HOME/homex-human-review"
install -d -m 700 "$TASK_PRIVATE"
uv run --locked --extra dev python -m training.audio_pilot.human_cli init \
  --dataset "$TASK_DATA" --project "$TASK_PRIVATE/project"
uv run --locked --extra dev python -m training.audio_pilot.human_cli status \
  --dataset "$TASK_DATA" --project "$TASK_PRIVATE/project"
```

El custodio proporciona el directorio ya hidratado y autorizado. No hacer `git lfs
pull` como parte de este instrumento. `init`, cada operación y reproducción validan
los 20 IDs, manifiesto y bytes; cualquier WAV cambiado bloquea. Se rechazan extras,
hashes cruzados, symlinks (incluidos ancestros), entradas huérfanas y JSON inválido.
No se modifica PostgreSQL. No usar directorios compartidos, dentro de Git, o symlinks.
No grabar la terminal ni habilitar trazas de shell durante revisión de textos.

Reproductor: `aplay` de `alsa-utils`, normalmente disponible en Ubuntu. Si falta,
el operador instala `sudo apt install alsa-utils`. `listen` pasa bytes WAV validados
por stdin a `aplay`, sin servicio/red ni nombre de archivo en el proceso. Segmentación
por segundos con `--start/--end`. Si no hay dispositivo, usar un reproductor local
como Audacity sobre el WAV del ID indicado en `audios/`; cotejar ID/hash con el
manifiesto validado antes de escuchar y volver a ejecutar `status` después.
No subir el audio a una web. Un error de reproducción no acredita escucha.

## Captura, reanudación y doble lectura

Cada comando de captura solicita texto oculto para evitar historial shell/stdout.
Usar una terminal interactiva privada. El texto es una línea Unicode; se pueden
pegar frases largas. No se admiten entradas por pipe ni ejecución de captura en CI.

```bash
uv run --locked --extra dev python -m training.audio_pilot.human_cli listen \
  --dataset "$TASK_DATA" --project "$TASK_PRIVATE/project" --id 01
uv run --locked --extra dev python -m training.audio_pilot.human_cli listen \
  --dataset "$TASK_DATA" --project "$TASK_PRIVATE/project" --id 01 --start 0 --end 1
uv run --locked --extra dev python -m training.audio_pilot.human_cli draft \
  --dataset "$TASK_DATA" --project "$TASK_PRIVATE/project" --id 01 --reviewer R1 --session S1
uv run --locked --extra dev python -m training.audio_pilot.human_cli inspect \
  --dataset "$TASK_DATA" --project "$TASK_PRIVATE/project" --id 01 --reviewer R1 --session S1
uv run --locked --extra dev python -m training.audio_pilot.human_cli submit \
  --dataset "$TASK_DATA" --project "$TASK_PRIVATE/project" --id 01 --reviewer R1 --session S1
```

`draft` puede repetirse para corregir el borrador propio; guarda cada versión en
un archivo nuevo. Para `submit`, introducir el literal final y escribir `CONFIRMO`;
una lectura enviada es inmutable. Reanudar con `status` e `inspect` del borrador
propio. Repetir escucha/captura como R2/S2 sin ver R1. Repetir IDs 01…20. Los aliases
son ejemplos: sustituir por los aliases reales proporcionados; no crearlos para
simular otra persona. La opción de duda requiere responder `NO` para ausencia de
duda. Texto copiado de ASR/guion no cumple el protocolo aunque los hashes coincidan;
el software comprueba procedencia declarada, no puede detectar una mentira humana.

```bash
uv run --locked --extra dev python -m training.audio_pilot.human_cli inspect \
  --dataset "$TASK_DATA" --project "$TASK_PRIVATE/project" --id 01
uv run --locked --extra dev python -m training.audio_pilot.human_cli adjudicate \
  --dataset "$TASK_DATA" --project "$TASK_PRIVATE/project" --id 01 --reviewer R1 --session S1
uv run --locked --extra dev python -m training.audio_pilot.human_cli approve \
  --dataset "$TASK_DATA" --project "$TASK_PRIVATE/project" --id 01 --reviewer R1 --session S1
uv run --locked --extra dev python -m training.audio_pilot.human_cli approve \
  --dataset "$TASK_DATA" --project "$TASK_PRIVATE/project" --id 01 --reviewer R2 --session S2
```

No se aprueba por similitud automática. El acta explica discrepancias, palabras
dudosas, intervalos reescuchados y decisión. Antes de la primera aprobación se
puede repetir adjudicación con una nueva acta. Si se descubre error después de
SUBMITTED/APROBACIÓN, conservar proyecto anterior intacto y crear uno nuevo con
`init`; volver a capturar/revisar. No borrar ni editar eventos para «desbloquear».
Los archivos secuenciales O_EXCL evitan sobrescrituras/concurrencia silenciosa.
La cadena de hashes detecta cambios entre eventos; NO es firma digital ni impide
que el propietario reconstruya/trunque todo el historial. Conservar respaldo
privado y su digest bajo custodia independiente antes de usar resultados.

## Declaraciones auténticas y exportación

Se necesita una corrida completa #26 del MISMO manifiesto. Puede reutilizarse una
existente, sin ejecutar ASR de nuevo. Para una nueva corrida, seguir README.md:
`evaluate --run-asr --model-dir ...`; `validate-only` y `compare` siguen intactos.
No existe autorización implícita para publicar métricas/textos por conservar WAV.
El asistente siguiente solicita lote, fecha, actas, aliases, permisos separados y
consentimiento para cada ID, sin rellenar declaraciones ni autorizaciones.

```bash
uv run --locked --extra dev python -m training.audio_pilot.human_cli declare \
  --output "$TASK_PRIVATE/declarations.json"
export TASK_RUN="$HOME/Descargas/homex-audio-evaluacion/run-final"
uv run --locked --extra dev python -m training.audio_pilot.human_cli export \
  --dataset "$TASK_DATA" --project "$TASK_PRIVATE/project" --run "$TASK_RUN" \
  --declarations "$TASK_PRIVATE/declarations.json" --output "$TASK_PRIVATE/export-1"
```

Usar rutas reales existentes para TASK_RUN. Sin 20 aprobaciones dobles y
declaraciones válidas, CLI devuelve código 2 / `BLOCKED_EXTERNAL`. Una publicación
con permiso NO sigue bloqueada organizativamente: esta herramienta nunca publica.
Se conserva `partition=PREVIOUSLY_OPEN`, `independence=PENDING`. Exportación reutiliza
`audio_pilot.export.export_batch` y `Batch` field-benchmark-1, sin duplicar contratos.
Produce anotaciones, batch, kit y binding privados (no subirlos como artefactos CI).

El responsable externo proporciona `registry.json` 0600 en TASK_PRIVATE: lista
`reviewer`, `attestation_id`, `authorized=true`, conforme al registro de #23.
El instrumento **no crea** ese registro ni certifica identidades. Ejemplo de forma,
no de autorización: `[{"reviewer":"ALIAS_REAL","attestation_id":"ACTA_REAL","authorized":true}]`.
Los revisores examinan referencias y consentimiento de los 20 casos, reescuchan si
procede y deciden explícitamente en terminal privada. `vote` muestra texto privado
sólo en esta etapa posterior; nunca habilitarlo en CI ni grabar su salida.

```bash
uv run --locked --extra dev python -m training.audio_pilot.human_cli vote \
  --batch "$TASK_PRIVATE/export-1/batch.json" --votes "$TASK_PRIVATE/votes-1" \
  --registry "$TASK_PRIVATE/registry.json" --reviewer R1
uv run --locked --extra dev python -m training.audio_pilot.human_cli vote \
  --batch "$TASK_PRIVATE/export-1/batch.json" --votes "$TASK_PRIVATE/votes-1" \
  --registry "$TASK_PRIVATE/registry.json" --reviewer R2
uv run --locked --extra dev python -m training.audio_pilot.human_cli score \
  --batch "$TASK_PRIVATE/export-1/batch.json" --votes "$TASK_PRIVATE/votes-1" \
  --registry "$TASK_PRIVATE/registry.json" --output "$TASK_PRIVATE/score-1.json"
```

Las decisiones ligan digest de audio/ASR/caso/lote/campo, timestamp con zona y acta.
Una sola persona, rechazo, discrepancia, decisión duplicada o campo cambiado bloquean
el scoring final. Se usa `benchmark_campo.pipeline.score`, que llama al alineador
#23. `score-1.json` es íntegramente privado, incluidos S/D/I y detalle. No mezclar
universos. No interpretar tiempos ASR como latencia E2E ni como mejora de calidad.

## Ensayo manual sintético sin hardware ASR

```bash
uv run --locked --extra dev python -m training.audio_pilot.human_cli demo \
  --output "$TASK_PRIVATE/demo-1"
export TASK_DATA="$TASK_PRIVATE/demo-1/dataset"
export TASK_RUN="$TASK_PRIVATE/demo-1/run"
```

`demo` genera 20 tonos PCM diferentes de un segundo, manifiesto, proyecto vacío y
corrida ASR **simulada** marcada SYNTHETIC_TEST_ONLY (no descarga/modelo/voz nueva).
Usar `--project "$TASK_PRIVATE/demo-1/project"` en escucha/captura/status y añadir
`--synthetic-test-data` a draft/submit/adjudicate/approve, declare y export. Escuchar
01, guardar borrador «tono», reanudarlo, enviar R1/S1 y R2/S2, adjudicar y aprobar
ambos. Comprobar 19 pendientes y exportación bloqueada. Completar los 20 para
ensayar exportación/scoring con actas y registro **sólo de prueba**, separados de
cualquier evidencia real. Es un ensayo de interacción, no WER de habla ni GOLD.
Registrar por una persona: ID oído, reproducción completa/segmentada, reanudación,
discrepancia deliberada, bloqueo antes de completar, export y scoring final.
La automatización verifica el recorrido con personas simuladas; no acredita que
una persona real haya oído el tono. Esa comprobación requiere al operador.

## Gates y conservación

```bash
uv run --locked --extra dev python -m training.audio_pilot.gate --evidence /tmp/homex-human-audio-gate
uv run --locked --extra dev python -m training.benchmark_campo.gate --evidence /tmp/homex-human-benchmark-gate
uv run --locked --extra dev python -m training.corpus_v2_rc2.ci_gate --evidence /tmp/homex-human-corpus-gate
uv audit --locked
```

Los gates ejecutan regresión completa sintética, Ruff check/format, diff, controles
de alcance y reproducibilidad, sin LFS/ASR real/entrenamiento. CI mantiene secretos
y auditoría de dependencias; sólo sube result.json agregado del gate de audio.
No almacenar entradas reales en fixtures ni outputs privados en Git.

Antes de limpiar, cerrar aplicaciones, comprobar hashes, respaldar proyecto,
actas, registro, corrida, export y score en almacenamiento privado autorizado y
verificar la copia. No borrar originales WAV ni evidencias aprobadas. Los ensayos
sintéticos pueden archivarse bajo su etiqueta; la eliminación de material privado
sigue la política de retención humana, no un borrado automático de este programa.

Estado real mientras no se complete escucha/autorización humana auténtica:
**HUMAN_GOLD=NO; WER=N/A; HOLDOUT_EXTERNO=0; PROMOCION=NO**.

## Evidencia técnica de la entrega

Rama independiente `codex/human-gold-wer-20261026`. La revisión de esta entrega y
los enlaces de CI se registran en su PR draft contra la rama #26, sin merge.

| Verificación local | Resultado |
| --- | --- |
| Gate audio: tests completos, Ruff check/format, diff, alcance, manifiesto determinista | PASS |
| Gate benchmark #23: regresión y reporte/schema congelados deterministas | PASS |
| Gate corpus rc2: 11 comandos y dos reconstrucciones idénticas | PASS |
| `uv audit --locked`: 70 paquetes | Sin vulnerabilidades conocidas |
| Escucha humana del ensayo sintético | Pendiente de operador real |
| Anotaciones reales y autorizaciones externas | Pendientes; ningún GOLD creado |

Los tests nuevos simulan revisores y también ejercitan el contrato de transporte
real con WAV generados. Esa simulación está rotulada SYNTHETIC_TEST_ONLY en tests;
no constituye una corrida ni autorización del piloto real. El demo se verificó por
CLI con 20 IDs DRAFT, cero capturas y modelo simulado explícitamente identificado.
