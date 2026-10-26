# Banco offline de campo PRF-04

Estado técnico sujeto a gates: `BENCHMARK_HERRAMIENTAS_VERIFICADAS`.
**Infraestructura lista ≠ evaluación de campo realizada.** Cero grabaciones reales
aportadas a esta entrega; `HUMAN_GOLD=NO`, `TEST_VOZ_REAL=NO`,
`HOLDOUT_EXTERNO_SIN_MUESTRAS`. Ningún resultado sintético demuestra precisión real.

Base inmutable: RC2 #22, `b27edfa522f08c4621d31113b14295ece08e2109`, sobre RC1 #20.
El benchmark amplía `training/evaluar_campo_prf04.py`: conserva `palabras`,
`distancia`, `evaluar` y la CLI JSONL histórica. Nuevas operaciones se despachan
al mismo evaluador. No ejecuta motores, no importa Backend, no requiere PostgreSQL,
ni cambia runtime, candidatos, dependencias o ledger RC2. El entorno paralelo v13
puede entregar salidas offline mediante este contrato, sin integrar sus PRs.

## Contrato y almacenamiento privado

Contrato ejecutable: `training/benchmark_campo/models.py`; JSON Schema reproducible:
`tests/fixtures/benchmark_campo/schema.json`. `extra=forbid`, tipos estrictos,
números finitos y hashes de texto UTF-8 exactos. Entrada: un objeto Batch JSON con
`schema_version=field-benchmark-1`, batch pseudónimo, fecha ISO y sesiones.
El esquema publicado incluye todas las propiedades, tipos, enums y requeridos;
las restricciones entre campos se comprueban además con Pydantic. La fixture
`synthetic.json` es **SINTETICO_SOLO_PRUEBA_NO_WER_REAL**, no una sesión humana.

Cada sesión contiene identidad pseudónima de sesión/caso/fuente/plantilla/speaker;
los pseudónimos se asignan aleatoriamente por el operador, nunca desde nombres,
teléfonos, documentos ni hashes de PII. El vínculo con personas vive en un registro
externo separado, bajo responsabilidad HOMEX. Ningún ID prueba anonimización.
Particiones permitidas: QUARANTINE, TRAIN, DEV, EXTERNAL_CANDIDATE, PREVIOUSLY_OPEN.
Ninguna opción asigna automáticamente un test ciego aprobado.

- `asr`: literal y SHA-256, sin correcciones silenciosas.
- `reference.faithful`: transcripción fiel e independiente del mismo audio;
  conservar vacilaciones, números realmente pronunciados, rectificaciones e idioma.
- `reference.ner`: texto objetivo (`asr` o `faithful`), hash y spans Unicode Python
  semiabiertos `[start,end)`, sin solapamientos. No reutilizar offsets entre textos.
- `reference.commercial`: ficha comercial ideal distinta de la transcripción;
  scopes ITEM/CONDITIONS/componentes/accesorios, facts con campo/valor/unidad/evidencia.
  `sold_quantity`, `capacity`, `internal_quantity`, `accessory_quantity` son distintos.
  ITEM es único; un caso multiproducto requiere referencia de abstención/negativos,
  no fusionar productos. Moneda solo en CONDITIONS. No convertir valores.
- `engines`: identidad/commit exacto/wheel SHA/version/rules_version, texto de entrada
  y salidas NER/comerciales. Un adaptador externo debe mapear sus componentes a
  los IDs de scope del caso independientemente revisados. El evaluador no los alinea
  por posición ni cambia los resultados del motor. Versiones distintas se estratifican
  mediante una huella de metadatos, sin divulgar sus IDs libres en agregados.
- Consentimiento: `human_declared`, acta externa, IDs de políticas de uso/retención.
  Audio opcional como referencia opaca + SHA, sin ruta en el lote. El custodio verifica
  bytes contra SHA al recibir el audio, documentándolo en acta; este evaluador
  **no abre ni verifica archivos de audio** y no puede demostrar que existieron.
- Estado de referencia, revisores/actas externos, arbitraje; tiempos y diagnóstico.

Para ASR_REAL se exige declaración de consentimiento y políticas, pero **declaración
no equivale a verificación**. Puede ingresarse solo ASR sin reference: WER/NER/campos
quedan NOT_EVALUABLE. `reference.origin=independent_human` es declaración de origen,
no evidencia suficiente. La opción sintética solo admite `synthetic_fixture`.
No generar referencia desde predicciones ni cambiar origen para pasar validaciones.

Todos los lotes reales, actos, decisiones y detalles permanecen fuera de cualquier
repositorio Git. Directorio 0700, archivos 0600. La CLI rechaza reales en CI, reales
con permisos amplios, entradas JSON con claves duplicadas/no finitos y outputs en
Git. Crea outputs con O_EXCL/0600: no sobrescribe ni sigue symlinks de salida.
Los errores no imprimen valores de entrada ni excepciones Pydantic. No publicar
stdout de otros programas que lean fuentes privadas.

## Flujo de revisión y entrega privada

1. HOMEX debe aprobar responsable, finalidad, voluntariedad, acceso, plazo de
   retención, eliminación y posible entrenamiento **por separado**. Completar los
   IDs de acta y políticas; no se entregan formularios firmados ni consentimientos
   ficticios. Sin aprobación: BLOCKED_EXTERNAL.
2. Vendedor aporta dictado espontáneo autorizado, caso independiente y condiciones
   no identificables. No reutilizar textos de train/dev ni ensayar con la fixture.
   Guardar audio solo si su acta lo permite; la captura efímera debe constar en acta.
3. Revisor A transcribe fielmente escuchando el audio; revisión B independiente.
   Anotar NER en el texto de comparación elegido. Registrar omisiones/negativos.
   Otro proceso comercial determina ficha ideal y scopes; no mostrar predicciones
   durante la anotación inicial. Priorizar precios/cantidades/unidades/componentes.
4. Registrar desacuerdos, propuestas de corrección del vendedor y arbitraje externo.
   `productivity.seller_corrections` conserva facts privados; no modifica gold.
   Antes de solicitar decisiones, fijar bundle final y declaraciones de estado
   `review_status=human_verified`, `arbitration=RESOLVED` **solo cuando corresponda**.
   Estos campos solos no habilitan scoring real.
5. `prepare-review` genera tres objetos por sesión: reference, consent, independence.
   Reutiliza `training.corpus_v2_rc2.review.field_digest/import_decisions` con un kit
   nuevo; liga texto/audio/caso/lote y contenido antes/después. No importa ni cambia
   el kit/ledger de los 11.591 campos RC2.
6. Dos revisores reales autorizados distintos completan ACCEPT/REJECT/DISPUTE,
   reviewer, attestation_id, reviewed_at ISO con zona y comment. Registro externo:
   lista de `{reviewer, attestation_id, authorized: true}` suministrada por HOMEX.
   Archivo de decisiones: lista JSON con los campos del kit (incluidos hashes).
   Ni IDs ni este registro son firma o autenticación criptográfica: HOMEX verifica
   identidades, independencia y acceso. Una decisión sola o cualquier discrepancia
   impide elegibilidad; cambios de contenido invalidan decisiones previas.
7. `score --decisions ... --authorized-reviewers ...` verifica hashes/votos.
   Para métricas reales de referencia exige consentimiento y bundle aceptados por
   dos revisores, estado final y arbitraje resuelto. Sin ellos no calcula referencia.
   Para latencia/productividad exige consentimiento verificado mediante decisiones;
   los tiempos completados y las causas siguen siendo evidencia declarada externa.
8. Separar decisiones de independencia/acceso del cálculo de precisión: incluso con
   votos la herramienta **no certifica test ciego** ni transforma el lote en gold.
   El custodio debe adjudicar todas las alertas, revisar paráfrasis semánticas y
   acceso previo, congelar contenido autorizado, limitar acceso y registrar primera
   apertura. Mismo dictado/fuente/plantilla/speaker no puede cruzar train/test externo.
9. Entregar privadamente `batch.json`, kit, decisiones, registro autorizado, índice
   de audio si existe, actas externas, informe agregado y manifiesto SHA-256.
   No adjuntar originales ni detalle privado a PR/CI. Cumplir eliminación aprobada.

## Reproducción

Desde un checkout de esta rama con historia completa (las pruebas RC2 comprueban
commits históricos), Python 3.11.15 y `uv` fijado en CI:

```bash
uv sync --locked --extra dev --python 3.11.15
install -d -m 700 "$HOME/Descargas/homex-benchmark-evidencia"
uv run --locked --extra dev python -m training.evaluar_campo_prf04 validate \
  tests/fixtures/benchmark_campo/synthetic.json \
  --output "$HOME/Descargas/homex-benchmark-evidencia/validacion.json"
uv run --locked --extra dev python -m training.evaluar_campo_prf04 score \
  tests/fixtures/benchmark_campo/synthetic.json \
  --output "$HOME/Descargas/homex-benchmark-evidencia/sintetico-a.json"
uv run --locked --extra dev python -m training.evaluar_campo_prf04 score \
  tests/fixtures/benchmark_campo/synthetic.json \
  --output "$HOME/Descargas/homex-benchmark-evidencia/sintetico-b.json"
sha256sum "$HOME/Descargas/homex-benchmark-evidencia/"sintetico-*.json
cmp "$HOME/Descargas/homex-benchmark-evidencia/sintetico-a.json" \
  "$HOME/Descargas/homex-benchmark-evidencia/sintetico-b.json"
uv run --locked --extra dev python -m training.benchmark_campo.gate \
  --evidence "$HOME/Descargas/homex-benchmark-evidencia/gate"
uv run --locked --extra dev python -m training.corpus_v2_rc2.validate \
  data/candidates/corpus_v2_rc2
```

Usar nombres nuevos en cada ejecución: la CLI impide sobrescritura. Para un lote
real **futuro**, después de las aprobaciones externas y con permisos restringidos:

```bash
uv run --locked --extra dev python -m training.evaluar_campo_prf04 prepare-review \
  "$HOME/Descargas/homex-campo-privado/batch.json" \
  --output "$HOME/Descargas/homex-campo-privado/kit.json"
# HOMEX realiza y verifica las revisiones externas antes del siguiente comando.
uv run --locked --extra dev python -m training.evaluar_campo_prf04 score \
  "$HOME/Descargas/homex-campo-privado/batch.json" \
  --decisions "$HOME/Descargas/homex-campo-privado/decisiones.json" \
  --authorized-reviewers "$HOME/Descargas/homex-campo-privado/revisores.json" \
  --previously-open "$HOME/Descargas/homex-campo-privado/test-abierto.json" \
  --output "$HOME/Descargas/homex-campo-privado/agregado.json"
```

`--previously-open` es lista JSON de text, case_id/source_id/template_id/speaker_id,
partition y audio_sha256 cuando exista; debe incluir **todo** test previamente
abierto, no una muestra conveniente. La herramienta no conoce registros externos
que no se suministren. `aggregate lote1.json lote2.json --output ...` suma conteos,
no promedia porcentajes; conserva cada lote y su vínculo de revisión; IDs duplicados
entre lotes se rechazan. No agrupar un caso repetido como observaciones independientes.
`schema --output ...` exporta esquemas. `--private-detail` en score/aggregate incluye
literal completo, metadatos y WER por sesión: **NO PUBLICAR**. Sin ese flag el agregado
omite textos, IDs libres, precios y rutas. Verificación de consentimiento no concede
permiso para compartir un agregado: HOMEX debe aprobar su divulgación.

## Definiciones y límites de las métricas

WER: misma tokenización histórica `palabras` (regex Unicode `\w+`, casefold), sin
reescribir palabras/números. Puntuación separa tokens; `1,20` y `1.20` se tokenizan
igual, `dos` y `2` difieren. Se publica esta limitación, no se normaliza el importe
comercial con ese tokenizador. Levenshtein determinista: desempate diagonal,
borrado, inserción. Micro=(ΣS+ΣD+ΣI)/ΣN; referencia vacía retiene inserciones y WER
null/NOT_EVALUABLE. Por sesión disponible solo en detalle privado.

NER: coincidencia exacta etiqueta/inicio/fin sobre **mismo texto/hash/coordenada**;
referencia parcial o coordenadas distintas: NOT_EVALUABLE. Ausencia de predicción
NER no equivale a lista vacía; para abstención explícita enviar `spans: []`.
TP/FP/FN por etiqueta, micro y macro de P/R/F1 con denominadores; cada razón sin
soporte es null y se excluye de su macro, indicando número de etiquetas.
Los negativos completos cuentan predicciones espurias como FP.

Comercial: strings exactos; números Decimal sin redondeos, coma o punto decimal
único y sin separadores de miles (normalizar explícitamente al importar con acta,
nunca adivinar `3.650,00`). Sin convertir cm/m ni BOB/USD. Dimensión completa requiere
campo de eje + unidad; medida sin unidad nunca cuenta como correcta, aun si ambos
lados la omiten. Relaciones por `(scope,field)`; TABLERO/espesor18 no intercambia con
MESON/espesor27; accesorios conservan scope y cantidad. Valores erróneos cuentan
omisión + falsa afirmación; faltantes no son acierto. Exactitud=correctos/positivos
esperados, omisión=omisiones/positivos esperados, falsas afirmaciones=incorrectos/
positivos predichos. Negativos completos cubren la unión de claves esperadas y
predichas; negativos explícitos parciales usan reviewed_keys. Abstención segura se
cuenta separada y no infla exactitud positiva. En parcial no se evalúan otras claves.
Críticos: producto/cantidad vendida/unidad/importes/descuento/moneda/ejes/espesor/
material/cantidad accesorio; denominador oportunidades revisadas en esos campos,
una oportunidad por scope/campo, no por audio. Referencia nula nunca habilita métricas.

Latencias: intervalos con reloj común monotónico o sincronizado, s/ms explícitos,
landmarks compartidos consistentes. Queue=queued→worker_started;
ASR=asr_started→asr_done; NLP=nlp_started→nlp_done;
projection=projection_started→projection_done;
frontend=frontend_received→form_usable;
end_to_form=recording_end→form_usable. No restar relojes de hosts sin sincronización.
Todo en segundos, n/p50 mediana (promedio centrales si par)/p95 rango más próximo
ceil(.95*n)/max. Estratos cold/warm/unknown, CPU/GPU y quiet/noise. No se infiere una
latencia ausente; GPU/CPU no identifica una persona ni describe rendimiento comparable
sin condiciones externas adicionales.

Productividad: caso pareado, orden manual_first/assisted_first, tiempos hasta tarea
comercial validada, correcciones y exclusión explícita. Ahorro=manual−asistido por
par (puede ser negativo); no usar tiempo de ASR como duración de tarea. Sesiones
incompletas/no validadas se excluyen con conteos y motivos. No hay ahorro real con
cero pares reales. Causas ASR/NLP/projection/UI/human_review requieren IDs externos
de evidencia y se reportan **declaradas, no verificadas**; discrepancia aislada queda
unknown. No atribuir automáticamente causalidad.

Independencia: comparación con V1 y textos RC1/RC2 publicados, más índice privado
previamente abierto; exactos normalizados, audio SHA, caso/fuente/plantilla/speaker,
y Jaccard léxico ≥0,8 para paráfrasis candidatas. No detecta todas las paráfrasis
semánticas; requiere revisión humana y acceso externo antes de test ciego. Reporte
sin matches no prueba independencia. El sello liga JSON canónico autorizado (solo
si consentimiento verificado o fixture sintética), candidato, reglas Python+evaluador
histórico+importador RC2+uv.lock, particiones y fecha; no es una firma humana.
No se habilita ninguna promoción, entrenamiento ni reasignación de particiones.

## CI y controles

Nuevo workflow `Benchmark campo — offline sin entrenamiento`, job
`benchmark-offline`: uv locked, suite completa bajo guard RC2 que bloquea entrenamiento
spaCy/carga de pesos/subprocesos de entrenamiento, Ruff check/format, diff, igualdad
de dos scoring y reporte fixture, esquema y protección del diff contra RC2.
Solo publica result.json agregado, nunca lotes ni logs privados. El workflow RC2
sigue validando/reconstruyendo datos sin entrenamiento. `ci.yml` conserva secretos
y auditoría de dependencias; no se alteran sus jobs.

El clasificador permite **archivos concretos**, no todo training/docs/tests.
Para primer push before=000 solo admite un commit directo desde RC1 original o
RC2 aprobado. Publicar este trabajo como **un primer commit directo de b27edfa**;
otro padre es desconocido y mantiene gates históricos. Cambios mixtos/runtime
mantienen package/prf04-experiment como antes. Push posteriores usan before real;
PR usa base.sha. No hay skip-ci, exclusión global ni relajación de secretos.

| Entrega | Control verificable | Estado técnico tras gate |
|---|---|---|
| E1 | Pydantic + Schema + fixture pseudónima; referencias separadas | PASS |
| E2 | CLI validate/prepare-review/score/aggregate; mutaciones, permisos | PASS |
| E3 | WER S/D/I, NER, Decimal/relaciones, latencias y pares | PASS |
| E4 | Screening V1/RC1/RC2/test abierto + sello; sin certificación ciega | PASS |
| E5 | Kit ligado a hashes, doble revisión externa, guía privada | PASS |
| E6 | Pruebas nuevas + antiguas intactas, ejemplo marcado | PASS |
| E7 | Gate local, scope preciso, CI remota por verificar en PR | Ver evidencia del PR |

| Gate de aceptación | Evidencia | Estado al aprobar verificaciones |
|---|---|---|
| 1 Retrocompatibilidad | tests originales sin editar; API/JSONL conservados | PASS |
| 2 Independencia | orígenes, referencias, hashes, screening, ninguna voz ficticia | PASS técnico / BLOCKED_EXTERNAL gold |
| 3 Ausencias honestas | cero real→NO_DISPONIBLE; null/NOT_EVALUABLE | PASS |
| 4 Privacidad | exact allowlist, synthetic-only fixtures, logs sin inputs, 0700/0600 | PASS técnico / autorización externa pendiente |
| 5 Seguridad comercial | negativos/mutaciones Decimal/ejes/scopes/cantidad/moneda | PASS |
| 6 Métricas auditables | conteos, métodos, estratos, N/A y límites | PASS |
| 7 Seguridad Git | diff respecto b27edfa, candidatos/runtime/repos originales intactos | PASS |
| 8 CI real | enlaces/SHA/jobs en informe privado y PR, esperar todos los jobs | Ver evidencia del PR |
| 9 Entregables | código, esquema, ejemplo, guía, CLI, matrices, manifiesto privado | PASS tras paquete |
| 10 Campo ≠ herramientas | declaración explícita, ninguna aprobación real inventada | PASS técnico / BLOCKED_EXTERNAL campo |

BLOCKED_EXTERNAL: aprobación HOMEX de consentimiento/finalidad/retención/acceso;
voces reales y verificación audio/SHA; transcripciones fieles; anotación comercial
independiente; dos revisores reales; arbitraje; screening semántico y test ciego;
medición de tarea real; umbrales de aceptación. Estos trabajos no se sustituyen con
pruebas unitarias. Los estados técnicos PASS dependen de las verificaciones locales
y remotas del SHA final, enlazadas en PR e informe de entrega.
